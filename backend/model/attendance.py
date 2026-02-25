import cv2
import os
import sys
import time
import pickle
import numpy as np
from datetime import datetime

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")


def validate_tensorflow() -> None:
    if sys.version_info >= (3, 13):
        raise RuntimeError(
            "Python 3.13 is not supported by TensorFlow. "
            "Use Python 3.11 or 3.10 in your venv."
        )

    try:
        import tensorflow as tf  # noqa: F401
    except Exception as exc:
        raise RuntimeError(
            "TensorFlow is missing. On Raspberry Pi 5 (aarch64), install with:\n"
            "  pip install tensorflow==2.20.0 tf-keras\n"
            "On Raspberry Pi 3/4 (armv7l), use:\n"
            "  pip install tensorflow==2.20.0 tf-keras"
        ) from exc

    if not hasattr(tf, "__version__"):
        raise RuntimeError(
            "TensorFlow install appears broken (missing __version__). "
            "Try: pip install --force-reinstall tensorflow tf-keras"
        )

    # Accept TF 2.15+ (RPi 3/4) and TF 2.20+ (RPi 5 aarch64)
    major, minor = (int(x) for x in tf.__version__.split(".")[:2])
    if (major, minor) < (2, 15):
        raise RuntimeError(
            f"TensorFlow {tf.__version__} is too old. Need 2.15 or newer. "
            "Run: pip install --upgrade tensorflow tf-keras"
        )


try:
    validate_tensorflow()
except RuntimeError as exc:
    print(f"[attendance] TensorFlow validation failed: {exc}")
    raise SystemExit(1)

from deepface import DeepFace

try:
    from picamera2 import Picamera2
except Exception:
    Picamera2 = None

_HERE = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(_HERE, "dataset")
model_name = "ArcFace"
detector_backend = "opencv"
fallback_backend = "retinaface"
embeddings_file = os.path.join(_HERE, "deepface_embeddings.pkl")

frame_width = 1280
frame_height = 720
frame_fps = 30

use_picamera2 = Picamera2 is not None
picam2 = None
cam = None

if use_picamera2:
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (frame_width, frame_height), "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()
else:
    cam = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    cam.set(cv2.CAP_PROP_FPS, frame_fps)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

present = set()
vote_required = 3
votes = {}
max_frames = 600
detect_every = 6
detection_scale = 0.5
frame_index = 0

fps_estimate = 0.0
last_frame_time = time.time()

embeddings_data = None
embeddings = None
embedding_names = None
embedding_threshold = 0.40
if os.path.exists(embeddings_file):
    with open(embeddings_file, "rb") as f:
        embeddings_data = pickle.load(f)
    embeddings = np.asarray(embeddings_data.get("embeddings", []), dtype=np.float32)
    embedding_names = embeddings_data.get("names", [])
    embedding_threshold = float(embeddings_data.get("threshold", embedding_threshold))

    if embeddings.size > 0:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms

print(f"DeepFace mode: {model_name} + {detector_backend}")

try:
    for i in range(max_frames):

        if use_picamera2:
            rgb_frame = picam2.capture_array()
            frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            ret = True
        else:
            ret, frame = cam.read()

        if not ret:
            break

        frame_index += 1
        now_frame = time.time()
        dt = max(now_frame - last_frame_time, 1e-6)
        inst_fps = 1.0 / dt
        fps_estimate = inst_fps if fps_estimate == 0.0 else (fps_estimate * 0.9 + inst_fps * 0.1)
        last_frame_time = now_frame

        if frame_index % detect_every == 0:
            detect_frame = frame
            if detection_scale != 1.0:
                detect_frame = cv2.resize(
                    frame,
                    (0, 0),
                    fx=detection_scale,
                    fy=detection_scale,
                    interpolation=cv2.INTER_LINEAR,
                )
            try:
                faces = DeepFace.extract_faces(
                    img_path=detect_frame,
                    detector_backend=detector_backend,
                    enforce_detection=False,
                    align=True,
                )
            except Exception:
                faces = DeepFace.extract_faces(
                    img_path=detect_frame,
                    detector_backend=fallback_backend,
                    enforce_detection=False,
                    align=True,
                )

            scale = 1.0 / detection_scale

            for face_obj in faces:
                face = face_obj.get("face")
                area = face_obj.get("facial_area", {})
                x = int(area.get("x", 0) * scale)
                y = int(area.get("y", 0) * scale)
                w = int(area.get("w", 0) * scale)
                h = int(area.get("h", 0) * scale)

                name = "Unknown"
                if embeddings is not None and embeddings.size > 0 and embedding_names:
                    try:
                        reps = DeepFace.represent(
                            img_path=face,
                            model_name=model_name,
                            detector_backend="skip",
                            enforce_detection=False,
                            align=False,
                        )
                    except Exception:
                        reps = []

                    if reps:
                        vec = np.asarray(reps[0].get("embedding"), dtype=np.float32)
                        norm = np.linalg.norm(vec)
                        if norm != 0:
                            vec = vec / norm

                        distances = 1.0 - np.dot(embeddings, vec)
                        best_per_name = {}
                        for idx, dist in enumerate(distances):
                            person = embedding_names[idx]
                            if person not in best_per_name or dist < best_per_name[person]:
                                best_per_name[person] = float(dist)

                        sorted_candidates = sorted(best_per_name.items(), key=lambda item: item[1])
                        if sorted_candidates:
                            best_name, best_dist = sorted_candidates[0]
                            second_dist = sorted_candidates[1][1] if len(sorted_candidates) > 1 else 1.0
                            confidence = max(0.0, min(1.0, 1.0 - best_dist)) * 100.0

                            adaptive_threshold = embedding_threshold
                            if best_dist < 0.52 and (second_dist - best_dist) >= 0.12:
                                adaptive_threshold = 0.52

                            if best_dist < adaptive_threshold and (second_dist - best_dist) >= 0.04:
                                name = best_name
                else:  # fallback: DeepFace.find against dataset folder
                    try:
                        dfs = DeepFace.find(
                            img_path=face,
                            db_path=db_path,
                            model_name=model_name,
                            detector_backend="skip",
                            enforce_detection=False,
                            silent=True,
                        )
                    except Exception:
                        dfs = []

                    if dfs and len(dfs) > 0 and not dfs[0].empty:
                        df = dfs[0].sort_values("distance")
                        best = df.iloc[0]
                        distance = float(best["distance"]) if "distance" in best else None
                        threshold = float(best["threshold"]) if "threshold" in best else None
                        identity = str(best["identity"]) if "identity" in best else ""
                        if identity:
                            name = os.path.basename(os.path.dirname(identity))

                        if threshold is not None and distance is not None and distance > threshold:
                            name = "Unknown"

                if name != "Unknown":
                    votes[name] = votes.get(name, 0) + 1
                    if votes[name] >= vote_required:
                        present.add(name)
                        print(f"[PRESENT] {name}  (votes={votes[name]})")
finally:
    if cam is not None:
        cam.release()
    if picam2 is not None:
        picam2.stop()

with open("attendance.csv", "a") as f:
    for name in present:
        f.write(f"{name},{datetime.now()}\n")

print("Attendance:", present)

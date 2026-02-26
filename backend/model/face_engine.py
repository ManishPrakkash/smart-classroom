"""
face_engine.py
──────────────
Thread-safe face-detection engine built on top of DeepFace + ArcFace.

Usage (from app.py):
    from model.face_engine import engine          # singleton
    engine.start(session_date="2026-02-20")
    status = engine.get_status()
    engine.stop()

Architecture (after performance optimisation):
  • _capture_thread  – runs at full camera speed, stores latest raw frame
  • _detect_loop     – reads raw frames, runs DeepFace every N frames via
                       a ThreadPoolExecutor, annotates & JPEG-encodes output

This separation means the live preview runs at camera speed (~20-30 fps on
a Pi 5) while face detection happens asynchronously without blocking frames.
"""

from __future__ import annotations

import os
import sys
import pickle
import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime
from typing import Optional

import numpy as np

# ── Logging ───────────────────────────────────────────────────────────────────
logger = logging.getLogger("face_engine")

# ── Optional heavy imports (fail gracefully on dev machines) ──────────────────
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

try:
    import cv2                          # type: ignore
    _CV2_OK = True
except ImportError:
    _CV2_OK = False
    logger.warning("cv2 not available – face detection disabled")

try:
    from deepface import DeepFace       # type: ignore
    _DF_OK = True
except Exception:
    _DF_OK = False
    logger.warning("DeepFace not available – face detection disabled")

try:
    from picamera2 import Picamera2     # type: ignore
    _PICAM_OK = True
except Exception:
    _PICAM_OK = False

# ── libcamera-vid subprocess fallback (RPi 5 with Python != system ver) ───────
import shutil as _shutil
_LIBCAM_BIN = _shutil.which("libcamera-vid") or _shutil.which("rpicam-vid")
_LIBCAM_OK  = (not _PICAM_OK) and (_LIBCAM_BIN is not None)


class _LibcameraCapture:
    """Read MJPEG frames from a libcamera-vid subprocess.

    Used on RPi 5 when picamera2 Python bindings are compiled for a different
    Python version than the one running in the venv (e.g. system 3.13 vs
    pyenv 3.11).  Spawns `libcamera-vid --codec mjpeg -o -` and decodes JPEG
    frames from the raw byte stream.
    """

    _SOI = b"\xff\xd8"
    _EOI = b"\xff\xd9"

    def __init__(self, width: int = 640, height: int = 480, fps: int = 30):
        import subprocess
        cmd = [
            _LIBCAM_BIN,
            "-t", "0",
            "--codec", "mjpeg",
            "--width",  str(width),
            "--height", str(height),
            "--framerate", str(fps),
            "--nopreview",
            "--flush",
            "-o", "-",
        ]
        logger.info("Spawning: %s", " ".join(cmd))
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        time.sleep(1.5)            # give libcamera-vid time to initialise
        self._buf:    bytes = b""
        self._opened: bool  = self._proc.poll() is None
        if not self._opened:
            err = self._proc.stderr.read(500).decode(errors="replace")
            logger.error("libcamera-vid failed to start: %s", err)

    def isOpened(self) -> bool:
        return self._opened and self._proc.poll() is None

    def read(self):
        """Return (ok, bgr_frame) like cv2.VideoCapture.read()."""
        try:
            while True:
                chunk = self._proc.stdout.read(65536)
                if not chunk:
                    return False, None
                self._buf += chunk

                start = self._buf.find(self._SOI)
                if start == -1:
                    self._buf = b""
                    continue

                end = self._buf.find(self._EOI, start + 2)
                if end == -1:
                    continue          # need more data

                jpeg       = self._buf[start : end + 2]
                self._buf  = self._buf[end + 2 :]

                arr   = np.frombuffer(jpeg, dtype=np.uint8)
                frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if frame is None:
                    continue
                return True, frame
        except Exception as exc:
            logger.debug("_LibcameraCapture.read() error: %s", exc)
            return False, None

    def release(self):
        self._opened = False
        try:
            self._proc.terminate()
            self._proc.wait(timeout=3)
        except Exception:
            pass

# ── Firebase Admin SDK ────────────────────────────────────────────────────────
try:
    import firebase_admin                                    # type: ignore
    from firebase_admin import credentials, firestore        # type: ignore
    _FB_OK = True
except ImportError:
    _FB_OK = False
    logger.warning("firebase-admin not installed – Firestore writes disabled")

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)

EMBEDDINGS_FILE = os.path.join(_HERE, "deepface_embeddings.pkl")
NAME_MAPPING_FILE = os.path.join(_HERE, "name_mapping.json")
SERVICE_ACCOUNT  = os.path.join(_BACKEND, "smart-class-da901-firebase-adminsdk-fbsvc-3b7bc6538d.json")

# ── Name mapping ──────────────────────────────────────────────────────────────────
#
# Two-layer approach:
#   1. _PKL_OVERRIDE   – loaded from name_mapping.json (hand-edited overrides only,
#                        needed when a pkl name is ambiguous, e.g. "manish" could
#                        be two different students).
#   2. _PKL_AUTO_MAP   – built at runtime by reading unique names from the pkl and
#                        auto-matching each to a student rollNo.  Re-built every
#                        time the pkl is loaded so adding new people to the pkl
#                        is instantly picked up with no manual edits needed.

import difflib
import json as _json

_PKL_OVERRIDE: dict[str, str] = {}   # lowercase pkl_name → rollNo  (from JSON)
_PKL_AUTO_MAP: dict[str, str] = {}   # lowercase pkl_name → rollNo  (auto)


def _load_override_mapping():
    """Load name_mapping.json as manual overrides (only used for ambiguous names)."""
    global _PKL_OVERRIDE
    if not os.path.exists(NAME_MAPPING_FILE):
        _PKL_OVERRIDE = {}
        return
    try:
        with open(NAME_MAPPING_FILE, "r", encoding="utf-8") as fh:
            raw = _json.load(fh)
        _PKL_OVERRIDE = {
            k.strip().lower(): v.strip()
            for k, v in raw.items()
            if not k.startswith("_") and v and v.strip()
        }
        if _PKL_OVERRIDE:
            logger.info("Loaded %d manual overrides from name_mapping.json", len(_PKL_OVERRIDE))
    except Exception as exc:
        logger.warning("name_mapping.json read error: %s", exc)
        _PKL_OVERRIDE = {}


def _auto_build_pkl_mapping(pkl_names: list[str]):
    """
    For every unique name found in the pkl, try to find the matching student
    rollNo using progressive fuzzy matching against _NAME_TO_ROLL.

    Match priority:
      1. Exact key           e.g. "KAVIN KUMAR C" in _NAME_TO_ROLL
      2. First-word prefix   e.g. pkl="Keerthi Aanand" matches "KEERTHI AANAND K S"
      3. Sequence similarity  closest difflib match above 0.6 score

    Ambiguous matches (two students score equally) are left unresolved here;
    they must be resolved via name_mapping.json overrides.
    """
    global _PKL_AUTO_MAP
    _PKL_AUTO_MAP = {}
    unique_names = sorted(set(pkl_names))

    for raw in unique_names:
        lower = raw.strip().lower()

        # Skip if already covered by a manual override
        if lower in _PKL_OVERRIDE:
            continue

        key = raw.strip().upper()
        resolved: Optional[str] = None
        all_mapped_keys = list(_NAME_TO_ROLL.keys())

        # 1. Exact key match
        if key in _NAME_TO_ROLL:
            resolved = _NAME_TO_ROLL[key]

        # 2. First-word prefix match
        if resolved is None:
            candidates = []
            for mk in all_mapped_keys:
                parts = mk.replace('.', ' ').split()
                if parts and parts[0] == key:
                    candidates.append(_NAME_TO_ROLL[mk])
            # Only resolve if unambiguous
            unique_candidates = list(dict.fromkeys(candidates))  # preserve order, dedup
            if len(unique_candidates) == 1:
                resolved = unique_candidates[0]
            elif len(unique_candidates) > 1:
                logger.warning(
                    "pkl name '%s' is ambiguous (matches: %s) — add an override to name_mapping.json",
                    raw, unique_candidates
                )

        # 3. Multi-word prefix (e.g. "Keerthi Aanand" → "KEERTHI AANAND K S")
        if resolved is None:
            words = key.split()
            if len(words) >= 2:
                prefix = ' '.join(words)
                candidates = []
                for mk in all_mapped_keys:
                    if mk.replace('.', ' ').startswith(prefix):
                        candidates.append(_NAME_TO_ROLL[mk])
                unique_candidates = list(dict.fromkeys(candidates))
                if len(unique_candidates) == 1:
                    resolved = unique_candidates[0]

        # 4. Sequence similarity fallback
        if resolved is None:
            scores = [
                (mk, difflib.SequenceMatcher(None, key, mk.replace('.', ' ')).ratio())
                for mk in all_mapped_keys
            ]
            scores.sort(key=lambda x: x[1], reverse=True)
            if scores and scores[0][1] >= 0.60:
                # Ambiguity check: second candidate must be meaningfully worse
                top_score  = scores[0][1]
                second_score = scores[1][1] if len(scores) > 1 else 0.0
                if (top_score - second_score) >= 0.10:
                    resolved = _NAME_TO_ROLL[scores[0][0]]

        if resolved:
            _PKL_AUTO_MAP[lower] = resolved
            # Find student name for friendly log
            s_name = next((s["name"] for s in _STUDENTS if s["rollNo"] == resolved), resolved)
            logger.info("pkl '%s' → %s (%s) [auto-mapped]", raw, resolved, s_name)
        else:
            logger.warning("pkl '%s' → no student match found; add to name_mapping.json", raw)


_load_override_mapping()

# ── Firebase init (once, shared with app.py if already initialised) ───────────
_db = None

def _init_firebase():
    global _db
    if not _FB_OK:
        return
    if not os.path.exists(SERVICE_ACCOUNT):
        logger.warning("Service account JSON not found at %s", SERVICE_ACCOUNT)
        return
    try:
        # Reuse existing app if already initialised by app.py
        try:
            app = firebase_admin.get_app("face-engine")
        except ValueError:
            cred = credentials.Certificate(SERVICE_ACCOUNT)
            app  = firebase_admin.initialize_app(cred, name="face-engine")
        _db = firestore.client(app=app)
        logger.info("Firestore client initialised (face-engine)")
    except Exception as exc:
        logger.error("Firebase init error: %s", exc)

_init_firebase()


# ── Student name→rollNo lookup ────────────────────────────────────────────────
# Loaded once from students_map.json (generated below) or inline from seed list.
# The ML model identifies people by the *folder name* in the dataset.
# That folder name may be a roll number or a student name — this map bridges both.

_STUDENTS: list[dict] = []          # [{"rollNo": "24CS071", "name": "HARI VIGNESH"}, …]
_NAME_TO_ROLL: dict[str, str] = {}  # detected_name (from pkl) → rollNo

def load_students(students: list[dict]):
    """
    Called by app.py at startup with the canonical student list.
    students: [{"rollNo": str, "name": str}, …]
    After building the student lookup, auto-build the pkl→rollNo mapping
    so any names currently in the pkl are resolved immediately.
    """
    global _STUDENTS, _NAME_TO_ROLL
    _STUDENTS = students
    _NAME_TO_ROLL = {}
    for s in students:
        roll = s["rollNo"]
        name = s["name"]
        _NAME_TO_ROLL[roll.upper()] = roll
        _NAME_TO_ROLL[name.upper()] = roll
    logger.info("Loaded %d students into face_engine", len(students))
    # Trigger auto-build if pkl already exists
    if os.path.exists(EMBEDDINGS_FILE):
        try:
            with open(EMBEDDINGS_FILE, "rb") as f:
                _d = pickle.load(f)
            _auto_build_pkl_mapping(_d.get("names", []))
        except Exception as exc:
            logger.warning("Auto-map at load_students failed: %s", exc)

def _detected_name_to_roll(detected: str) -> Optional[str]:
    """
    Map a pkl folder/label name to a rollNo.

    Priority:
      0. Manual override from name_mapping.json (resolves ambiguous first names)
      1. Auto-built mapping from pkl unique names (built at startup & each scan)
      2. Exact key match in _NAME_TO_ROLL
      3. Multi-word prefix match (e.g. "Keerthi Aanand" in "KEERTHI AANAND K S")
      4. First-word prefix match (e.g. "MANISH" first word of a unique student)
    """
    if not detected or not detected.strip():
        return None

    raw  = detected.strip()
    low  = raw.lower()
    key  = raw.upper()

    # 0. Manual JSON override
    if low in _PKL_OVERRIDE:
        return _PKL_OVERRIDE[low]

    # 1. Auto-built mapping (derived from pkl unique names)
    if low in _PKL_AUTO_MAP:
        return _PKL_AUTO_MAP[low]

    # 2. Exact key in student lookup
    if key in _NAME_TO_ROLL:
        return _NAME_TO_ROLL[key]

    # 3. Multi-word prefix (e.g. "Keerthi Aanand" → "KEERTHI AANAND K S")
    words = key.split()
    if len(words) >= 2:
        prefix = ' '.join(words)
        for mk, roll in _NAME_TO_ROLL.items():
            if mk.replace('.', ' ').startswith(prefix):
                return roll

    # 4. First-word prefix — only when unambiguous
    candidates = []
    for mk, roll in _NAME_TO_ROLL.items():
        parts = mk.replace('.', ' ').split()
        if parts and parts[0] == key:
            if roll not in candidates:
                candidates.append(roll)
    if len(candidates) == 1:
        return candidates[0]

    logger.debug("No rollNo mapping for detected name: '%s'", raw)
    return None


# ── Embedding loader ──────────────────────────────────────────────────────────

def _load_embeddings():
    """Load pkl, normalise embeddings, and refresh the auto pkl→roll mapping."""
    if not os.path.exists(EMBEDDINGS_FILE):
        logger.warning("Embeddings file not found: %s", EMBEDDINGS_FILE)
        return None, None, 0.40

    with open(EMBEDDINGS_FILE, "rb") as f:
        data = pickle.load(f)

    embs   = np.asarray(data.get("embeddings", []), dtype=np.float32)
    names  = data.get("names", [])
    thresh = float(data.get("threshold", 0.40))

    if embs.size > 0:
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embs = embs / norms

    # Re-load override JSON in case the user edited it between scans
    _load_override_mapping()
    # Rebuild auto-mapping from the current pkl unique names
    _auto_build_pkl_mapping(names)

    unique = sorted(set(names))
    logger.info(
        "Loaded %d embeddings, %d unique people from pkl (threshold=%.2f): %s",
        len(names), len(unique), thresh, unique
    )
    return embs, names, thresh


# ── Firestore writer ──────────────────────────────────────────────────────────

def _mark_present_firebase(date: str, roll_no: str, student_name: str):
    """Update attendance/{date}/records/{rollNo} → status=present."""
    if _db is None:
        logger.warning("Firestore not available – skipping write for %s", roll_no)
        return
    try:
        ref = _db.collection("attendance").document(date) \
                 .collection("records").document(roll_no)
        ref.set({
            "rollNo":    roll_no,
            "name":      student_name,
            "status":    "present",
            "odType":    None,
            "source":    "camera",
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }, merge=True)

        # Also touch the parent summary doc so it exists
        _db.collection("attendance").document(date).set({
            "date":       date,
            "classLabel": "24CS (Batch 2024)",
            "markedAt":   firestore.SERVER_TIMESTAMP,
        }, merge=True)

        logger.info("[Firestore] Marked present: %s (%s) on %s", student_name, roll_no, date)
    except Exception as exc:
        logger.error("[Firestore] Write error for %s: %s", roll_no, exc)


# ── Session state ─────────────────────────────────────────────────────────────

class _State:
    IDLE     = "idle"
    RUNNING  = "running"
    STOPPING = "stopping"


class FaceEngine:
    """
    Singleton engine. Call start() / stop() from Flask routes or scheduler.
    All public methods are thread-safe.
    """

    def __init__(self):
        self._lock   = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Status fields (read by get_status())
        self._state          = _State.IDLE
        self._session_date   = ""
        self._detected_so_far: list[str] = []   # rollNo list
        self._last_seen: dict[str, str]  = {}   # rollNo → name
        self._started_at: Optional[str]  = None
        self._stopped_at: Optional[str]  = None
        self._error: Optional[str]       = None
        self._frame_count    = 0
        self._fps            = 0.0

        # Live frame buffer (JPEG bytes of the latest annotated frame)
        self._frame_lock   = threading.Lock()
        self._latest_jpeg: Optional[bytes]   = None
        self._face_boxes:  list[dict]        = []   # [{label, confirmed, facial_area}]

        # Raw frame double-buffer (written by capture thread, read by detect loop)
        self._raw_lock  = threading.Lock()
        self._raw_frame: Optional[object] = None   # latest BGR numpy array

        # Config
        self.max_duration_s   = int(os.getenv("CAM_MAX_DURATION", 600))   # 10 min default
        self.vote_required    = int(os.getenv("CAM_VOTES", 3))
        self.detect_every     = int(os.getenv("CAM_DETECT_EVERY", 10))   # was 6
        self.detection_scale  = float(os.getenv("CAM_SCALE", 0.5))
        self.model_name       = os.getenv("CAM_MODEL", "ArcFace")
        self.detector_backend = os.getenv("CAM_DETECTOR", "opencv")
        self.fallback_backend = os.getenv("CAM_FALLBACK", "retinaface")
        self.jpeg_quality     = int(os.getenv("CAM_JPEG_QUALITY", 55))   # was 70
        self.preview_every    = int(os.getenv("CAM_PREVIEW_EVERY", 5))   # heartbeat frames

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self, session_date: Optional[str] = None) -> dict:
        with self._lock:
            if self._state == _State.RUNNING:
                return {"ok": False, "reason": "Already running"}
            if not _CV2_OK or not _DF_OK:
                return {"ok": False, "reason": "cv2 or DeepFace not available on this machine"}

            date = session_date or datetime.now().strftime("%Y-%m-%d")
            self._session_date   = date
            self._detected_so_far = []
            self._last_seen      = {}
            self._started_at     = datetime.now().isoformat(timespec="seconds")
            self._stopped_at     = None
            self._error          = None
            self._frame_count    = 0
            self._fps            = 0.0
            self._stop_event.clear()
            self._state          = _State.RUNNING

            self._thread = threading.Thread(
                target=self._run_loop,
                daemon=True,
                name="face-detection"
            )
            self._thread.start()
            logger.info("Face detection started for date=%s", date)
            return {"ok": True, "date": date, "detect_every": self.detect_every}

    def stop(self) -> dict:
        with self._lock:
            if self._state != _State.RUNNING:
                return {"ok": False, "reason": "Not running"}
            self._state = _State.STOPPING
        self._stop_event.set()
        logger.info("Stop requested for face detection session")
        return {"ok": True}

    def get_frame(self) -> Optional[bytes]:
        """Return the latest annotated JPEG frame, or None if not available."""
        with self._frame_lock:
            return self._latest_jpeg

    def get_status(self) -> dict:
        with self._lock:
            return {
                "state":         self._state,
                "session_date":  self._session_date,
                "detected":      list(self._detected_so_far),
                "last_seen":     dict(self._last_seen),
                "started_at":    self._started_at,
                "stopped_at":    self._stopped_at,
                "frame_count":   self._frame_count,
                "fps":           round(self._fps, 1),
                "error":         self._error,
                "embeddings_ok": os.path.exists(EMBEDDINGS_FILE),
                "firebase_ok":   _db is not None,
            }

    # ── Frame annotation ──────────────────────────────────────────────────────

    def _store_annotated_frame(self, frame):
        """Draw bounding boxes + labels on frame and store as JPEG.

        Only called after a detection pass or on the preview heartbeat.
        Reuses the last-known face boxes so the display stays live even
        between detection passes.
        """
        if not _CV2_OK:
            return
        annotated = frame.copy()
        h, w = annotated.shape[:2]

        with self._frame_lock:
            boxes = list(self._face_boxes)

        for box in boxes:
            x, y, bw, bh = box["x"], box["y"], box["w"], box["h"]
            label     = box.get("label", "")
            confirmed = box.get("confirmed", False)

            color  = (0, 200, 80) if confirmed else (0, 180, 255)   # green / orange
            thick  = 2

            # Clamp coords
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(w - 1, x + bw), min(h - 1, y + bh)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thick)

            # Label background + text
            font       = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            font_thick = 1
            (tw, th), _ = cv2.getTextSize(label, font, font_scale, font_thick)
            ty = max(y1 - 6, th + 4)
            cv2.rectangle(annotated, (x1, ty - th - 4), (x1 + tw + 6, ty + 2), color, -1)
            cv2.putText(annotated, label, (x1 + 3, ty - 2),
                        font, font_scale, (0, 0, 0), font_thick, cv2.LINE_AA)

            if confirmed:
                cv2.putText(annotated, "\u2713 PRESENT", (x1 + 3, y2 - 6),
                            font, 0.45, (0, 220, 80), 1, cv2.LINE_AA)

        # FPS watermark
        with self._lock:
            fps = self._fps
        cv2.putText(annotated, f"{fps:.1f} fps", (8, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

        ret, buf = cv2.imencode(".jpg", annotated,
                                [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
        if ret:
            with self._frame_lock:
                self._latest_jpeg = bytes(buf)

    # ── Capture thread ────────────────────────────────────────────────────────

    def _capture_thread_fn(self, picam2, libcam, cam):
        """Dedicated capture thread: grab frames as fast as the camera allows
        and store the latest one in the raw-frame double buffer.
        Exits when _stop_event is set.
        """
        while not self._stop_event.is_set():
            try:
                if picam2:
                    rgb   = picam2.capture_array()
                    frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                    ok    = True
                elif libcam:
                    ok, frame = libcam.read()
                else:
                    ok, frame = cam.read()

                if ok and frame is not None:
                    with self._raw_lock:
                        self._raw_frame = frame
                else:
                    time.sleep(0.005)
            except Exception as exc:
                logger.debug("Capture thread error: %s", exc)
                time.sleep(0.01)

    # ── Internal detection loop ───────────────────────────────────────────────

    def _run_loop(self):
        try:
            self._detect_loop()
        except Exception as exc:
            logger.exception("Face detection loop crashed: %s", exc)
            with self._lock:
                self._error   = str(exc)
                self._state   = _State.IDLE
                self._stopped_at = datetime.now().isoformat(timespec="seconds")
        else:
            with self._lock:
                self._state      = _State.IDLE
                self._stopped_at = datetime.now().isoformat(timespec="seconds")

    def _detect_loop(self):
        # Load embeddings fresh for this session
        embs, emb_names, threshold = _load_embeddings()

        # ── Open camera ───────────────────────────────────────────────────────
        picam2  = None
        libcam  = None
        cam     = None
        if _PICAM_OK:
            picam2 = Picamera2()
            # Use a lores stream at half-res for detection + full display stream
            # If lores is unavailable just use 640×480 on the main stream.
            try:
                config = picam2.create_preview_configuration(
                    main={"size": (640, 480), "format": "RGB888"},
                    lores={"size": (320, 240), "format": "YUV420"},
                )
                self._picam_has_lores = True
            except Exception:
                config = picam2.create_preview_configuration(
                    main={"size": (640, 480), "format": "RGB888"}
                )
                self._picam_has_lores = False
            picam2.configure(config)
            picam2.start()
            logger.info("Using PiCamera2 @ 640x480")
        elif _LIBCAM_OK:
            # RPi 5: libcamera Python bindings compiled for a different Python
            # version → use libcamera-vid subprocess and parse MJPEG stream.
            libcam = _LibcameraCapture(width=640, height=480, fps=30)
            if not libcam.isOpened():
                logger.warning("libcamera-vid subprocess failed; falling back to V4L2")
                libcam.release()
                libcam = None
            else:
                logger.info("Using libcamera-vid subprocess (%s) @ 640x480/30fps", _LIBCAM_BIN)
        if not picam2 and not libcam:
            # On Windows use DirectShow (CAP_DSHOW) for reliable webcam access;
            # on Linux/Pi fall back to CAP_V4L2 (or CAP_ANY when V4L2 absent).
            if sys.platform == "win32":
                backend = cv2.CAP_DSHOW
                backend_name = "DirectShow"
            elif hasattr(cv2, "CAP_V4L2"):
                backend = cv2.CAP_V4L2
                backend_name = "V4L2"
            else:
                backend = cv2.CAP_ANY
                backend_name = "CAP_ANY"
            cam = cv2.VideoCapture(0, backend)
            if not cam.isOpened():
                cam = cv2.VideoCapture(0)   # fallback: no backend hint
                backend_name += "(fallback)"
            cam.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cam.set(cv2.CAP_PROP_FPS,          30)
            cam.set(cv2.CAP_PROP_BUFFERSIZE,   1)   # keep buffer minimal → low latency
            logger.info("Using OpenCV VideoCapture(0) via %s @ 640x480/30fps", backend_name)

        # ── Start dedicated capture thread ────────────────────────────────────
        self._raw_frame = None
        cap_thread = threading.Thread(
            target=self._capture_thread_fn,
            args=(picam2, libcam, cam),
            daemon=True,
            name="cam-capture",
        )
        cap_thread.start()

        # Wait for the first frame
        for _ in range(100):   # up to ~1 second
            with self._raw_lock:
                if self._raw_frame is not None:
                    break
            time.sleep(0.01)

        votes:        dict[str, int] = {}
        present_set:  set[str]       = set()   # confirmed rollNos this session
        frame_idx     = 0
        preview_idx   = 0    # counts frames that reach the preview encoder
        fps_est       = 0.0
        cap_t         = time.time()
        deadline      = time.time() + self.max_duration_s

        # Detection is heavy — offload to a single-worker thread pool so the
        # capture + preview loop is never blocked by DeepFace.
        detect_future: Optional[Future] = None
        detect_frame:  Optional[object] = None   # frame being analysed

        with self._lock:
            date = self._session_date

        def _run_detection(small_frame, orig_frame):
            """Runs in the ThreadPoolExecutor. Returns (faces, orig_frame)."""
            try:
                faces = DeepFace.extract_faces(
                    img_path=small_frame,
                    detector_backend=self.detector_backend,
                    enforce_detection=False,
                    align=True,
                )
            except Exception:
                try:
                    faces = DeepFace.extract_faces(
                        img_path=small_frame,
                        detector_backend=self.fallback_backend,
                        enforce_detection=False,
                        align=True,
                    )
                except Exception:
                    faces = []
            return faces, orig_frame

        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="deepface")

        try:
            while not self._stop_event.is_set() and time.time() < deadline:
                # ── Grab latest raw frame from capture thread ─────────────────
                with self._raw_lock:
                    frame = self._raw_frame

                if frame is None:
                    time.sleep(0.005)
                    continue

                frame_idx += 1
                now   = time.time()
                dt    = max(now - cap_t, 1e-6)
                fps_est = fps_est * 0.9 + (1.0 / dt) * 0.1
                cap_t   = now

                with self._lock:
                    self._frame_count = frame_idx
                    self._fps         = fps_est

                # ── Check if the async detection task finished ────────────────
                if detect_future is not None and detect_future.done():
                    try:
                        faces, _df = detect_future.result()
                    except Exception as exc:
                        logger.debug("Detection task error: %s", exc)
                        faces = []
                    detect_future = None

                    # Update bounding boxes
                    scale = 1.0 / self.detection_scale if self.detection_scale != 1.0 else 1.0
                    with self._frame_lock:
                        self._face_boxes = []
                        for fo in faces:
                            fa = fo.get("facial_area") or {}
                            if fa:
                                self._face_boxes.append({
                                    "x": int(fa.get("x", 0) * scale),
                                    "y": int(fa.get("y", 0) * scale),
                                    "w": int(fa.get("w", 50) * scale),
                                    "h": int(fa.get("h", 50) * scale),
                                    "label": "...",
                                    "confirmed": False,
                                })

                    # Identify each detected face (still on this thread — fast)
                    for face_obj in faces:
                        face          = face_obj.get("face")
                        detected_name = "Unknown"

                        if embs is not None and embs.size > 0 and emb_names:
                            try:
                                reps = DeepFace.represent(
                                    img_path=face,
                                    model_name=self.model_name,
                                    detector_backend="skip",
                                    enforce_detection=False,
                                    align=False,
                                )
                            except Exception:
                                reps = []

                            if reps:
                                vec  = np.asarray(reps[0].get("embedding"), dtype=np.float32)
                                norm = np.linalg.norm(vec)
                                if norm:
                                    vec = vec / norm

                                distances  = 1.0 - np.dot(embs, vec)
                                best_per_n: dict[str, float] = {}
                                for i, dist in enumerate(distances):
                                    person = emb_names[i]
                                    if person not in best_per_n or dist < best_per_n[person]:
                                        best_per_n[person] = float(dist)

                                sorted_c = sorted(best_per_n.items(), key=lambda x: x[1])
                                if sorted_c:
                                    best_name, best_dist = sorted_c[0]
                                    second_dist = sorted_c[1][1] if len(sorted_c) > 1 else 1.0
                                    adaptive_thresh = threshold
                                    if best_dist < 0.52 and (second_dist - best_dist) >= 0.12:
                                        adaptive_thresh = 0.52
                                    if best_dist < adaptive_thresh and (second_dist - best_dist) >= 0.04:
                                        detected_name = best_name

                        if detected_name == "Unknown":
                            continue

                        roll = _detected_name_to_roll(detected_name)
                        if roll is None:
                            logger.debug("No rollNo mapping for detected name: %s", detected_name)
                            continue

                        if roll in present_set:
                            continue  # already confirmed

                        votes[roll] = votes.get(roll, 0) + 1
                        logger.debug("Vote %d/%d for %s (%s)",
                                     votes[roll], self.vote_required, detected_name, roll)

                        if votes[roll] >= self.vote_required:
                            present_set.add(roll)
                            s_name = next(
                                (s["name"] for s in _STUDENTS if s["rollNo"] == roll),
                                detected_name
                            )
                            _mark_present_firebase(date, roll, s_name)
                            with self._lock:
                                if roll not in self._detected_so_far:
                                    self._detected_so_far.append(roll)
                                self._last_seen[roll] = s_name
                            with self._frame_lock:
                                for box in self._face_boxes:
                                    if box.get("label") in (detected_name, "...", "Unknown"):
                                        box["label"]     = s_name
                                        box["confirmed"] = True
                                        break

                    # Always annotate right after a detection pass finishes
                    self._store_annotated_frame(frame)
                    preview_idx = 0   # reset heartbeat counter

                # ── Submit a new detection task if idle and it's time ─────────
                if detect_future is None and (frame_idx % self.detect_every == 0):
                    if self.detection_scale != 1.0:
                        small = cv2.resize(frame, (0, 0),
                                           fx=self.detection_scale,
                                           fy=self.detection_scale,
                                           interpolation=cv2.INTER_LINEAR)
                    else:
                        small = frame
                    detect_future = executor.submit(_run_detection, small, frame)

                # ── Heartbeat: encode a preview frame every N frames so the
                #    live feed stays smooth even between detection passes ────────
                else:
                    preview_idx += 1
                    if preview_idx >= self.preview_every:
                        self._store_annotated_frame(frame)
                        preview_idx = 0

                # Yield CPU briefly — the capture thread runs independently
                time.sleep(0.001)

        finally:
            self._stop_event.set()   # also stops capture thread
            executor.shutdown(wait=False)
            cap_thread.join(timeout=3)
            if cam:
                cam.release()
            if libcam:
                libcam.release()
            if picam2:
                picam2.stop()
            logger.info("Detection session ended. Confirmed present: %s", list(present_set))


# ── Module-level singleton ────────────────────────────────────────────────────
engine = FaceEngine()


# ── Pre-warm ArcFace model in background so first scan has no download delay ──
def _prewarm_arcface():
    if not (_CV2_OK and _DF_OK):
        return
    weights = os.path.join(os.path.expanduser("~"), ".deepface", "weights", "arcface_weights.h5")
    if os.path.exists(weights):
        return   # already cached – nothing to do
    try:
        import numpy as _np
        logger.info("Pre-warming ArcFace model (first-time download ~137 MB)…")
        dummy = _np.zeros((100, 100, 3), dtype="uint8")
        DeepFace.represent(dummy, model_name="ArcFace", enforce_detection=False)
        logger.info("ArcFace model cached – future scans will start instantly")
    except Exception as exc:
        logger.warning("ArcFace pre-warm failed (will retry on first scan): %s", exc)

threading.Thread(target=_prewarm_arcface, daemon=True, name="arcface-prewarm").start()

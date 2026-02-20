import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from threading import Lock, Thread

import ntplib
import pytz

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from gpiozero import Button, Device, OutputDevice
from gpiozero.pins.mock import MockFactory
from gpiozero.exc import BadPinFactory

from devices import devices, switch_pins

# ── Face-detection engine (optional — disabled on machines without camera/TF) ──
try:
    from model.face_engine import engine as face_engine, load_students
    _FACE_ENGINE_OK = True
except Exception as _fe_err:
    face_engine   = None
    load_students = None
    _FACE_ENGINE_OK = False
    logging.getLogger("smart-switch").warning(
        "face_engine unavailable: %s", _fe_err
    )

# ── App setup ────────────────────────────────────────────

app = Flask("SmartSwitch")
CORS(app)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("smart-switch")

SCHEDULES_FILE = os.path.join(os.path.dirname(__file__), "schedules.json")
schedules_lock = Lock()

# ── NTP time sync ────────────────────────────────────────
#
# Raspberry Pi has no hardware RTC. Without internet on first boot the
# system clock is wrong, which breaks all schedules.
# We fetch the true time from NTP servers, compute the offset between
# NTP and the local clock, and apply that offset in ntp_now().
# This never requires root and works even without 'timedatectl'.

TIMEZONE    = pytz.timezone(os.getenv("TZ", "Asia/Kolkata"))  # change via TZ env var
_ntp_offset = 0.0          # seconds: ntp_utc - local_utc
_ntp_lock   = Lock()
NTP_SERVERS = ["pool.ntp.org", "time.google.com", "time.cloudflare.com"]

def sync_ntp():
    """Query NTP and update _ntp_offset. Safe to call from any thread."""
    global _ntp_offset
    c = ntplib.NTPClient()
    for server in NTP_SERVERS:
        try:
            resp = c.request(server, version=3, timeout=3)
            offset = resp.offset          # how many seconds NTP is ahead of us
            with _ntp_lock:
                _ntp_offset = offset
            logger.info("[NTP] Synced with %s  offset=%.3fs  true_time=%s",
                        server,
                        offset,
                        datetime.fromtimestamp(resp.tx_time, tz=timezone.utc)
                            .astimezone(TIMEZONE)
                            .strftime("%Y-%m-%d %H:%M:%S %Z"))
            return True
        except Exception as exc:
            logger.warning("[NTP] %s unreachable: %s", server, exc)
    logger.warning("[NTP] All servers failed — using system clock (offset unchanged)")
    return False

def ntp_now() -> datetime:
    """Return the current local time corrected by the last NTP offset."""
    with _ntp_lock:
        offset = _ntp_offset
    return datetime.fromtimestamp(time.time() + offset, tz=TIMEZONE)

# Run initial NTP sync in a background thread so startup isn't blocked
Thread(target=sync_ntp, daemon=True, name="ntp-init").start()

# ── Student list (used by face engine for name→rollNo mapping) ───────────────
# Mirrors frontend/src/students.js — keep in sync with seed_users.py

STUDENTS = [
    {"rollNo": "24CS071", "name": "HARI VIGNESH"},
    {"rollNo": "24CS072", "name": "HARINATH S"},
    {"rollNo": "24CS073", "name": "HARINI C"},
    {"rollNo": "24CS074", "name": "HARINI C H"},
    {"rollNo": "24CS075", "name": "HARINI K"},
    {"rollNo": "24CS076", "name": "HARIPRASATH M"},
    {"rollNo": "24CS077", "name": "HARIPRIYAN A"},
    {"rollNo": "24CS078", "name": "HARIS BALAJEE P L"},
    {"rollNo": "24CS079", "name": "HARISH G"},
    {"rollNo": "24CS080", "name": "HARISH KUMAR V"},
    {"rollNo": "24CS081", "name": "HARISH S"},
    {"rollNo": "24CS082", "name": "HARITHA E"},
    {"rollNo": "24CS083", "name": "HARSHAD R"},
    {"rollNo": "24CS084", "name": "HARSHINI A"},
    {"rollNo": "24CS085", "name": "HARSHITHA M P"},
    {"rollNo": "24CS086", "name": "HERANYAA T P"},
    {"rollNo": "24CS087", "name": "ILAMSARAVANBALAJI PA"},
    {"rollNo": "24CS088", "name": "JAGATHRATCHAGAN M"},
    {"rollNo": "24CS089", "name": "JAIANISH J"},
    {"rollNo": "24CS090", "name": "JAISURYA S"},
    {"rollNo": "24CS091", "name": "JASHWANTH J"},
    {"rollNo": "24CS092", "name": "JAY PRAKASH SAH"},
    {"rollNo": "24CS093", "name": "JAYASURIYA S"},
    {"rollNo": "24CS094", "name": "JAYATHEERTHAN P"},
    {"rollNo": "24CS095", "name": "JEFF JEROME JABEZ"},
    {"rollNo": "24CS096", "name": "JENITHA M"},
    {"rollNo": "24CS097", "name": "JOSHUA RUBERT R"},
    {"rollNo": "24CS098", "name": "JUMAANAH BASHEETH"},
    {"rollNo": "24CS101", "name": "KANHAIYA PATEL"},
    {"rollNo": "24CS102", "name": "KANISH KRISHNA J P"},
    {"rollNo": "24CS103", "name": "KANISH M R"},
    {"rollNo": "24CS104", "name": "KANISHKA S"},
    {"rollNo": "24CS105", "name": "KANWAL KISHORE"},
    {"rollNo": "24CS106", "name": "KARTHIKA A"},
    {"rollNo": "24CS107", "name": "KARUNESH A R"},
    {"rollNo": "24CS108", "name": "KATHIRAVAN S P"},
    {"rollNo": "24CS109", "name": "KATHIRVEL S"},
    {"rollNo": "24CS110", "name": "KAVIN KUMAR C"},
    {"rollNo": "24CS111", "name": "KAVIN PRAKASH T"},
    {"rollNo": "24CS112", "name": "KAVIPRIYA P"},
    {"rollNo": "24CS113", "name": "KAVYA K"},
    {"rollNo": "24CS114", "name": "KAVYASRI D"},
    {"rollNo": "24CS115", "name": "KEERTHI AANAND K S"},
    {"rollNo": "24CS116", "name": "KHAVIYA SREE M"},
    {"rollNo": "24CS117", "name": "KIRITH MALINI D S"},
    {"rollNo": "24CS118", "name": "KIRITHIKA S K"},
    {"rollNo": "24CS119", "name": "KOWSALYA V"},
    {"rollNo": "24CS120", "name": "KRISHNA VARUN K"},
    {"rollNo": "24CS121", "name": "KRISHNAN A"},
    {"rollNo": "24CS122", "name": "LAVANYA R"},
    {"rollNo": "24CS123", "name": "LOGAPRABHU S"},
    {"rollNo": "24CS124", "name": "LOGAVARSHHNI S"},
    {"rollNo": "24CS125", "name": "MADHANIKA M"},
    {"rollNo": "24CS126", "name": "MADHUMITHA Y"},
    {"rollNo": "24CS127", "name": "MADHUSREE M"},
    {"rollNo": "24CS128", "name": "MANASA DEVI CHAPAGAIN"},
    {"rollNo": "24CS129", "name": "MANISH BASNET"},
    {"rollNo": "24CS130", "name": "MANISH PRAKKASH M S"},
    {"rollNo": "24CS131", "name": "MANOJ V"},
    {"rollNo": "24CS132", "name": "MANOJKUMAR S"},
    {"rollNo": "24CS133", "name": "MANSUR ANSARI"},
    {"rollNo": "24CS134", "name": "MATHIYAZHINI S"},
    {"rollNo": "24CS135", "name": "MATHUMITHA S"},
    {"rollNo": "24CS136", "name": "MEKALA S"},
    {"rollNo": "24CS137", "name": "MITHRHA Y"},
    {"rollNo": "24CS138", "name": "MOHAMED ASIF S"},
    {"rollNo": "24CS139", "name": "MOHAMMED SUHAIL M"},
    {"rollNo": "24CS140", "name": "MOHAN KAARTHICK C"},
    {"rollNo": "LE01",    "name": "NAVEEN N"},
    {"rollNo": "LE02",    "name": "SUJAY S"},
    {"rollNo": "LE03",    "name": "ABDHUL KAREEM L"},
]

if _FACE_ENGINE_OK and load_students:
    try:
        load_students(STUDENTS)
    except Exception as _ls_err:
        logger.warning("load_students failed: %s", _ls_err)

# ── GPIO setup ───────────────────────────────────────────

def setup_pin_factory():
    try:
        Device.ensure_pin_factory()
        logger.info("GPIO pin factory: %s", type(Device.pin_factory).__name__)
    except BadPinFactory as exc:
        if os.getenv("USE_MOCK_GPIO", "0") == "1":
            Device.pin_factory = MockFactory()
            logger.warning("Using MockFactory (no real GPIO). %s", exc)
            return
        logger.error("GPIO pin factory unavailable. %s", exc)
        raise

def create_relays():
    return {
        name: OutputDevice(pin, active_high=False)
        for name, pin in devices.items()
    }

setup_pin_factory()
relays = create_relays()

# ── Physical switch (push-button) setup ─────────────────
#
# Each push button is wired between its GPIO input pin and GND.
# The internal pull-up resistor keeps the pin HIGH when idle.
# Pressing the button pulls it LOW → gpiozero fires when_pressed.
# The callback simply toggles whichever relay the button controls.
# Because /states always reads live relay state, the next frontend
# poll (every 1 s) will automatically reflect the physical change.

def _make_toggle(relay, name):
    """Return a thread-safe closure that toggles one relay."""
    def _toggle():
        if relay.is_active:
            relay.off()
            logger.info("[Physical Switch] OFF  %s", name)
        else:
            relay.on()
            logger.info("[Physical Switch] ON   %s", name)
    return _toggle

def create_buttons():
    buttons = {}
    for name, pin in switch_pins.items():
        relay = relays.get(name)
        if relay is None:
            logger.warning("No relay found for switch '%s' (pin %s)", name, pin)
            continue
        try:
            btn = Button(pin, pull_up=True, bounce_time=0.05)
            btn.when_pressed = _make_toggle(relay, name)
            buttons[name] = btn
            logger.info("Physical switch '%s' listening on GPIO %s", name, pin)
        except Exception as exc:
            logger.warning("Could not set up button '%s' on GPIO %s: %s", name, pin, exc)
    return buttons

buttons = create_buttons()

# ── Schedule persistence ─────────────────────────────────

def load_schedules():
    if not os.path.exists(SCHEDULES_FILE):
        return []
    try:
        with open(SCHEDULES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_schedules(schedules):
    with open(SCHEDULES_FILE, "w") as f:
        json.dump(schedules, f, indent=2)

# ── Scheduler logic ──────────────────────────────────────

def run_schedules():
    """Called every minute by APScheduler. Uses NTP-corrected time."""
    now = ntp_now()
    current_time = now.strftime("%H:%M")
    current_day  = now.weekday()  # 0=Mon … 6=Sun

    with schedules_lock:
        schedules = load_schedules()

    for sched in schedules:
        if not sched.get("enabled", True):
            continue
        if current_day not in sched.get("days", list(range(7))):
            continue

        for device in sched.get("devices", []):
            relay = relays.get(device)
            if relay is None:
                continue
            if sched.get("on_time") == current_time:
                relay.on()
                logger.info("[Scheduler] ON  %s (schedule: %s)", device, sched.get("label"))
            if sched.get("off_time") == current_time:
                relay.off()
                logger.info("[Scheduler] OFF %s (schedule: %s)", device, sched.get("label"))

        # ── Auto-start camera attendance if schedule has attendance=True ──
        if sched.get("attendance") and sched.get("on_time") == current_time:
            if _FACE_ENGINE_OK and face_engine:
                date_str = now.strftime("%Y-%m-%d")
                result   = face_engine.start(session_date=date_str)
                logger.info("[Scheduler] Auto-start camera for %s: %s",
                            sched.get("label"), result)

        if sched.get("attendance") and sched.get("off_time") == current_time:
            if _FACE_ENGINE_OK and face_engine:
                result = face_engine.stop()
                logger.info("[Scheduler] Auto-stop camera for %s: %s",
                            sched.get("label"), result)

scheduler = BackgroundScheduler(timezone=TIMEZONE)
scheduler.add_job(run_schedules, "cron", minute="*")          # every minute
scheduler.add_job(sync_ntp,      "cron", hour="*", minute=0)  # re-sync every hour
scheduler.start()
logger.info("Scheduler started (timezone: %s)", TIMEZONE)

# ── Routes ───────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({
        "message": "Smart Switch API",
        "endpoints": {
            "status": "/status",
            "devices": "/devices",
            "states": "/states",
            "control": "/control/<device>/<state>",
            "schedules": "/schedules"
        }
    })

@app.route("/status")
def status():
    return jsonify({"status": "Smart Switch Running"})

@app.route("/time")
def server_time():
    """Return the NTP-corrected server time so the frontend can display it."""
    now = ntp_now()
    with _ntp_lock:
        offset = _ntp_offset
    return jsonify({
        "time":     now.strftime("%H:%M:%S"),
        "date":     now.strftime("%Y-%m-%d"),
        "timezone": str(TIMEZONE),
        "ntp_offset_s": round(offset, 3),
        "ntp_synced":   abs(offset) < 600,   # consider synced if offset < 10 min
    })

@app.route("/devices")
def list_devices():
    return jsonify(list(devices.keys()))

@app.route("/states")
def get_states():
    """Return current on/off state of every relay (reflects physical switch changes too)."""
    return jsonify({
        name: relay.is_active
        for name, relay in relays.items()
    })

@app.route("/control/<device>/<state>")
def control(device, state):
    relay = relays.get(device)
    if relay is None:
        return jsonify({"error": "Invalid device"}), 404
    if state not in {"on", "off"}:
        return jsonify({"error": "Invalid state"}), 400
    try:
        relay.on() if state == "on" else relay.off()
        logger.info("Set %s to %s", device, state)
    except Exception as exc:
        logger.error("Failed to set %s to %s: %s", device, state, exc)
        return jsonify({"error": "Hardware control failed"}), 500
    return jsonify({"device": device, "state": state, "is_active": relay.is_active})

# ── Schedule CRUD ────────────────────────────────────────

@app.route("/schedules", methods=["GET"])
def get_schedules():
    with schedules_lock:
        return jsonify(load_schedules())

@app.route("/schedules", methods=["POST"])
def create_schedule():
    data = request.get_json(force=True)
    required = {"devices", "on_time", "off_time"}
    if not required.issubset(data):
        return jsonify({"error": f"Missing fields: {required - data.keys()}"}), 400

    schedule = {
        "id":         str(uuid.uuid4()),
        "label":      data.get("label", "Untitled"),
        "devices":    data["devices"],
        "on_time":    data["on_time"],
        "off_time":   data["off_time"],
        "days":       data.get("days", list(range(7))),
        "enabled":    data.get("enabled", True),
        "attendance": data.get("attendance", False),  # auto-start camera when True
    }

    with schedules_lock:
        schedules = load_schedules()
        schedules.append(schedule)
        save_schedules(schedules)

    logger.info("Created schedule: %s", schedule["label"])
    return jsonify(schedule), 201

@app.route("/schedules/<sched_id>", methods=["DELETE"])
def delete_schedule(sched_id):
    with schedules_lock:
        schedules = load_schedules()
        new = [s for s in schedules if s["id"] != sched_id]
        if len(new) == len(schedules):
            return jsonify({"error": "Not found"}), 404
        save_schedules(new)
    logger.info("Deleted schedule %s", sched_id)
    return jsonify({"deleted": sched_id})

# ── Camera / Attendance routes ───────────────────────────────────────────────

@app.route("/attendance/camera", methods=["GET"])
def camera_status():
    """Return current face-detection engine status."""
    if not _FACE_ENGINE_OK or face_engine is None:
        return jsonify({"available": False,
                        "reason": "face_engine not available on this server"})
    status = face_engine.get_status()
    status["available"] = True
    return jsonify(status)


@app.route("/attendance/camera/start", methods=["POST"])
def camera_start():
    """Manually start a face-detection session for the given date (or today)."""
    if not _FACE_ENGINE_OK or face_engine is None:
        return jsonify({"ok": False, "reason": "face_engine not available"}), 503

    data = request.get_json(force=True, silent=True) or {}
    date_str = data.get("date") or ntp_now().strftime("%Y-%m-%d")
    result   = face_engine.start(session_date=date_str)
    code     = 200 if result["ok"] else 409
    return jsonify(result), code


@app.route("/attendance/camera/stop", methods=["POST"])
def camera_stop():
    """Stop the running face-detection session."""
    if not _FACE_ENGINE_OK or face_engine is None:
        return jsonify({"ok": False, "reason": "face_engine not available"}), 503
    result = face_engine.stop()
    return jsonify(result)


@app.route("/attendance/camera/frame", methods=["GET"])
def camera_frame():
    """Return the latest annotated JPEG frame from the face-detection engine."""
    if not _FACE_ENGINE_OK or face_engine is None:
        return ("", 204)
    jpeg = face_engine.get_frame()
    if jpeg is None:
        return ("", 204)
    return Response(
        jpeg,
        mimetype="image/jpeg",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma":        "no-cache",
        },
    )


@app.route("/schedules/<sched_id>/toggle", methods=["PATCH"])
def toggle_schedule(sched_id):
    with schedules_lock:
        schedules = load_schedules()
        for s in schedules:
            if s["id"] == sched_id:
                s["enabled"] = not s.get("enabled", True)
                save_schedules(schedules)
                logger.info("Toggled schedule %s -> enabled=%s", sched_id, s["enabled"])
                return jsonify(s)
    return jsonify({"error": "Not found"}), 404

# ── Entry point ──────────────────────────────────────────

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)
    finally:
        scheduler.shutdown()
        for btn in buttons.values():
            btn.close()

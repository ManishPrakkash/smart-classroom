"""
slider_motor.py
───────────────
Dual-motor slider control for Raspberry Pi 5.
Runs while attendance camera scan is active.

Wiring (BCM pin numbers):
  Motor A:  IN1=15, IN2=17, ENA=10
  Motor B:  IN3=9,  IN4=11, ENB=8
  Limits:   LIMIT_A=7, LIMIT_B=0  (wired to GND, internal pull-up)

The slider moves forward until LIMIT_A fires → reverses.
Reverses until LIMIT_B fires → goes forward again.
Continues bouncing until stop() is called.
"""

from __future__ import annotations

import logging
import os
import time
from threading import Lock

logger = logging.getLogger("smart-switch")

# ── Lazy imports so dev machines (Mock GPIO) don't crash ─────────────────────
_USE_MOCK = os.getenv("USE_MOCK_GPIO", "0") == "1"

try:
    from gpiozero import DigitalOutputDevice, PWMOutputDevice, Button
    _GPIOZERO_OK = True
except ImportError:
    _GPIOZERO_OK = False
    logger.warning("[Slider] gpiozero not available – slider disabled")

# ── Pin numbers (BCM) ─────────────────────────────────────────────────────────
_PIN_IN1   = 15
_PIN_IN2   = 17
_PIN_ENA   = 10
_PIN_IN3   = 9
_PIN_IN4   = 11
_PIN_ENB   = 8
_PIN_LIM_A = 7
_PIN_LIM_B = 0

SPEED = 1.0          # 0.0 – 1.0  PWM duty cycle
COOLDOWN_S = 1.0     # seconds between limit-switch triggers (debounce)


class SliderMotor:
    """
    Thread-safe slider motor controller.
    Call start() when attendance scan begins, stop() when it ends.
    """

    def __init__(self):
        self._lock               = Lock()
        self._running            = False
        self._direction          = "forward"   # "forward" | "reverse"
        self._last_trigger_time  = 0.0

        # Hardware handles – created on first start() if not mock
        self._in1  = None
        self._in2  = None
        self._ena  = None
        self._in3  = None
        self._in4  = None
        self._enb  = None
        self._lim_a = None
        self._lim_b = None
        self._hw_ok  = False

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self) -> bool:
        """Start slider in current direction. Returns True if started."""
        with self._lock:
            if self._running:
                logger.info("[Slider] Already running")
                return True

            if not self._init_hardware():
                return False

            self._running = True
            self._direction = "forward"
            self._last_trigger_time = 0.0

        self._apply_direction()
        logger.info("[Slider] Started – direction: forward")
        return True

    def stop(self):
        """Stop slider immediately."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        self._motor_stop()
        logger.info("[Slider] Stopped")

    @property
    def running(self) -> bool:
        return self._running

    @property
    def direction(self) -> str:
        return self._direction

    # ── Hardware init ─────────────────────────────────────────────────────────

    def _init_hardware(self) -> bool:
        if self._hw_ok:
            return True

        if not _GPIOZERO_OK:
            logger.warning("[Slider] gpiozero unavailable – cannot init hardware")
            return False

        if _USE_MOCK:
            logger.warning("[Slider] Mock GPIO mode – slider will not move physically")
            self._hw_ok = True   # allow run in mock mode without crashing
            return True

        try:
            self._in1  = DigitalOutputDevice(_PIN_IN1)
            self._in2  = DigitalOutputDevice(_PIN_IN2)
            self._ena  = PWMOutputDevice(_PIN_ENA)
            self._in3  = DigitalOutputDevice(_PIN_IN3)
            self._in4  = DigitalOutputDevice(_PIN_IN4)
            self._enb  = PWMOutputDevice(_PIN_ENB)

            self._lim_a = Button(_PIN_LIM_A, pull_up=True, bounce_time=0.1)
            self._lim_b = Button(_PIN_LIM_B, pull_up=True, bounce_time=0.1)

            self._lim_a.when_pressed = self._on_limit_switch
            self._lim_b.when_pressed = self._on_limit_switch

            self._hw_ok = True
            logger.info("[Slider] Hardware initialized (pins: IN1=%d IN2=%d ENA=%d "
                        "IN3=%d IN4=%d ENB=%d LimA=%d LimB=%d)",
                        _PIN_IN1, _PIN_IN2, _PIN_ENA,
                        _PIN_IN3, _PIN_IN4, _PIN_ENB,
                        _PIN_LIM_A, _PIN_LIM_B)
            return True

        except Exception as exc:
            logger.error("[Slider] Hardware init failed: %s", exc)
            return False

    # ── Motor helpers ─────────────────────────────────────────────────────────

    def _motor_stop(self):
        if not self._hw_ok or _USE_MOCK:
            return
        try:
            if self._ena: self._ena.value = 0
            if self._enb: self._enb.value = 0
            if self._in1: self._in1.off()
            if self._in2: self._in2.off()
            if self._in3: self._in3.off()
            if self._in4: self._in4.off()
        except Exception as exc:
            logger.error("[Slider] motor_stop error: %s", exc)

    def _motor_forward(self):
        if not self._hw_ok or _USE_MOCK:
            return
        try:
            self._in1.on();  self._in2.off()   # Motor A forward
            self._in3.on();  self._in4.off()   # Motor B forward (same direction)
            self._ena.value = SPEED
            self._enb.value = SPEED
        except Exception as exc:
            logger.error("[Slider] motor_forward error: %s", exc)

    def _motor_reverse(self):
        if not self._hw_ok or _USE_MOCK:
            return
        try:
            self._in1.off(); self._in2.on()    # Motor A reverse
            self._in3.off(); self._in4.on()    # Motor B reverse (same direction)
            self._ena.value = SPEED
            self._enb.value = SPEED
        except Exception as exc:
            logger.error("[Slider] motor_reverse error: %s", exc)

    def _apply_direction(self):
        if self._direction == "forward":
            self._motor_forward()
        else:
            self._motor_reverse()

    # ── Limit switch callback ─────────────────────────────────────────────────

    def _on_limit_switch(self):
        """
        Called by gpiozero from its own thread when either limit switch is pressed.
        Reverses direction and resumes, with cooldown to prevent bounce retriggering.
        """
        now = time.time()

        with self._lock:
            if not self._running:
                return
            if (now - self._last_trigger_time) < COOLDOWN_S:
                return   # still within cooldown – ignore
            self._last_trigger_time = now
            # Flip direction
            self._direction = "reverse" if self._direction == "forward" else "forward"
            new_dir = self._direction

        # Brief stop before reversing (protects H-bridge driver)
        self._motor_stop()
        time.sleep(0.1)
        self._apply_direction()
        logger.info("[Slider] Limit hit → direction now: %s", new_dir)

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def close(self):
        """Release GPIO resources."""
        self.stop()
        for dev in (self._in1, self._in2, self._ena,
                    self._in3, self._in4, self._enb,
                    self._lim_a, self._lim_b):
            try:
                if dev is not None:
                    dev.close()
            except Exception:
                pass
        logger.info("[Slider] GPIO resources released")


# Singleton used by app.py
slider = SliderMotor()

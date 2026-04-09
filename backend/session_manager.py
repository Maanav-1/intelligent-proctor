"""
Session manager — owns the per-session state:
  HeadPoseEstimator, BehaviorAnalyzer, and the shared YOLO model reference.
"""

import time
import uuid
import base64
import cv2
import numpy as np
from ultralytics import YOLO

import sys, os
# Add project root so we can import the existing modules directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from head_pose import HeadPoseEstimator
from behavior_analyzer import BehaviorAnalyzer


class SessionManager:
    """Manages a single proctoring/deep-work session."""

    def __init__(self, vision_model: YOLO):
        self.vision_model = vision_model
        self.session_id: str | None = None
        self.analyzer: BehaviorAnalyzer | None = None
        self.pose_estimator: HeadPoseEstimator | None = None
        self.mode: str | None = None

        # Calibration
        self.calibrating = False
        self.calibration_start: float = 0.0
        self.calibration_duration: float = 3.0

        # Last report (persisted after session ends)
        self.last_report: dict | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start_session(self, mode: str) -> str:
        """Initialize a new session. Returns session_id."""
        self.session_id = uuid.uuid4().hex[:12]
        self.mode = mode.upper()
        self.analyzer = BehaviorAnalyzer()
        self.pose_estimator = None  # created on first frame (need dimensions)
        self.calibrating = True
        self.calibration_start = time.time()
        self.last_report = None
        return self.session_id

    def stop_session(self) -> dict:
        """End the session and return the JSON report."""
        if self.analyzer is None:
            return {"error": "No active session"}

        # If calibration never completed, the analyzer was never started
        if self.analyzer.session_start_time is None:
            report = {
                "mode": self.mode,
                "date": None,
                "duration_sec": 0,
                "total_frames": 0,
                "violation_events": dict(self.analyzer.violation_events),
                "violation_frames": dict(self.analyzer.violation_frames),
                "error": "Session ended before calibration completed",
            }
        else:
            report = self.analyzer.get_session_report_json()
            # Also save the text report to disk (keeps existing behavior)
            self.analyzer.save_report()

        self.last_report = report

        # Reset
        self.session_id = None
        self.mode = None
        self.calibrating = False
        return report

    @property
    def is_active(self) -> bool:
        return self.session_id is not None

    # ------------------------------------------------------------------
    # Frame processing
    # ------------------------------------------------------------------

    def process_frame(self, b64_jpeg: str) -> dict:
        """
        Decode a base64 JPEG frame, run the full CV pipeline,
        and return a metrics dict.
        """
        # Decode
        img_bytes = base64.b64decode(b64_jpeg)
        np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return {"type": "error", "message": "Could not decode frame"}

        h, w = frame.shape[:2]

        # Lazy-init the pose estimator with actual frame dimensions
        if self.pose_estimator is None:
            self.pose_estimator = HeadPoseEstimator(w, h)

        # --- Head pose ---
        face_detected, pitch, yaw, roll = self.pose_estimator.process_frame(frame)
        pitch_val = float(pitch[0]) if isinstance(pitch, np.ndarray) else float(pitch)
        yaw_val = float(yaw[0]) if isinstance(yaw, np.ndarray) else float(yaw)

        # --- Calibration phase ---
        if self.calibrating:
            elapsed = time.time() - self.calibration_start
            remaining = max(0.0, self.calibration_duration - elapsed)

            if face_detected:
                self.pose_estimator.calibrate(pitch_val, yaw_val)

            if elapsed >= self.calibration_duration:
                self.pose_estimator.finish_calibration()
                self.calibrating = False
                self.analyzer.start_session(self.mode)

            return {
                "type": "metrics",
                "calibrating": True,
                "calibration_remaining": round(remaining, 1),
                "face_detected": face_detected,
                "pitch": round(pitch_val, 1),
                "yaw": round(yaw_val, 1),
            }

        # --- YOLO object detection ---
        phone_detected, book_detected, people_count = False, False, 0
        results = self.vision_model(frame, verbose=False)[0]

        for box in results.boxes:
            cid = int(box.cls[0])
            conf = float(box.conf[0])
            if conf > 0.4:
                if cid == 4 or cid == 1:
                    people_count += 1
                if cid == 3:
                    phone_detected = True
                if cid == 0:
                    book_detected = True

        # --- Behavior classification ---
        current_state = self.analyzer.classify_state(
            pitch_val, yaw_val, face_detected,
            phone_detected, book_detected, people_count
        )

        # --- Build response ---
        metrics = {
            "type": "metrics",
            "calibrating": False,
            "state": current_state,
            "face_detected": face_detected,
            "pitch": round(pitch_val, 1),
            "yaw": round(yaw_val, 1),
            "violations": dict(self.analyzer.violation_events),
            "violation_frames": dict(self.analyzer.violation_frames),
        }

        if self.mode == "DEEP_WORK":
            focus_score = (
                (self.analyzer.focused_frames / self.analyzer.total_frames * 100)
                if self.analyzer.total_frames > 0
                else 0
            )
            metrics["focus_score"] = round(focus_score, 1)

        return metrics

import time
import os
from datetime import datetime

class BehaviorAnalyzer:
    def __init__(self):
        # Session Analytics Data
        self.session_start_time = None
        self.mode = None 
        self.violations = {"PHONE": 0, "BOOK": 0, "MULTIPLE_PEOPLE": 0, "LOOKING_AWAY": 0}
        self.total_frames = 0
        self.focused_frames = 0
        
        # Time-based tracking for looking away
        self.looking_away_start_time = None
        self.grace_period = 2.0
        self.already_flagged = False  # NEW: prevents re-flagging every frame

    def start_session(self, mode):
        self.mode = mode
        self.session_start_time = time.time()
        self.violations = {k: 0 for k in self.violations}
        self.total_frames = 0
        self.focused_frames = 0
        self.looking_away_start_time = None
        self.already_flagged = False
        print(f"--- Session Started: {self.mode} Mode ---")

    def classify_state(self, pitch, yaw, face_detected, phone_detected, book_detected, people_count):
        self.total_frames += 1
        state = "FOCUSED"
        
        if not face_detected:
            # Reset gaze timer when face is lost
            self.looking_away_start_time = None
            self.already_flagged = False
            return "USER_MISSING"

        # 1. Evaluate Head Pose with timer + single-flag logic
        is_looking_away = abs(yaw) > 25  # Only left/right head turn matters
        
        if is_looking_away:
            if self.looking_away_start_time is None:
                # Just started looking away — begin timer
                self.looking_away_start_time = time.time()
                state = "WARNING: GAZE DEVIATING..."
            elif not self.already_flagged and (time.time() - self.looking_away_start_time) > self.grace_period:
                # Timer exceeded AND we haven't flagged this event yet
                state = "VIOLATION: LOOKING_AWAY" if self.mode == "PROCTOR" else "DISTRACTED: GAZE_OFF"
                self.violations["LOOKING_AWAY"] += 1
                self.already_flagged = True  # Only count ONCE per look-away event
            elif self.already_flagged:
                # Still looking away after being flagged — show state but don't re-count
                state = "VIOLATION: LOOKING_AWAY" if self.mode == "PROCTOR" else "DISTRACTED: GAZE_OFF"
            else:
                # Within grace period
                state = "WARNING: GAZE DEVIATING..."
        else:
            # User looked back — reset everything for the next event
            self.looking_away_start_time = None
            self.already_flagged = False

        # 2. Hard Object Violations (Overrides head pose)
        if self.mode == "PROCTOR":
            if people_count > 1:
                state = "VIOLATION: MULTIPLE_PEOPLE"
                self.violations["MULTIPLE_PEOPLE"] += 1
            elif phone_detected:
                state = "VIOLATION: PHONE"
                self.violations["PHONE"] += 1
            elif book_detected:
                state = "VIOLATION: BOOK"
                self.violations["BOOK"] += 1
        else: 
            if phone_detected:
                state = "DISTRACTED: PHONE"
                self.violations["PHONE"] += 1
            elif state == "FOCUSED":
                self.focused_frames += 1

        return state

    def get_session_report(self):
        duration_sec = int(time.time() - self.session_start_time)
        mins, secs = divmod(duration_sec, 60)
        
        report = f"==========================================\n"
        report += f"         {self.mode} SESSION REPORT       \n"
        report += f"==========================================\n"
        report += f"User: Maanav Chellani\n"
        report += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total Duration: {mins} minutes, {secs} seconds\n"
        report += f"------------------------------------------\n"

        if self.mode == "DEEP_WORK":
            focus_score = (self.focused_frames / self.total_frames) * 100 if self.total_frames > 0 else 0
            report += f"Overall Productivity Score: {focus_score:.1f}%\n\n"
            report += f"Distraction Breakdown (measured in frames):\n"
            report += f" - Phone Usage: {self.violations['PHONE']} times\n"
            report += f" - Gaze/Attention Loss: {self.violations['LOOKING_AWAY']} times\n"
        else:
            report += "Academic Integrity Summary:\n"
            total_violations = sum(self.violations.values())
            report += f"Total Infractions Flagged: {total_violations}\n\n"
            for v_type, count in self.violations.items():
                report += f" - {v_type}: {count} violation frames\n"
        
        report += f"==========================================\n"
        return report

    def save_report(self):
        if not os.path.exists("session_reports"):
            os.makedirs("session_reports")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"session_reports/{self.mode}_Report_{timestamp}.txt"
        with open(filename, "w") as f:
            f.write(self.get_session_report())
        print(f"\n[+] Session Report successfully saved to: {filename}")
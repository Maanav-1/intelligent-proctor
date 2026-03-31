import time
import os
from datetime import datetime

class BehaviorAnalyzer:
    def __init__(self):
        # Session Analytics Data
        self.session_start_time = None
        self.mode = None 
        self.total_frames = 0
        self.focused_frames = 0
        
        # Violation tracking: frames (every frame it's detected) + events (distinct occurrences)
        self.violation_frames = {"PHONE": 0, "BOOK": 0, "MULTIPLE_PEOPLE": 0, "LOOKING_AWAY": 0}
        self.violation_events = {"PHONE": 0, "BOOK": 0, "MULTIPLE_PEOPLE": 0, "LOOKING_AWAY": 0}
        
        # State tracking for detecting NEW events (was it happening last frame?)
        self.prev_phone = False
        self.prev_book = False
        self.prev_multiple_people = False
        
        # Time-based tracking for looking away
        self.looking_away_start_time = None
        self.grace_period = 2.0
        self.already_flagged = False

    def start_session(self, mode):
        self.mode = mode
        self.session_start_time = time.time()
        self.violation_frames = {k: 0 for k in self.violation_frames}
        self.violation_events = {k: 0 for k in self.violation_events}
        self.total_frames = 0
        self.focused_frames = 0
        self.looking_away_start_time = None
        self.already_flagged = False
        self.prev_phone = False
        self.prev_book = False
        self.prev_multiple_people = False
        print(f"--- Session Started: {self.mode} Mode ---")

    def classify_state(self, pitch, yaw, face_detected, phone_detected, book_detected, people_count):
        self.total_frames += 1
        state = "FOCUSED"
        
        if not face_detected:
            self.looking_away_start_time = None
            self.already_flagged = False
            self._reset_object_states()
            return "USER_MISSING"

        # 1. Evaluate Head Pose with timer + single-flag logic
        is_looking_away = abs(yaw) > 25

        if is_looking_away:
            if self.looking_away_start_time is None:
                self.looking_away_start_time = time.time()
                state = "WARNING: GAZE DEVIATING..."
            elif not self.already_flagged and (time.time() - self.looking_away_start_time) > self.grace_period:
                state = "VIOLATION: LOOKING_AWAY" if self.mode == "PROCTOR" else "DISTRACTED: GAZE_OFF"
                self.violation_frames["LOOKING_AWAY"] += 1
                self.violation_events["LOOKING_AWAY"] += 1
                self.already_flagged = True
            elif self.already_flagged:
                state = "VIOLATION: LOOKING_AWAY" if self.mode == "PROCTOR" else "DISTRACTED: GAZE_OFF"
                self.violation_frames["LOOKING_AWAY"] += 1  # Keep counting frames
            else:
                state = "WARNING: GAZE DEVIATING..."
        else:
            self.looking_away_start_time = None
            self.already_flagged = False

        # 2. Hard Object Violations
        if self.mode == "PROCTOR":
            if people_count > 1:
                state = "VIOLATION: MULTIPLE_PEOPLE"
                self.violation_frames["MULTIPLE_PEOPLE"] += 1
                if not self.prev_multiple_people:
                    self.violation_events["MULTIPLE_PEOPLE"] += 1
                self.prev_multiple_people = True
            else:
                self.prev_multiple_people = False

            if phone_detected:
                state = "VIOLATION: PHONE"
                self.violation_frames["PHONE"] += 1
                if not self.prev_phone:
                    self.violation_events["PHONE"] += 1
                self.prev_phone = True
            else:
                self.prev_phone = False

            if book_detected:
                state = "VIOLATION: BOOK"
                self.violation_frames["BOOK"] += 1
                if not self.prev_book:
                    self.violation_events["BOOK"] += 1
                self.prev_book = True
            else:
                self.prev_book = False

        else:  # DEEP_WORK mode — only phone matters
            if phone_detected:
                state = "DISTRACTED: PHONE"
                self.violation_frames["PHONE"] += 1
                if not self.prev_phone:
                    self.violation_events["PHONE"] += 1
                self.prev_phone = True
            else:
                self.prev_phone = False

            if state == "FOCUSED":
                self.focused_frames += 1

        return state

    def _reset_object_states(self):
        self.prev_phone = False
        self.prev_book = False
        self.prev_multiple_people = False

    def get_session_report(self):
        duration_sec = int(time.time() - self.session_start_time)
        mins, secs = divmod(duration_sec, 60)
        
        report = f"==========================================\n"
        report += f"         {self.mode} SESSION REPORT       \n"
        report += f"==========================================\n"
        report += f"User: Maanav Chellani\n"
        report += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total Duration: {mins} minutes, {secs} seconds\n"
        report += f"Total Frames Processed: {self.total_frames}\n"
        report += f"------------------------------------------\n"

        if self.mode == "DEEP_WORK":
            focus_score = (self.focused_frames / self.total_frames) * 100 if self.total_frames > 0 else 0
            report += f"Overall Productivity Score: {focus_score:.1f}%\n\n"
            report += f"Distraction Breakdown:\n"
            report += f" - Phone Usage: {self.violation_events['PHONE']} time(s) detected across {self.violation_frames['PHONE']} frames\n"
            report += f" - Gaze/Attention Loss: {self.violation_events['LOOKING_AWAY']} time(s) detected across {self.violation_frames['LOOKING_AWAY']} frames\n"
        else:
            total_events = sum(self.violation_events.values())
            report += f"Academic Integrity Summary:\n"
            report += f"Total Infractions Flagged: {total_events}\n\n"
            report += f"Violation Breakdown:\n"
            report += f" - PHONE: {self.violation_events['PHONE']} time(s) detected across {self.violation_frames['PHONE']} frames\n"
            report += f" - BOOK: {self.violation_events['BOOK']} time(s) detected across {self.violation_frames['BOOK']} frames\n"
            report += f" - MULTIPLE_PEOPLE: {self.violation_events['MULTIPLE_PEOPLE']} time(s) detected across {self.violation_frames['MULTIPLE_PEOPLE']} frames\n"
            report += f" - LOOKING_AWAY: {self.violation_events['LOOKING_AWAY']} time(s) detected across {self.violation_frames['LOOKING_AWAY']} frames\n"
        
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
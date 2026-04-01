import time
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

class BehaviorAnalyzer:
    def __init__(self):
        # Session Analytics Data
        self.session_start_time = None
        self.mode = None 
        self.total_frames = 0
        self.focused_frames = 0
        
        # Violation tracking: frames + events
        self.violation_frames = {"PHONE": 0, "BOOK": 0, "MULTIPLE_PEOPLE": 0, "LOOKING_AWAY": 0}
        self.violation_events = {"PHONE": 0, "BOOK": 0, "MULTIPLE_PEOPLE": 0, "LOOKING_AWAY": 0}
        
        # State tracking for event detection
        self.prev_phone = False
        self.prev_book = False
        self.prev_multiple_people = False
        
        # Gaze tracking
        self.looking_away_start_time = None
        self.grace_period = 2.0
        self.already_flagged = False

        # ---- Deep Work: Time-series tracking ----
        self.time_series = []
        self.last_snapshot_time = None
        self.snapshot_interval = 1.0
        self.window_focused = 0
        self.window_total = 0
        self.window_phone = False
        self.window_gaze_off = False

        # Streak tracking
        self.current_focus_streak = 0.0
        self.current_distraction_streak = 0.0
        self.longest_focus_streak = 0.0
        self.longest_distraction_streak = 0.0
        self.last_state_was_focused = True
        self._streak_start = None

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

        self.time_series = []
        self.last_snapshot_time = time.time()
        self.window_focused = 0
        self.window_total = 0
        self.window_phone = False
        self.window_gaze_off = False

        self.current_focus_streak = 0.0
        self.current_distraction_streak = 0.0
        self.longest_focus_streak = 0.0
        self.longest_distraction_streak = 0.0
        self.last_state_was_focused = True
        self._streak_start = time.time()

        print(f"--- Session Started: {self.mode} Mode ---")

    def classify_state(self, pitch, yaw, face_detected, phone_detected, book_detected, people_count):
        self.total_frames += 1
        state = "FOCUSED"
        
        if not face_detected:
            self.looking_away_start_time = None
            self.already_flagged = False
            self._reset_object_states()
            if self.mode == "DEEP_WORK":
                self._update_time_series(False, False, False)
                self._update_streaks(False)
            return "USER_MISSING"

        # 1. Evaluate Head Pose
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
                self.violation_frames["LOOKING_AWAY"] += 1
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

        else:  # DEEP_WORK
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

        # Deep Work: time-series + streaks
        if self.mode == "DEEP_WORK":
            is_focused = (state == "FOCUSED")
            is_phone = phone_detected
            is_gaze_off = "LOOKING_AWAY" in state or "GAZE_OFF" in state
            self._update_time_series(is_focused, is_phone, is_gaze_off)
            self._update_streaks(is_focused)

        return state

    def _reset_object_states(self):
        self.prev_phone = False
        self.prev_book = False
        self.prev_multiple_people = False

    def _update_time_series(self, is_focused, is_phone, is_gaze_off):
        self.window_total += 1
        if is_focused:
            self.window_focused += 1
        if is_phone:
            self.window_phone = True
        if is_gaze_off:
            self.window_gaze_off = True

        now = time.time()
        if (now - self.last_snapshot_time) >= self.snapshot_interval:
            elapsed = round(now - self.session_start_time, 1)
            focus_pct = (self.window_focused / self.window_total * 100) if self.window_total > 0 else 0

            self.time_series.append({
                "elapsed_sec": elapsed,
                "focus_pct": round(focus_pct, 1),
                "phone_detected": self.window_phone,
                "gaze_off": self.window_gaze_off
            })

            self.window_focused = 0
            self.window_total = 0
            self.window_phone = False
            self.window_gaze_off = False
            self.last_snapshot_time = now

    def _update_streaks(self, is_focused):
        now = time.time()
        
        if is_focused:
            if self.last_state_was_focused:
                self.current_focus_streak = now - self._streak_start
            else:
                if self.current_distraction_streak > self.longest_distraction_streak:
                    self.longest_distraction_streak = self.current_distraction_streak
                self._streak_start = now
                self.current_focus_streak = 0
                self.current_distraction_streak = 0
                self.last_state_was_focused = True
        else:
            if not self.last_state_was_focused:
                self.current_distraction_streak = now - self._streak_start
            else:
                if self.current_focus_streak > self.longest_focus_streak:
                    self.longest_focus_streak = self.current_focus_streak
                self._streak_start = now
                self.current_distraction_streak = 0
                self.current_focus_streak = 0
                self.last_state_was_focused = False

        if is_focused and self.current_focus_streak > self.longest_focus_streak:
            self.longest_focus_streak = self.current_focus_streak
        if not is_focused and self.current_distraction_streak > self.longest_distraction_streak:
            self.longest_distraction_streak = self.current_distraction_streak

    def _format_duration(self, seconds):
        mins, secs = divmod(int(seconds), 60)
        if mins > 0:
            return f"{mins}m {secs}s"
        return f"{secs}s"

    def get_session_report(self):
        duration_sec = int(time.time() - self.session_start_time)
        mins, secs = divmod(duration_sec, 60)
        
        report = f"==========================================\n"
        report += f"         {self.mode} SESSION REPORT       \n"
        report += f"==========================================\n"
        report += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total Duration: {mins} minutes, {secs} seconds\n"
        report += f"Total Frames Processed: {self.total_frames}\n"
        report += f"------------------------------------------\n"

        if self.mode == "DEEP_WORK":
            focus_score = (self.focused_frames / self.total_frames) * 100 if self.total_frames > 0 else 0
            report += f"Overall Productivity Score: {focus_score:.1f}%\n\n"
            
            report += f"Streaks:\n"
            report += f" - Longest Focus Streak: {self._format_duration(self.longest_focus_streak)}\n"
            report += f" - Longest Distraction Streak: {self._format_duration(self.longest_distraction_streak)}\n\n"

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
        
        # Save text report
        txt_filename = f"session_reports/{self.mode}_Report_{timestamp}.txt"
        with open(txt_filename, "w") as f:
            f.write(self.get_session_report())
        print(f"\n[+] Session Report saved to: {txt_filename}")

        # Deep Work: generate focus graph
        if self.mode == "DEEP_WORK" and len(self.time_series) >= 2:
            graph_filename = f"session_reports/DEEP_WORK_Graph_{timestamp}.png"
            self._generate_graph(graph_filename)
            print(f"[+] Focus Graph saved to: {graph_filename}")

    def _generate_graph(self, filename):
        focus = [p["focus_pct"] for p in self.time_series]
        phone_indices = [i for i, p in enumerate(self.time_series) if p["phone_detected"]]
        gaze_indices = [i for i, p in enumerate(self.time_series) if p["gaze_off"]]

        total_sec = len(focus)
        use_minutes = total_sec > 120  # Switch to minutes if session > 2 min

        if use_minutes:
            x = [i / 60 for i in range(total_sec)]
            phone_x = [i / 60 for i in phone_indices]
            gaze_x = [i / 60 for i in gaze_indices]
            x_label = "Time (minutes)"
        else:
            x = list(range(total_sec))
            phone_x = phone_indices
            gaze_x = gaze_indices
            x_label = "Time (seconds)"

        fig, ax = plt.subplots(figsize=(12, 5))
        
        ax.plot(x, focus, color='#4CAF50', linewidth=2, label='Focus %')
        ax.fill_between(x, focus, alpha=0.15, color='#4CAF50')

        if phone_x:
            ax.scatter(phone_x, [0] * len(phone_x), color='red', marker='^', 
                       s=60, label='Phone Detected', zorder=5)
        if gaze_x:
            ax.scatter(gaze_x, [0] * len(gaze_x), color='orange', marker='v', 
                       s=60, label='Gaze Off', zorder=5)

        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel("Focus %", fontsize=12)
        ax.set_title("Deep Work Session — Focus Over Time", fontsize=14, fontweight='bold')
        ax.set_ylim(-5, 105)
        ax.axhline(y=50, color='gray', linestyle='--', alpha=0.4, label='50% threshold')
        ax.legend(loc='lower left')
        ax.grid(True, alpha=0.3)

        overall = (self.focused_frames / self.total_frames * 100) if self.total_frames > 0 else 0
        summary = f"Overall: {overall:.1f}%  |  Best Streak: {self._format_duration(self.longest_focus_streak)}  |  Phone: {self.violation_events['PHONE']}x  |  Gaze Off: {self.violation_events['LOOKING_AWAY']}x"
        fig.text(0.5, 0.01, summary, ha='center', fontsize=10, style='italic', color='gray')

        plt.tight_layout()
        plt.subplots_adjust(bottom=0.12)
        plt.savefig(filename, dpi=150)
        plt.close()
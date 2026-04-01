import cv2
import time
import numpy as np
from ultralytics import YOLO
from head_pose import HeadPoseEstimator
from behavior_analyzer import BehaviorAnalyzer

def main():
    print("Select Mode: (1) Proctor Mode | (2) Deep Work Mode")
    choice = input("Enter 1 or 2: ")
    mode = "PROCTOR" if choice == '1' else "DEEP_WORK"

    cap = cv2.VideoCapture(0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    pose_estimator = HeadPoseEstimator(width, height)
    analyzer = BehaviorAnalyzer()
    
    print("Loading Custom Vision Model (best.pt)...")
    vision_model = YOLO("best.pt") 

    # ========== CALIBRATION PHASE (3 seconds) ==========
    print("\n[*] CALIBRATION: Look straight at the screen for 3 seconds...")
    cal_start = time.time()
    cal_duration = 3.0

    while cap.isOpened() and (time.time() - cal_start) < cal_duration:
        ret, frame = cap.read()
        if not ret:
            break

        face_detected, pitch, yaw, roll = pose_estimator.process_frame(frame)
        
        # Extract scalars
        pitch_val = float(pitch[0]) if isinstance(pitch, np.ndarray) else float(pitch)
        yaw_val = float(yaw[0]) if isinstance(yaw, np.ndarray) else float(yaw)

        if face_detected:
            pose_estimator.calibrate(pitch_val, yaw_val)

        # Show calibration countdown on screen
        remaining = cal_duration - (time.time() - cal_start)
        cv2.putText(frame, "CALIBRATING: Look at the screen", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f"Starting in {remaining:.1f}s...", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"Raw Pitch: {pitch_val:.1f}  Raw Yaw: {yaw_val:.1f}", (20, height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.imshow("Intelligent Monitor", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            cap.release()
            cv2.destroyAllWindows()
            return

    pose_estimator.finish_calibration()
    # ===================================================

    analyzer.start_session(mode)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 1. Process Head Pose (now returns calibrated values)
        face_detected, pitch, yaw, roll = pose_estimator.process_frame(frame)
        
        pitch_val = float(pitch[0]) if isinstance(pitch, np.ndarray) else float(pitch)
        yaw_val = float(yaw[0]) if isinstance(yaw, np.ndarray) else float(yaw)

        # 2. Process YOLO Vision
        phone_detected, book_detected, people_count = False, False, 0
        results = vision_model(frame, verbose=False)[0]
        
        for box in results.boxes:
            cid = int(box.cls[0])
            conf = float(box.conf[0])
            if conf > 0.4:
                if cid == 4 or cid == 1: people_count += 1 
                if cid == 3: phone_detected = True 
                if cid == 0: book_detected = True 

        # 3. Classify Behavior
        current_state = analyzer.classify_state(pitch_val, yaw_val, face_detected, phone_detected, book_detected, people_count)
        
        # 4. Render UI
        color = (0, 255, 0) if "FOCUSED" in current_state else (0, 165, 255) if "WARNING" in current_state else (0, 0, 255)
        cv2.putText(frame, f"STATE: {current_state}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        y_offset = 80
        if mode == "PROCTOR":
            cv2.putText(frame, "LIVE VIOLATION TALLY:", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            for v_type in ["PHONE", "BOOK", "MULTIPLE_PEOPLE", "LOOKING_AWAY"]:
                events = analyzer.violation_events[v_type]
                if events > 0:
                    y_offset += 30
                    cv2.putText(frame, f"{v_type}: {events} time(s)", (30, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        else:
            focus_score = (analyzer.focused_frames / analyzer.total_frames * 100) if analyzer.total_frames > 0 else 0
            cv2.putText(frame, f"LIVE FOCUS SCORE: {focus_score:.1f}%", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            y_offset += 30
            cv2.putText(frame, f"Distractions (Phone): {analyzer.violation_events['PHONE']} time(s)", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            y_offset += 30
            cv2.putText(frame, f"Distractions (Gaze Off): {analyzer.violation_events['LOOKING_AWAY']} time(s)", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # Debug: show calibrated pitch/yaw so you can verify
        cv2.putText(frame, f"Pitch: {pitch_val:.1f}  Yaw: {yaw_val:.1f}", (20, height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("Intelligent Monitor", frame)
        # Exit on ESC key OR clicking the X button on the window
        if cv2.waitKey(1) & 0xFF == 27:
            break
        if cv2.getWindowProperty("Intelligent Monitor", cv2.WND_PROP_VISIBLE) < 1:
            break

    print(analyzer.get_session_report())
    analyzer.save_report()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
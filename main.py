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

    # Start the session immediately (No 10s calibration)
    analyzer.start_session(mode)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # 1. Process Head Pose
        face_detected, pitch, yaw, roll = pose_estimator.process_frame(frame)
        
        # Ensure values are single floats, not arrays
        pitch_val = pitch[0] if isinstance(pitch, np.ndarray) else pitch
        yaw_val = yaw[0] if isinstance(yaw, np.ndarray) else yaw

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
            for v_type, count in analyzer.violations.items():
                if count > 0:
                    y_offset += 30
                    cv2.putText(frame, f"{v_type}: {count}", (30, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        else:
            focus_score = (analyzer.focused_frames / analyzer.total_frames * 100) if analyzer.total_frames > 0 else 0
            cv2.putText(frame, f"LIVE FOCUS SCORE: {focus_score:.1f}%", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            y_offset += 30
            cv2.putText(frame, f"Distractions (Phone): {analyzer.violations['PHONE']}", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            y_offset += 30
            cv2.putText(frame, f"Distractions (Gaze Off): {analyzer.violations['LOOKING_AWAY']}", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        cv2.imshow("Intelligent Monitor", frame)
        if cv2.waitKey(1) & 0xFF == 27: # ESC to quit
            break

    # Save and Print Report
    print(analyzer.get_session_report())
    analyzer.save_report()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
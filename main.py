import cv2
import time
import numpy as np
from ultralytics import YOLO
from head_pose import HeadPoseEstimator
from behavior_analyzer import BehaviorAnalyzer

def main():
    cap = cv2.VideoCapture(0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Initialize Core Components
    pose_estimator = HeadPoseEstimator(width, height)
    behavior_analyzer = BehaviorAnalyzer()
    
    # Load YOLOv8 (Currently using the nano model. Once you train your custom model on Colab, 
    # change 'yolov8n.pt' to 'best.pt')
    print("Loading Vision Model...")
    vision_model = YOLO("yolov8n.pt") 

    # Calibration Variables
    calibration_duration = 10 # seconds
    calibration_data = []
    start_time = time.time()
    calibrating = True

    print("Starting Intelligent Proctor & Productivity Monitor...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # 1. Vision & Pose Extraction
        face_detected, pitch, yaw, roll, left_ear, right_ear = pose_estimator.process_frame(frame)
        current_features = [pitch[0] if isinstance(pitch, np.ndarray) else pitch, 
                            yaw[0] if isinstance(yaw, np.ndarray) else yaw, 
                            left_ear, right_ear]

        phone_detected = False
        people_count = 0

        # Run YOLO inference
        results = vision_model(frame, verbose=False)[0]
        for box in results.boxes:
            class_id = int(box.cls[0])
            # Default YOLO classes: 0 is person, 67 is cell phone
            if class_id == 0: people_count += 1
            if class_id == 67: phone_detected = True

        # 2. Calibration Phase Logic
        if calibrating:
            elapsed_time = time.time() - start_time
            remaining_time = int(calibration_duration - elapsed_time)
            
            cv2.putText(frame, f"CALIBRATION PHASE: Stare at screen", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"Time remaining: {remaining_time}s", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            if face_detected:
                calibration_data.append(current_features)
                
            if elapsed_time > calibration_duration:
                behavior_analyzer.calibrate(calibration_data)
                calibrating = False

        # 3. Active Monitoring Logic
        else:
            current_state = behavior_analyzer.classify_state(current_features, face_detected, phone_detected, people_count)
            
            # UI Rendering
            color = (0, 255, 0) if current_state == "FOCUSED" else (0, 0, 255)
            cv2.putText(frame, f"State: {current_state}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            if face_detected:
                cv2.putText(frame, f"EAR: {(left_ear+right_ear)/2:.2f} | Yaw: {current_features[1]:.1f}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Monitor Dashboard", frame)
        if cv2.waitKey(1) & 0xFF == 27: # ESC to quit
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
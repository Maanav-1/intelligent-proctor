import cv2
from head_pose import HeadPoseEstimator
from attention_model import TemporalAttentionModel
from behavior_analyzer import BehaviorAnalyzer

def main():
    cap = cv2.VideoCapture(0)
    
    # Initialize components based on dynamic camera resolution
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    pose_estimator = HeadPoseEstimator(width, height)
    attention_model = TemporalAttentionModel(window_size=45)
    behavior_analyzer = BehaviorAnalyzer()

    print("Starting Intelligent Proctor & Productivity Monitor...")
    print("Press 'ESC' to exit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 1. Computer Vision Pipeline
        face_detected, pitch, yaw, roll = pose_estimator.process_frame(frame)
        
        # Placeholder variables for upcoming YOLOv8 integration
        phone_detected = False 
        people_count = 1 if face_detected else 0 

        # 2. Temporal Analytics & Smoothing
        if face_detected:
            attention_model.update(yaw, pitch, phone_detected)
        else:
            attention_model.attention_window.append(0.0)

        smoothed_score = attention_model.get_smoothed_score()

        # 3. Behavioral Modeling
        current_state = behavior_analyzer.classify_state(
            smoothed_score, face_detected, phone_detected, people_count
        )

        # 4. User Interface Rendering
        color = (0, 255, 0) if current_state == "FOCUSED" else (0, 0, 255)
        cv2.putText(frame, f"State: {current_state}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, f"Focus Score: {smoothed_score:.2f}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        if face_detected:
            cv2.putText(frame, f"Yaw: {yaw[0]:.1f} | Pitch: {pitch[0]:.1f}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Monitor Dashboard", frame)

        if cv2.waitKey(1) & 0xFF == 27: # ESC to quit
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
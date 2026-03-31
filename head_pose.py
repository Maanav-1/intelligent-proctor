import cv2
import mediapipe as mp
import numpy as np

class HeadPoseEstimator:
    def __init__(self, image_width, image_height):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1, 
            refine_landmarks=True, 
            min_detection_confidence=0.5
        )
        
        self.camera_matrix = np.array([
            [image_width, 0, image_width / 2],
            [0, image_width, image_height / 2],
            [0, 0, 1]
        ], dtype="double")
        self.dist_coeffs = np.zeros((4, 1))

        self.model_points_3d = np.array([
            (0.0, 0.0, 0.0),             
            (0.0, -330.0, -65.0),        
            (-225.0, 170.0, -135.0),     
            (225.0, 170.0, -135.0),      
            (-150.0, -150.0, -125.0),    
            (150.0, -150.0, -125.0)      
        ], dtype=np.float64)

        # Calibration state
        self.calibrated = False
        self.calibration_pitches = []
        self.calibration_yaws = []
        self.baseline_pitch = 0.0
        self.baseline_yaw = 0.0

    def calibrate(self, pitch, yaw):
        """Collect samples during calibration phase."""
        self.calibration_pitches.append(pitch)
        self.calibration_yaws.append(yaw)

    def finish_calibration(self):
        """Lock in the baseline from collected samples."""
        if len(self.calibration_pitches) > 0:
            self.baseline_pitch = np.median(self.calibration_pitches)
            self.baseline_yaw = np.median(self.calibration_yaws)
        self.calibrated = True
        print(f"[✓] Calibration complete — Baseline Pitch: {self.baseline_pitch:.1f}, Yaw: {self.baseline_yaw:.1f}")

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        h, w, _ = frame.shape
        pitch, yaw, roll = 0.0, 0.0, 0.0
        face_detected = False

        if results.multi_face_landmarks:
            for face in results.multi_face_landmarks:
                face_detected = True
                
                points_2d = np.array([
                    (face.landmark[1].x * w, face.landmark[1].y * h),       
                    (face.landmark[152].x * w, face.landmark[152].y * h),   
                    (face.landmark[226].x * w, face.landmark[226].y * h),   
                    (face.landmark[446].x * w, face.landmark[446].y * h),   
                    (face.landmark[57].x * w, face.landmark[57].y * h),     
                    (face.landmark[287].x * w, face.landmark[287].y * h)    
                ], dtype="double")

                success, rotation_vector, translation_vector = cv2.solvePnP(
                    self.model_points_3d, points_2d, self.camera_matrix, self.dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
                )

                if success:
                    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
                    proj_matrix = np.hstack((rotation_matrix, translation_vector))
                    euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)[6]
                    raw_pitch, raw_yaw, roll = euler_angles.flatten()

                    # Extract scalar values
                    raw_pitch = float(raw_pitch[0]) if isinstance(raw_pitch, np.ndarray) else float(raw_pitch)
                    raw_yaw = float(raw_yaw[0]) if isinstance(raw_yaw, np.ndarray) else float(raw_yaw)

                    # Subtract baseline so "looking straight" → ~0
                    pitch = raw_pitch - self.baseline_pitch
                    yaw = raw_yaw - self.baseline_yaw

        return face_detected, pitch, yaw, roll
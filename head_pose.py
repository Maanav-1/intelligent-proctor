import cv2
import mediapipe as mp
import numpy as np
import math

class HeadPoseEstimator:
    def __init__(self, image_width, image_height):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1, 
            refine_landmarks=True, 
            min_detection_confidence=0.5
        )
        
        self.focal_length = image_width
        self.center = (image_width / 2, image_height / 2)
        self.camera_matrix = np.array([
            [self.focal_length, 0, self.center[0]],
            [0, self.focal_length, self.center[1]],
            [0, 0, 1]
        ], dtype="double")
        self.dist_coeffs = np.zeros((4, 1))

        # 3D generic facial model coordinates
        self.model_points_3d = np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (0.0, -330.0, -65.0),        # Chin
            (-225.0, 170.0, -135.0),     # Left eye left corner
            (225.0, 170.0, -135.0),      # Right eye right corner
            (-150.0, -150.0, -125.0),    # Left mouth corner
            (150.0, -150.0, -125.0)      # Right mouth corner
        ], dtype=np.float64)

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        h, w, _ = frame.shape
        pitch, yaw, roll = 0.0, 0.0, 0.0
        landmarks_extracted = False

        if results.multi_face_landmarks:
            for face in results.multi_face_landmarks:
                landmarks_extracted = True
                
                # Extract specific 2D points for PnP calculation
                points_2d = np.array([
                    (face.landmark[1].x * w, face.landmark[1].y * h),       # Nose
                    (face.landmark[152].x * w, face.landmark[152].y * h),   # Chin
                    (face.landmark[226].x * w, face.landmark[226].y * h),   # Left eye
                    (face.landmark[446].x * w, face.landmark[446].y * h),   # Right eye
                    (face.landmark[57].x * w, face.landmark[57].y * h),     # Left mouth
                    (face.landmark[287].x * w, face.landmark[287].y * h)    # Right mouth
                ], dtype="double")

                success, rotation_vector, translation_vector = cv2.solvePnP(
                    self.model_points_3d, points_2d, self.camera_matrix, self.dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
                )

                if success:
                    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
                    proj_matrix = np.hstack((rotation_matrix, translation_vector))
                    euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)[6]
                    
                    pitch, yaw, roll = [math.degrees(_) for _ in euler_angles]

        return landmarks_extracted, pitch, yaw, roll
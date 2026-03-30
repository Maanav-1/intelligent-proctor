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

    def _calculate_ear(self, landmarks, eye_indices, w, h):
        # Calculate Euclidean distance between vertical and horizontal eye landmarks
        def dist(p1, p2):
            return math.hypot((landmarks[p1].x - landmarks[p2].x) * w, 
                              (landmarks[p1].y - landmarks[p2].y) * h)
        
        # indices: [left/right, top, bottom, top, bottom]
        horizontal = dist(eye_indices[0], eye_indices[1])
        vertical_1 = dist(eye_indices[2], eye_indices[3])
        vertical_2 = dist(eye_indices[4], eye_indices[5])
        
        if horizontal == 0:
            return 0
        return (vertical_1 + vertical_2) / (2.0 * horizontal)

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        h, w, _ = frame.shape
        pitch, yaw, roll, left_ear, right_ear = 0.0, 0.0, 0.0, 0.0, 0.0
        landmarks_extracted = False

        if results.multi_face_landmarks:
            for face in results.multi_face_landmarks:
                landmarks_extracted = True
                
                # 1. EAR Calculation
                # Left eye indices: horizontal(33, 133), vertical(160, 144), (158, 153)
                left_ear = self._calculate_ear(face.landmark, [33, 133, 160, 144, 158, 153], w, h)
                # Right eye indices: horizontal(362, 263), vertical(385, 380), (387, 373)
                right_ear = self._calculate_ear(face.landmark, [362, 263, 385, 380, 387, 373], w, h)

                # 2. PnP Head Pose
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
                    pitch, yaw, roll = [math.degrees(_) for _ in euler_angles]

        return landmarks_extracted, pitch, yaw, roll, left_ear, right_ear
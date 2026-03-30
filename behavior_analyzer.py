from sklearn.ensemble import IsolationForest
import numpy as np

class BehaviorAnalyzer:
    def __init__(self):
        # The Isolation Forest will learn what is "Normal" for this specific user
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.is_calibrated = False

    def calibrate(self, calibration_data):
        """
        Takes a list of features collected during the 10-second calibration phase
        and trains the anomaly detector instantly.
        """
        if len(calibration_data) > 50: # Ensure we have enough frames
            X = np.array(calibration_data)
            self.anomaly_detector.fit(X)
            self.is_calibrated = True
            print("Model successfully calibrated to user's baseline.")
        else:
            print("Not enough data to calibrate.")

    def classify_state(self, features, face_detected, phone_detected, people_count):
        if not face_detected:
            return "USER_MISSING"
        
        # 1. Proctor Mode: Hard violations
        if people_count > 1:
            return "ACADEMIC_INTEGRITY_FLAG: MULTIPLE_PERSONS"
        if phone_detected:
            return "UNAUTHORIZED_OBJECT"

        # 2. Deep Work Mode: Behavioral Anomalies
        if self.is_calibrated:
            # Reshape features for sklearn: [pitch, yaw, left_ear, right_ear]
            X_live = np.array(features).reshape(1, -1)
            
            # predict() returns 1 for normal, -1 for anomaly
            prediction = self.anomaly_detector.predict(X_live)[0]
            
            if prediction == -1:
                return "DISTRACTED"
            return "FOCUSED"
        
        return "CALIBRATING..."
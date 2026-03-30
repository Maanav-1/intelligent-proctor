from collections import deque
import numpy as np

class TemporalAttentionModel:
    def __init__(self, window_size=30):
        # 30 frames window to smooth out quick blinks or rapid head movements
        self.attention_window = deque(maxlen=window_size)

    def update(self, yaw, pitch, phone_detected=False):
        score = 1.0

        # Penalize for spatial gaze deviations
        if abs(yaw) > 25.0 or abs(pitch) > 20.0:
            score -= 0.5

        # Heavy penalty for unauthorized objects
        if phone_detected:
            score -= 0.8

        score = max(0.0, score)
        self.attention_window.append(score)

    def get_smoothed_score(self):
        if not self.attention_window:
            return 1.0
        return np.mean(self.attention_window)
    

class BehaviorAnalyzer:
    def __init__(self, attention_threshold=0.6):
        self.attention_threshold = attention_threshold

    def classify_state(self, smoothed_score, face_detected, phone_detected, people_count):
        if not face_detected:
            return "USER_MISSING"
        
        # Proctor Mode logic for academic integrity
        if people_count > 1:
            return "ACADEMIC_INTEGRITY_FLAG: MULTIPLE_PERSONS"
            
        if phone_detected:
            return "UNAUTHORIZED_OBJECT"

        if smoothed_score < self.attention_threshold:
            return "DISTRACTED"

        return "FOCUSED"
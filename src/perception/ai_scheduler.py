class AIScheduler:

    def __init__(self, fire_detector=None, flood_detector=None, boulder_detector=None, fire_interval=4, flood_interval=8, boulder_interval=2):
        self.fire_detector = fire_detector
        self.flood_detector = flood_detector
        self.boulder_detector = boulder_detector
        self.fire_interval = max(1, fire_interval)
        self.flood_interval = max(1, flood_interval)
        self.boulder_interval = max(1, boulder_interval)
        self.frame_counter = 0

    def run(self, frame):
        current_frame = self.frame_counter
        self.frame_counter += 1
        results = {'fire': [], 'flood': [], 'boulder': []}
        if self.fire_detector is not None and current_frame % self.fire_interval == 0:
            results['fire'] = self.fire_detector.detect(frame)
        if self.flood_detector is not None and current_frame % self.flood_interval == 0:
            results['flood'] = self.flood_detector.detect(frame)
        if self.boulder_detector is not None and current_frame % self.boulder_interval == 0:
            results['boulder'] = self.boulder_detector.detect(frame)
        return results

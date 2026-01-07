import cv2
import json
import numpy as np
from pathlib import Path

class ZoneManager:
    def __init__(self, config_path="zones.json"):
        self.config_path = Path(config_path)
        self.zones = self._load_zones()
        self.drawing = False
        self.current_points = []
        self.delete_mode = False

    def _load_zones(self):
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return json.load(f)
        return []

    def handle_mouse(self, event, x, y, flags, param):
        # DELETE MODE: Remove zones by clicking inside them
        if self.delete_mode and event == cv2.EVENT_LBUTTONDOWN:
            for i, zone in enumerate(self.zones):
                poly = np.array(zone['points'], np.int32)
                if cv2.pointPolygonTest(poly, (x, y), False) >= 0:
                    self.zones.pop(i)
                    return

        # DRAW MODE: Left-click points, Right-click to finalize
        if not self.delete_mode:
            if event == cv2.EVENT_LBUTTONDOWN:
                self.drawing = True
                self.current_points.append([x, y])
            elif event == cv2.EVENT_RBUTTONDOWN:
                if len(self.current_points) > 2:
                    name = f"Zone {len(self.zones) + 1}"
                    self.zones.append({"name": name, "points": list(self.current_points)})
                self.current_points = []
                self.drawing = False

    def save_zones(self):
        with open(self.config_path, "w") as f:
            json.dump(self.zones, f)

    def draw_zones_on(self, frame, counts):
        overlay = frame.copy()
        # Draw Saved Polygons
        for zone in self.zones:
            pts = np.array(zone['points'], np.int32).reshape((-1, 1, 2))
            cv2.polylines(overlay, [pts], True, (255, 120, 0), 2)
            # Display Count Stats
            live = len(counts['live'].get(zone['name'], set()))
            total = len(counts['cumulative'].get(zone['name'], set()))
            cv2.putText(overlay, f"{zone['name']} L:{live} T:{total}", tuple(zone['points'][0]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Draw Active Lines while drawing
        if len(self.current_points) > 0:
            for pt in self.current_points: cv2.circle(overlay, tuple(pt), 4, (0, 255, 0), -1)
            if len(self.current_points) > 1:
                pts_drawing = np.array(self.current_points, np.int32).reshape((-1, 1, 2))
                cv2.polylines(overlay, [pts_drawing], False, (0, 255, 0), 2)
        
        return overlay

    def get_zone_at_point(self, point):
        for zone in self.zones:
            if cv2.pointPolygonTest(np.array(zone['points'], np.int32), point, False) >= 0:
                return zone['name']
        return None
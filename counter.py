import cv2
from ultralytics import YOLO
import numpy as np
import json, time
from pathlib import Path

class CounterManager:
    def __init__(self, zone_manager):
        self.model = YOLO("yolov8n.pt")
        self.zm = zone_manager
        self.heatmap = None
        self.LIVE_DATA_FILE = Path(__file__).resolve().parent / "live_data.json"
        self._init_counters()

    def _init_counters(self):
        self.zm.counted_ids = {z['name']: set() for z in self.zm.zones}
        self.zm.live_ids = {z['name']: set() for z in self.zm.zones}

    def process_frame(self, frame):
        if self.heatmap is None: 
            self.heatmap = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.float32)
        
        results = self.model.track(frame, persist=True, classes=[0], conf=0.4, verbose=False)[0]
        for z in self.zm.live_ids: self.zm.live_ids[z].clear()

        if results.boxes.id is not None:
            boxes = results.boxes.xyxy.cpu().numpy().astype(int)
            ids = results.boxes.id.cpu().numpy().astype(int)

            for (x1, y1, x2, y2), tid in zip(boxes, ids):
                cx, cy = int((x1 + x2) / 2), int(y2) # Feet detection
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.circle(self.heatmap, (cx, cy), 15, 1, -1)
                
                zone = self.zm.get_zone_at_point((cx, cy))
                if zone:
                    if zone not in self.zm.live_ids: self._init_counters()
                    self.zm.live_ids[zone].add(tid)
                    self.zm.counted_ids[zone].add(tid)

        counts = {"live": self.zm.live_ids, "cumulative": self.zm.counted_ids}
        annotated = self.zm.draw_zones_on(frame, counts)
        
        # Heatmap Blending
        h_norm = cv2.normalize(self.heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        h_color = cv2.applyColorMap(h_norm, cv2.COLORMAP_JET)
        annotated = cv2.addWeighted(annotated, 0.7, h_color, 0.3, 0)

        self._export_data(counts)
        return annotated, counts

    def _export_data(self, counts):
        with open(self.LIVE_DATA_FILE) as f:
            prev = json.load(f)
        ALERT_THRESHOLD = prev.get("threshold", 20)

        total_live = sum(len(v) for v in counts['live'].values())
        
        # Global or Zone alert logic
        zone_data = {}
        any_zone_alert = False
        for z in counts['live']:
            z_live = len(counts['live'][z])
            z_total = len(counts['cumulative'][z])
            is_z_alert = z_live >= ALERT_THRESHOLD
            if is_z_alert: any_zone_alert = True
            zone_data[z] = {"live": z_live, "total": z_total, "alert": is_z_alert}

        data = {
            "total_live": total_live,
            "total_cumulative": sum(len(v) for v in counts['cumulative'].values()),
            "zones": zone_data,
            "global_alert": total_live >= ALERT_THRESHOLD or any_zone_alert,
            "threshold": ALERT_THRESHOLD,
            "timestamp": time.strftime("%H:%M:%S")
        }
        with open(self.LIVE_DATA_FILE, "w") as f: json.dump(data, f)
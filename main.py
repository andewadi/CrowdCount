import cv2
from pathlib import Path
from zones import ZoneManager
from counter import CounterManager

VIDEO_PATH = Path(r"C:\Users\Pratik\OneDrive\Desktop\CrowdCount1\recorded_video.mp4")

def main():
    cap = cv2.VideoCapture(0 if str(VIDEO_PATH) == "0" else str(VIDEO_PATH))
    zm = ZoneManager()
    cm = CounterManager(zm)
    
    win_name = "CrowdCount AI - Milestone 3"
    cv2.namedWindow(win_name)
    cv2.setMouseCallback(win_name, zm.handle_mouse)

    while True:
        ret, frame = cap.read()

        #INFINITE LOOP
        if not ret:
            # If the video is a file (not a webcam), rewind to the start
            if str(VIDEO_PATH) != "0":
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue 
            else:
                break

        # AI Processing
        annotated_frame, _ = cm.process_frame(frame)
        
        # UI Overlay
        mode_txt = "DELETE MODE" if zm.delete_mode else "DRAW MODE"
        cv2.putText(annotated_frame, f"STATUS: {mode_txt} | 'q': Quit", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow(win_name, annotated_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): 
            break
        elif key == ord('d'): 
            zm.delete_mode = not zm.delete_mode
        elif key == ord('s'): 
            zm.save_zones()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
import cv2
from pathlib import Path

def create_video_from_frames(frames_dir, output_path="simulation.mp4", base_fps=30, speed=1.0):
    frames = sorted(Path(frames_dir).glob("*"))
    if not frames:
        return
    frame = cv2.imread(str(frames[0]))
    h, w = frame.shape[:2]

    adjusted_fps = base_fps * speed
    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), adjusted_fps, (w, h))

    for f in frames:
        img = cv2.imread(str(f))
        if img is None or img.shape[:2] != (h, w):
            continue
        writer.write(img)

    writer.release()

if __name__ =='__main__':
    create_video_from_frames("scenarios/scenario_strogino/render_frames", "scenarios/scenario_strogino/output.mp4", base_fps=30, speed=0.2)
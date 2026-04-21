import cv2
import os
import logging
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from config import CONFIG

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)


def extract_frames_hybrid(video_path: str) -> list[dict]:
    """
    Hybrid frame sampling strategy:
      1. Scene-change detection (PySceneDetect ContentDetector)
         → captures visually distinct moments at scene boundaries
      2. Uniform 1fps fallback
         → ensures coverage of slow/static scenes missed by scene detection
    
    Why not every frame?
      A 30-min video at 30fps = 54,000 frames — too slow and memory-heavy.
      This hybrid reduces that to ~1,000–2,000 frames with no meaningful loss.

    Returns:
        List of dicts: {frame_idx, timestamp, timestamp_sec, video_path, thumb_path}
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logging.error(f"Cannot open video: {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    os.makedirs(CONFIG["thumbnail_dir"], exist_ok=True)

    # --- Step 1: Scene-change detection ---
    scene_frames = set()
    if CONFIG["scene_detection"]:
        try:
            video = open_video(video_path)
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=27.0))
            scene_manager.detect_scenes(video)
            for scene in scene_manager.get_scene_list():
                scene_frames.add(int(scene[0].get_frames()))
            logging.info(f"Scene detection found {len(scene_frames)} scene boundaries in {video_path}")
        except Exception as e:
            logging.warning(f"Scene detection failed, falling back to uniform only: {e}")

    # --- Step 2: Uniform sampling ---
    step = max(1, int(fps * (1.0 / CONFIG["frame_sample_fps"])))
    uniform_frames = set(range(0, total_frames, step))

    # --- Merge both sets ---
    sampled = sorted(scene_frames | uniform_frames)
    logging.info(f"Sampling {len(sampled)} frames from {os.path.basename(video_path)} "
                 f"(scene={len(scene_frames)}, uniform={len(uniform_frames)})")

    frames_data = []
    for idx in sampled:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue

        timestamp_sec = idx / fps
        ts_str = seconds_to_hms(timestamp_sec)

        thumb_path = os.path.join(
            CONFIG["thumbnail_dir"],
            f"{os.path.splitext(os.path.basename(video_path))[0]}_f{idx}.jpg"
        )
        cv2.imwrite(thumb_path, frame)

        frames_data.append({
            "frame_idx": idx,
            "timestamp": ts_str,
            "timestamp_sec": round(timestamp_sec, 3),
            "video_path": video_path,
            "thumb_path": thumb_path,
        })

    cap.release()
    return frames_data


def seconds_to_hms(sec: float) -> str:
    """Convert float seconds to HH:MM:SS string."""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

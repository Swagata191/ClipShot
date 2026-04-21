import os
import json
import time
import tracemalloc
import faiss
import numpy as np
import open_clip
import torch
from PIL import Image
from tqdm import tqdm
from config import CONFIG
from utils import extract_frames_hybrid
import logging


def load_model():
    """
    Load CLIP ViT-B-32 model.
    - Uses FP16 on GPU for ~2x speedup and halved VRAM usage.
    - Falls back to FP32 on CPU automatically.
    """
    model, _, preprocess = open_clip.create_model_and_transforms(
        CONFIG["model_name"], pretrained=CONFIG["pretrained"]
    )
    model = model.to(CONFIG["device"])
    if CONFIG["fp16"] and CONFIG["device"] == "cuda":
        model = model.half()
    model.eval()
    logging.info(f"Model loaded on {CONFIG['device']} "
                 f"({'FP16' if CONFIG['fp16'] and CONFIG['device'] == 'cuda' else 'FP32'})")
    return model, preprocess


def embed_frames(frames_data: list, model, preprocess) -> np.ndarray:
    """
    Batch-embed all sampled frames using CLIP image encoder.

    Temporal context:
        Instead of embedding each frame in isolation, we average the embeddings
        of each frame with its ±N neighbors (configured via temporal_context_neighbors).
        This reduces ambiguity caused by motion blur or mid-action frames.

    Returns:
        float32 numpy array of shape (N, embedding_dim)
    """
    batch_size = CONFIG["batch_size"]
    n_neighbors = CONFIG.get("temporal_context_neighbors", 0)

    # --- Pass 1: embed all frames individually ---
    raw_embeddings = []
    for i in tqdm(range(0, len(frames_data), batch_size), desc="Embedding frames"):
        batch = frames_data[i:i + batch_size]
        images = []
        for f in batch:
            try:
                img = Image.open(f["thumb_path"]).convert("RGB")
                images.append(preprocess(img))
            except Exception as e:
                logging.warning(f"Skipping frame {f.get('thumb_path')}: {e}")
                images.append(torch.zeros(3, 224, 224))

        image_tensor = torch.stack(images).to(CONFIG["device"])
        if CONFIG["fp16"] and CONFIG["device"] == "cuda":
            image_tensor = image_tensor.half()

        with torch.no_grad():
            feats = model.encode_image(image_tensor)
            feats = feats / feats.norm(dim=-1, keepdim=True)

        raw_embeddings.append(feats.float().cpu().numpy())

    raw_embeddings = np.vstack(raw_embeddings)  # shape: (N, 512)

    # --- Pass 2: apply temporal context averaging ---
    if n_neighbors > 0:
        logging.info(f"Applying temporal context averaging (±{n_neighbors} neighbors)")
        smoothed = np.zeros_like(raw_embeddings)
        N = len(raw_embeddings)
        for i in range(N):
            lo = max(0, i - n_neighbors)
            hi = min(N, i + n_neighbors + 1)
            window = raw_embeddings[lo:hi]
            avg = window.mean(axis=0)
            # Re-normalize after averaging
            norm = np.linalg.norm(avg)
            smoothed[i] = avg / norm if norm > 0 else avg
        return smoothed
    else:
        return raw_embeddings


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Build FAISS index.

    Why IVFFlat (ANN) over FlatIP (exact)?
        - FlatIP is O(N) per query — fine for small archives but slow at scale.
        - IVFFlat clusters vectors into `nlist` buckets; at query time only
          `nprobe` buckets are searched → sub-linear complexity, ~same recall.
        - For 1,000-hour archives this is the only viable approach.

    Falls back to FlatIP if not enough vectors to train IVF.
    """
    dim = embeddings.shape[1]
    n = embeddings.shape[0]
    use_ann = CONFIG.get("use_ann", True)
    nlist = CONFIG.get("ivf_nlist", 50)

    if use_ann and n >= nlist * 10:
        logging.info(f"Building IVFFlat ANN index (nlist={nlist}, nprobe={CONFIG['ivf_nprobe']})")
        quantizer = faiss.IndexFlatIP(dim)
        index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
        index.nprobe = CONFIG["ivf_nprobe"]
        index.train(embeddings)
        index.add(embeddings)
    else:
        logging.info(f"Using exact FlatIP index "
                     f"({'ANN disabled' if not use_ann else f'too few vectors ({n}) to train IVF'})")
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)

    return index


def build_index(video_paths: list):
    """Full offline indexing pipeline with benchmarking."""

    # --- Start memory profiling ---
    tracemalloc.start()
    t_pipeline_start = time.time()

    model, preprocess = load_model()

    # --- Frame extraction ---
    all_frames = []
    for vp in video_paths:
        logging.info(f"Processing: {vp}")
        frames = extract_frames_hybrid(vp)
        all_frames.extend(frames)
        logging.info(f"  → {len(frames)} frames extracted")

    if not all_frames:
        logging.error("No frames extracted. Check video paths.")
        return

    logging.info(f"Total frames to embed: {len(all_frames)}")

    # --- Embedding ---
    t_embed_start = time.time()
    embeddings = embed_frames(all_frames, model, preprocess)
    t_embed_elapsed = time.time() - t_embed_start
    throughput = len(all_frames) / t_embed_elapsed

    # --- Memory snapshot ---
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # --- Build FAISS index ---
    index = build_faiss_index(embeddings)

    # --- Save index + metadata ---
    os.makedirs("results", exist_ok=True)
    faiss.write_index(index, CONFIG["index_path"])
    with open(CONFIG["metadata_path"], "w") as f:
        json.dump(all_frames, f, indent=2)

    t_pipeline_elapsed = time.time() - t_pipeline_start
    index_size_mb = os.path.getsize(CONFIG["index_path"]) / 1e6
    embed_size_mb = embeddings.nbytes / 1e6

    # --- Benchmark report ---
    benchmark = {
        "total_frames_indexed": len(all_frames),
        "videos_processed": len(video_paths),
        "embedding_time_sec": round(t_embed_elapsed, 2),
        "total_pipeline_time_sec": round(t_pipeline_elapsed, 2),
        "throughput_frames_per_sec": round(throughput, 2),
        "peak_memory_mb": round(peak_mem / 1e6, 2),
        "embedding_array_mb": round(embed_size_mb, 2),
        "faiss_index_size_mb": round(index_size_mb, 2),
        "device": CONFIG["device"],
        "model": CONFIG["model_name"],
        "ann_index": CONFIG.get("use_ann", True),
        "temporal_context_neighbors": CONFIG.get("temporal_context_neighbors", 0),
    }

    with open(CONFIG["benchmark_file"], "w") as f:
        json.dump(benchmark, f, indent=2)

    # --- Print benchmark summary ---
    print("\n" + "=" * 50)
    print("         INDEXING BENCHMARK REPORT")
    print("=" * 50)
    print(f"  Videos processed       : {len(video_paths)}")
    print(f"  Total frames indexed   : {len(all_frames)}")
    print(f"  Embedding time         : {t_embed_elapsed:.2f}s")
    print(f"  Total pipeline time    : {t_pipeline_elapsed:.2f}s")
    print(f"  Throughput             : {throughput:.1f} frames/sec")
    print(f"  Peak memory usage      : {peak_mem / 1e6:.1f} MB")
    print(f"  Embedding array size   : {embed_size_mb:.1f} MB")
    print(f"  FAISS index size       : {index_size_mb:.1f} MB")
    print(f"  Device                 : {CONFIG['device']}")
    print(f"  Index type             : {'IVFFlat (ANN)' if CONFIG.get('use_ann') else 'FlatIP (Exact)'}")
    print("=" * 50 + "\n")
    logging.info(f"Benchmark saved to {CONFIG['benchmark_file']}")


if __name__ == "__main__":
    import sys
    paths = sys.argv[1:]
    if not paths:
        print("Usage: python indexer.py videos/sample1.mp4 videos/sample2.mp4")
    else:
        build_index(paths)

import torch

CONFIG = {
    # --- Model ---
    "model_name": "ViT-B-32",
    "pretrained": "openai",
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "fp16": True,                        # FP16 on GPU, FP32 on CPU (auto)

    # --- Frame Sampling ---
    "frame_sample_fps": 1,               # 1 frame/sec uniform baseline
    "scene_detection": True,             # hybrid: scene-change + uniform
    "temporal_context_neighbors": 2,     # avg embeddings of ±2 neighboring frames

    # --- Inference ---
    "batch_size": 32,                    # GPU batch size for embedding

    # --- FAISS Index ---
    "use_ann": True,                     # True = IVFFlat ANN, False = exact FlatIP
    "ivf_nlist": 50,                     # number of IVF clusters (tune for corpus size)
    "ivf_nprobe": 10,                    # clusters to search at query time (speed vs recall)
    "embedding_dim": 512,                # ViT-B-32 output dimension

    # --- Retrieval ---
    "top_k": 10,
    "min_score_threshold": 0.25,         # discard weak matches below this score

    # --- Paths ---
    "index_path": "results/index.faiss",
    "metadata_path": "results/metadata.json",
    "thumbnail_dir": "results/thumbnails/",
    "results_file": "results/results.json",
    "benchmark_file": "results/benchmark.json",
}

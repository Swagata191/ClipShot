import json
import time
import faiss
import numpy as np
import open_clip
import torch
import logging
from config import CONFIG
from indexer import load_model

# ============================================================
# Global cache — model and index loaded ONCE, reused per query
# Loading CLIP on every search() call wastes ~2-5 seconds each time
# ============================================================
_model = None
_tokenizer = None
_index = None
_metadata = None


def _load_resources():
    """Load model, index, and metadata into globals if not already loaded."""
    global _model, _tokenizer, _index, _metadata

    if _model is None:
        logging.info("Loading CLIP model into cache...")
        _model, _ = load_model()
        _tokenizer = open_clip.get_tokenizer(CONFIG["model_name"])
        logging.info("Model cached.")

    # if _index is None:
    #     logging.info("Loading FAISS index into cache...")
    #     _index = faiss.read_index(CONFIG["index_path"])
    #     # Restore nprobe for IVF index
    #     if hasattr(_index, "nprobe"):
    #         _index.nprobe = CONFIG.get("ivf_nprobe", 10)
    #     with open(CONFIG["metadata_path"]) as f:
    #         _metadata = json.load(f)
    #     logging.info(f"Index loaded: {_index.ntotal} vectors.")
    
    if _index is None:
        logging.info("Loading FAISS index into cache...")
        _index = faiss.read_index(CONFIG["index_path"])
        if hasattr(_index, "nprobe"):
            _index.nprobe = CONFIG.get("ivf_nprobe", 10)
        logging.info(f"Index loaded: {_index.ntotal} vectors.")
    
    if _metadata is None:
        logging.info("Loading metadata...")
        with open(CONFIG["metadata_path"]) as f:
            _metadata = json.load(f)
        logging.info(f"Metadata loaded: {len(_metadata)} entries.")


def parse_temporal_filter(query: str):
    """
    Parse temporal constraints from natural language query.

    Supports:
        "after 18:00"                  → start=18:00, end=∞
        "between 06:00 and 08:00"      → start=06:00, end=08:00

    Returns:
        (clean_query, start_sec, end_sec)
    """
    import re
    start_sec, end_sec = 0, float("inf")

    m_between = re.search(r"between (\d{1,2}):(\d{2}) and (\d{1,2}):(\d{2})", query)
    if m_between:
        start_sec = int(m_between.group(1)) * 3600 + int(m_between.group(2)) * 60
        end_sec = int(m_between.group(3)) * 3600 + int(m_between.group(4)) * 60
    else:
        m_after = re.search(r"after (\d{1,2}):(\d{2})", query)
        if m_after:
            start_sec = int(m_after.group(1)) * 3600 + int(m_after.group(2)) * 60

    # Remove time tokens from query before embedding
    clean = re.sub(r"(after|between|and)\s+\d{1,2}:\d{2}", "", query).strip()
    return clean, start_sec, end_sec


def search(query: str, top_k: int = None) -> list[dict]:
    """
    Search the video index for frames matching a natural language query.

    Pipeline:
        1. Parse temporal filter from query
        2. Encode cleaned query text with CLIP
        3. ANN search in FAISS index
        4. Filter by temporal constraints + confidence threshold
        5. Return top-K ranked results

    Args:
        query:  Free-form natural language string
        top_k:  Number of results to return (default: CONFIG["top_k"])

    Returns:
        List of result dicts with timestamp, score, thumb_path, video_path, query
    """
    top_k = top_k or CONFIG["top_k"]
    _load_resources()

    timings = {}

    # --- Step 1: Parse temporal filter ---
    clean_query, t_start, t_end = parse_temporal_filter(query)
    if t_start > 0 or t_end < float("inf"):
        logging.info(f"Temporal filter: {t_start}s – {t_end if t_end < float('inf') else '∞'}s")

    # --- Step 2: Encode query text ---
    t0 = time.time()
    tokens = _tokenizer([clean_query]).to(CONFIG["device"])
    with torch.no_grad():
        text_feat = _model.encode_text(tokens)
        text_feat = text_feat / text_feat.norm(dim=-1, keepdim=True)
    query_vec = text_feat.float().cpu().numpy()
    timings["text_encode_ms"] = round((time.time() - t0) * 1000, 2)

    # --- Step 3: ANN search ---
    t1 = time.time()
    candidate_k = min(top_k * 10, _index.ntotal)
    scores, indices = _index.search(query_vec, candidate_k)
    timings["faiss_search_ms"] = round((time.time() - t1) * 1000, 2)

    # --- Step 4: Filter and rank ---
    t2 = time.time()
    min_score = CONFIG.get("min_score_threshold", 0.25)
    results = []

    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_metadata):
            continue
        if float(score) < min_score:
            continue

        frame = _metadata[idx]
        ts = frame["timestamp_sec"]
        if ts < t_start or ts > t_end:
            continue

        results.append({
            "timestamp": frame["timestamp"],
            "score": round(float(score), 4),
            "thumb_path": frame["thumb_path"],
            "video_path": frame["video_path"],
            "query": query,
        })

        if len(results) >= top_k:
            break

    timings["filter_ms"] = round((time.time() - t2) * 1000, 2)
    timings["total_ms"] = round(sum(timings.values()), 2)

    # --- Log query event with timing breakdown ---
    logging.info(
        f"Query: '{query}' | Results: {len(results)} | "
        f"encode={timings['text_encode_ms']}ms | "
        f"search={timings['faiss_search_ms']}ms | "
        f"filter={timings['filter_ms']}ms | "
        f"total={timings['total_ms']}ms"
    )

    # --- Save results to file ---
    with open(CONFIG["results_file"], "w") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python searcher.py <query>")
        print('Example: python searcher.py "person walking near the entrance"')
    else:
        q = " ".join(sys.argv[1:])
        results = search(q)
        if not results:
            print("No results found.")
        else:
            print(f"\nFound {len(results)} results for: '{q}'\n")
            for r in results:
                print(f"  [{r['timestamp']}] score={r['score']:.3f} → {r['thumb_path']}")

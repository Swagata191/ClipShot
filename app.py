import streamlit as st
from PIL import Image
from searcher import search
import json
import os
import time

st.set_page_config(
    page_title="ClipShot",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&family=Orbitron:wght@400;700;900&display=swap');

html, body { font-family: 'Rajdhani', sans-serif; }

.stApp {
    background-color: #080c10;
    background-image:
        linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    color: #c9d1d9;
}

section[data-testid="stSidebar"] {
    background-color: #0d1117 ;
    border-right: 1px solid #21262d ;
}
section[data-testid="stSidebar"] * {
    font-family: 'Share Tech Mono', monospace ;
}

.terminal-header {
    padding: 20px 0 10px;
    border-bottom: 1px solid #21262d;
    margin-bottom: 24px;
}
.terminal-logo {
    font-family: 'Orbitron', monospace;
    font-size: 28px;
    font-weight: 900;
    color: #00d4ff;
    letter-spacing: 3px;
    text-shadow: 0 0 20px rgba(0,212,255,0.5);
}
.terminal-subtitle {
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    color: #8b949e;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 4px;
}
.blink { animation: blink 1.2s step-end infinite; color: #00ff88; }
@keyframes blink { 50% { opacity: 0; } }

.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 24px;
}
.metric-card {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #21262d;
    border-top: 2px solid #00d4ff;
    border-radius: 6px;
    padding: 16px;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 60px; height: 60px;
    background: radial-gradient(circle, rgba(0,212,255,0.08) 0%, transparent 70%);
}
.metric-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 10px;
    color: #8b949e;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.metric-value {
    font-family: 'Orbitron', monospace;
    font-size: 20px;
    font-weight: 700;
    color: #00d4ff;
}
.metric-sub {
    font-family: 'Share Tech Mono', monospace;
    font-size: 10px;
    color: #3fb950;
    margin-top: 4px;
}

.section-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    color: #8b949e;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 12px;
    padding-left: 2px;
}
.section-label span { color: #00d4ff; margin-right: 8px; }

.result-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-left: 3px solid #00d4ff;
    border-radius: 6px;
    margin-bottom: 6px;
    overflow: hidden;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.result-card:hover {
    border-left-color: #00ff88;
    box-shadow: 0 0 20px rgba(0,212,255,0.08);
}
.result-header {
    background: #161b22;
    border-bottom: 1px solid #21262d;
    padding: 8px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.result-ts { font-family: 'Share Tech Mono', monospace; font-size: 13px; color: #e6edf3; }
.score-high   { color: #3fb950; font-family: 'Share Tech Mono', monospace; font-size: 12px; }
.score-medium { color: #d29922; font-family: 'Share Tech Mono', monospace; font-size: 12px; }
.score-low    { color: #f85149; font-family: 'Share Tech Mono', monospace; font-size: 12px; }
.result-meta {
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    color: #8b949e;
    margin-top: 6px;
    word-break: break-all;
}

.status-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    align-items: center;
    padding: 8px 14px;
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 4px;
    margin-bottom: 20px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    color: #8b949e;
}
.status-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; margin-right: 6px; }
.dot-green  { background: #3fb950; box-shadow: 0 0 6px #3fb950; }
.dot-blue   { background: #00d4ff; box-shadow: 0 0 6px #00d4ff; }
.dot-yellow { background: #d29922; box-shadow: 0 0 6px #d29922; }

.template-chip {
    display: block;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 3px;
    padding: 5px 10px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    color: #8b949e;
    margin-bottom: 5px;
}

.stTextInput input {
    background-color: #0d1117 !important;
    border: 1px solid #30363d !important;
    border-radius: 4px !important;
    color: #e6edf3 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 14px !important;
}
.stTextInput input:focus {
    border-color: #00d4ff !important;
    box-shadow: 0 0 0 2px rgba(0,212,255,0.2) !important;
}

.stButton button {
    background: linear-gradient(135deg, #00d4ff22, #00d4ff11) !important;
    border: 1px solid #00d4ff55 !important;
    color: #00d4ff !important;
    font-family: 'Share Tech Mono', monospace !important;
    letter-spacing: 1px !important;
    border-radius: 4px !important;
    transition: all 0.2s !important;
}
.stButton button:hover {
    background: #00d4ff22 !important;
    box-shadow: 0 0 12px rgba(0,212,255,0.3) !important;
    border-color: #00d4ff !important;
}

.stProgress > div > div {
    background: linear-gradient(90deg, #00d4ff, #00ff88) !important;
    border-radius: 2px !important;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #00d4ff55; }

#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────
metadata_exists = os.path.exists("results/metadata.json")
total_frames    = 0
indexed_videos  = set()
if metadata_exists:
    with open("results/metadata.json") as f:
        meta = json.load(f)
        total_frames   = len(meta)
        indexed_videos = {os.path.basename(m["video_path"]) for m in meta}

benchmark = {}
if os.path.exists("results/benchmark.json"):
    with open("results/benchmark.json") as f:
        benchmark = json.load(f)

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="terminal-header">
    <div class="terminal-logo">CLIPSHOT <span class="blink">█</span></div>
    <div class="terminal-subtitle">Video Intelligence Terminal &nbsp;·&nbsp; AI-Powered Forensic Retrieval</div>
</div>
""", unsafe_allow_html=True)

# ── Status bar ────────────────────────────────────────────────
index_type = "IVFFlat ANN" if benchmark.get("ann_index") else "FlatIP Exact"
throughput = benchmark.get("throughput_frames_per_sec", "—")
st.markdown(f"""
<div class="status-bar">
    <span><span class="status-dot dot-green"></span>SYSTEM ONLINE</span>
    <span><span class="status-dot dot-blue"></span>MODEL: ViT-B-32 OPENAI</span>
    <span><span class="status-dot dot-blue"></span>INDEX: {index_type}</span>
    <span><span class="status-dot dot-yellow"></span>THROUGHPUT: {throughput} fps</span>
    <span><span class="status-dot dot-green"></span>STREAMS: {len(indexed_videos)}</span>
</div>
""", unsafe_allow_html=True)

# ── Metric cards ──────────────────────────────────────────────
peak_mem   = benchmark.get("peak_memory_mb", "—")
index_size = benchmark.get("faiss_index_size_mb", "—")
device     = benchmark.get("device", "cpu").upper()

st.markdown(f"""
<div class="metric-grid">
    <div class="metric-card">
        <div class="metric-label">System Status</div>
        <div class="metric-value" style="color:#3fb950">ACTIVE</div>
        <div class="metric-sub">▲ All systems nominal</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Indexed Frames</div>
        <div class="metric-value">{total_frames:,}</div>
        <div class="metric-sub">▲ {len(indexed_videos)} video stream(s)</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Compute Device</div>
        <div class="metric-value" style="font-size:16px">{device}</div>
        <div class="metric-sub">Peak mem: {peak_mem} MB</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Index Size</div>
        <div class="metric-value">{index_size}<span style="font-size:13px"> MB</span></div>
        <div class="metric-sub">▲ FAISS {index_type}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="font-family:'Orbitron',monospace;font-size:16px;font-weight:700;
                color:#00d4ff;letter-spacing:2px;padding:10px 0 4px;">CLIPSHOT</div>
    <div style="font-family:'Share Tech Mono',monospace;font-size:10px;
                color:#8b949e;letter-spacing:2px;margin-bottom:18px;">
        INTELLIGENCE TERMINAL v1.0
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label"><span>▸</span>INDEXED STREAMS</div>', unsafe_allow_html=True)
    if indexed_videos:
        for v in sorted(indexed_videos):
            st.markdown(f"""
            <div style="font-family:'Share Tech Mono',monospace;font-size:11px;
                        color:#3fb950;padding:3px 0;border-bottom:1px solid #21262d;">
                ● &nbsp;{v}
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace;font-size:11px;color:#f85149;">
            ⚠ No index found.<br>Run: python indexer.py videos/
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label"><span>▸</span>PARAMETERS</div>', unsafe_allow_html=True)

    top_k = st.selectbox(
        "Results Limit (Top-K)",
        options=[1, 3, 5, 10, 15, 20],
        index=3
    )
    score_threshold = st.slider(
        "Confidence Threshold",
        min_value=0.10, max_value=0.50,
        value=0.25, step=0.01
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label"><span>▸</span>QUERY TEMPLATES</div>', unsafe_allow_html=True)
    for t in [
        "person near the entrance",
        "crowded indoor corridor",
        "cars parked from above",
        "group of people outdoors",
        "person carrying a bag",
        "two people talking after 18:00",
    ]:
        st.markdown(f'<div class="template-chip">{t}</div>', unsafe_allow_html=True)

    if benchmark:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label"><span>▸</span>BENCHMARK</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="font-family:'Share Tech Mono',monospace;font-size:11px;
                    color:#8b949e;line-height:2.2;">
        THROUGHPUT &nbsp;{benchmark.get('throughput_frames_per_sec','—')} fps<br>
        EMBED TIME &nbsp;{benchmark.get('embedding_time_sec','—')}s<br>
        PEAK MEM &nbsp;&nbsp;{benchmark.get('peak_memory_mb','—')} MB<br>
        INDEX SIZE &nbsp;{benchmark.get('faiss_index_size_mb','—')} MB<br>
        NEIGHBORS &nbsp;&nbsp;±{benchmark.get('temporal_context_neighbors','—')}
        </div>""", unsafe_allow_html=True)

# ── Query Interface ───────────────────────────────────────────
st.markdown('<div class="section-label"><span>▸</span>INTELLIGENCE QUERY</div>', unsafe_allow_html=True)

col_input, col_btn, col_reset = st.columns([5, 1.2, 0.8])
with col_input:
    query = st.text_input(
        label="query",
        placeholder="e.g. person carrying a bag near exit after 18:00",
        label_visibility="collapsed"
    )
with col_btn:
    search_clicked = st.button("⚡ SEARCH", type="primary", use_container_width=True)
with col_reset:
    if st.button("↺ Reset", use_container_width=True):
        st.rerun()

# ── Results ───────────────────────────────────────────────────
if search_clicked and query:
    t0 = time.time()
    with st.spinner("Scanning index..."):
        results = search(query, top_k=top_k)
    elapsed = time.time() - t0

    results = [r for r in results if r["score"] >= score_threshold]

    st.markdown("<br>", unsafe_allow_html=True)

    if not results:
        st.error(f"⚠ No matches above threshold ({score_threshold:.2f}). Try lowering the confidence threshold or rephrasing your query.")
    else:
        st.markdown(f"""
        <div class="status-bar">
            <span><span class="status-dot dot-green"></span>QUERY COMPLETE</span>
            <span>MATCHES: <b style="color:#e6edf3">{len(results)}</b></span>
            <span>ELAPSED: <b style="color:#e6edf3">{elapsed:.2f}s</b></span>
            <span>QUERY: <b style="color:#00d4ff">"{query}"</b></span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-label"><span>▸</span>RETRIEVED FRAMES</div>', unsafe_allow_html=True)

        cols = st.columns(3)
        for i, r in enumerate(results):
            score = r["score"]
            if score >= 0.28:
                score_cls, score_lbl = "score-high", "HIGH"
            elif score >= 0.25:
                score_cls, score_lbl = "score-medium", "MED"
            else:
                score_cls, score_lbl = "score-low", "LOW"

            with cols[i % 3]:
                st.markdown(f"""
                <div class="result-card">
                    <div class="result-header">
                        <span class="result-ts">⏱ {r['timestamp']}</span>
                        <span class="{score_cls}">■ {score_lbl} &nbsp;{score:.4f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                img = Image.open(r["thumb_path"])
                st.image(img, use_container_width=True)
                st.progress(min(score * 2, 1.0))
                st.markdown(f'<div class="result-meta">↳ {os.path.basename(r["video_path"])}</div>', unsafe_allow_html=True)

                # ✅ Video playback at exact timestamp
                if os.path.exists(r["video_path"]):
                    with st.expander("▶ Play at timestamp"):
                        st.video(r["video_path"], start_time=int(r.get("timestamp_sec", 0)))

                st.markdown("<br>", unsafe_allow_html=True)

        # ── Export ────────────────────────────────────────────
        st.markdown("---")
        st.markdown('<div class="section-label"><span>▸</span>EXPORT</div>', unsafe_allow_html=True)
        dl1, dl2 = st.columns(2)
        with dl1:
            if os.path.exists("results/results.json"):
                with open("results/results.json") as f:
                    st.download_button(
                        "📥 Export Results JSON",
                        f,
                        file_name=f"clipshot_{int(time.time())}.json",
                        mime="application/json",
                        use_container_width=True
                    )
        with dl2:
            if benchmark:
                st.download_button(
                    "📊 Export Benchmark JSON",
                    json.dumps(benchmark, indent=2),
                    file_name="clipshot_benchmark.json",
                    mime="application/json",
                    use_container_width=True
                )

elif search_clicked and not query:
    st.warning("⚠ Query cannot be empty.")

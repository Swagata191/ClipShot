# ClipShot – Video Intelligence Terminal

ClipShot is an AI-powered video search system that enables **natural language querying over videos**. It uses CLIP embeddings + FAISS indexing to retrieve the most relevant frames with timestamps.

---

## 🚀Key Features
* **Text-to-Video Search** – Query videos using natural language  
* **CLIP Embeddings** – Semantic understanding of scenes  
* **Fast Retrieval** – FAISS-based similarity search  
* **Frame-Level Results** – Timestamped thumbnails + playback  
* **Modern UI** – Streamlit-based interactive dashboard  

---

## 🛠️ Tech Stack
| Category | Technology |
| :--- | :--- |
| **Frontend** | Streamlit |
- **Backend** | Python |  
- **Model** | OpenAI CLIP (ViT-B/32) |
- **Indexing** | FAISS |

---

## ▶️ Demo

🎥 **Project Demo Video:**  
👉 [Watch Demo](YOUR_VIDEO_LINK_HERE)

📦 **Full Test Video (Large File):**  
👉 [Download test_video.mp4](YOUR_GOOGLE_DRIVE_LINK)

---

📂 Project Structure
```text
ClipShot/
├── app.py
├── indexer.py
├── searcher.py
├── utils.py
├── requirements.txt
├── videos/              # Sample videos
├── results/             # Metadata + thumbnails
└── README.md
```

---

Example queries:
- *"person carrying a bag near entrance"*
- *"cars parked from above"*
- *"two people talking after 18:00"*

---

## 🏗️ Architecture Overview

### 🔹 Pipeline
Video Input → Frame Sampling → CLIP Embedding → FAISS Index → Query Encoding → ANN Search → Results

### 🔹 Components
#### 1. Video Ingestion
- Reads videos from directory
- Extracts frames at fixed intervals
#### 2. Frame Sampling
- Uniform sampling strategy (efficient & memory-safe)
- Avoids processing every frame
#### 3. Embedding (Core AI)
- Model: **CLIP (ViT-B/32 - OpenAI)**
- Converts:
  - Frames → Image embeddings
  - Queries → Text embeddings
- Shared embedding space enables semantic matching
#### 4. Vector Index
- Library: **FAISS**
- Supports:
  - Flat (Exact Search)
  - IVF (Approximate ANN)
- Optimized for fast similarity search
#### 5. Query Engine
- Encodes text query
- Performs nearest neighbor search
- Returns:
  - Timestamp
  - Score
  - Thumbnail
  - Video reference

#### 6. UI (Streamlit)
- Interactive dashboard
- Real-time search
- Frame previews + video playback

---

## ⚙️ Setup & Installation

### 1. Clone Repo
```bash
git clone [https://github.com/Swagata191/ClipShot.git](https://github.com/Swagata191/ClipShot.git)
cd ClipShot
```
### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
### 3. Add Videos
```bash
mkdir videos # Add your .mp4 files here
```
### 4. Run Indexing Pipeline
```bash
python indexer.py videos/file_name.mp4
```
### 5. Launch UI
```bash
streamlit run app.py
```

---

## 📊 Benchmark Results
Metric	Value
Throughput	~4.4 FPS
Embedding Time	~1.36s
Peak Memory	~52 MB
Index Size	~0.01 MB
Device	CPU

---

##⚡ Performance Optimizations
Batch embedding for faster inference
FAISS ANN indexing (IVFFlat)
Lightweight CLIP model
Efficient frame sampling

---

## 📁 Output Format
Results are stored in:
```bash
results/results.json
```

---

## ⚠️ Known Limitations
- No true temporal reasoning (frame-level only)
- Limited query understanding for complex relationships
- No re-ranking stage yet
- Performance depends on sampling rate

---

## 🔍 Future Improvements
- Temporal modeling (video clips instead of frames)
- Query decomposition (multi-object reasoning)
- Re-ranking using cross-attention models
- GPU acceleration
- Scalable indexing for large datasets

---

## 🌟 What I Explored Beyond Requirements
- Built a full UI dashboard with:
- Live search
- Confidence scoring
- Video playback at timestamp
- Implemented ANN indexing
- Added benchmark tracking
- Designed a cyberpunk-style UX interface

---

## Developed by Swagata Maji
## Domain: Video AI & Retrieval 
## Subject: Variphi Take-Home Project

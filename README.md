# Multi-Source RAG 🚀

A lightweight **Multi-Source Retrieval Augmented Generation (RAG)** system that lets you ingest knowledge from files and websites, then chat with an AI grounded in your data — with **hybrid retrieval**, **streaming responses**, and a modern UI.



## 📸 Screenshots

### 🏗️ Architecture (1)
![Architecture 1](docs/architecture/Ingestion.png)

### 🏗️ Architecture (2)
![Architecture 2](docs/architecture/Query-pipeline.png)

### 💻 UI (Light/Dark + Draft Chat)
![UI 1](docs/screenshot/new_chat_ui.png)

### 💻 UI (Chat + Sources + Ingestion)
![UI 2](docs/screenshot/UI_2.png)





## ✨ Features

### ✅ Multi-Source Ingestion
- Upload files: **PDF, DOCX, TXT**
- Ingest **Web URLs**
- Chunking + Embedding + Storage into Vector DB

### ✅ Hybrid Retrieval + RAG Pipeline
- **Hybrid Retrieval (Dense + Keyword/BM25-style)**
- Dense retrieval with embeddings
- Multi-Query expansion
- Cross-Encoder reranking


### ✅ Conversations + Memory
- Multiple conversations supported
- Chat history stored in **PostgreSQL**
- Delete conversations

### ✅ Streaming UI + Sources
- Real-time **token streaming** answers
- Retrieved **sources shown** under assistant messages


### ✅ Draft Chat 
- App opens into a **New Chat (Draft)**
- Draft chat is **UI-only** (not stored in DB)
- A real conversation is created only when the user:
  - sends the first message, OR
  - uploads a file / URL
- Sidebar refreshes instantly when a chat is created

### ✅ Dark Mode
- Light/Dark theme switch
- Theme persists via `localStorage`

### ✅ Docker + Deployment Ready
- Dockerized frontend + backend setup
- Easy to run locally with Docker Compose



## 🧱 Tech Stack

### Backend
- FastAPI
- PostgreSQL (chat history)
- ChromaDB (vector database)
- OpenAI API (LLM)
- HuggingFace Cross-Encoder (reranking)

### Frontend
- React (Vite)
- Streaming via Fetch + ReadableStream
- Clean UI with Draft Chat behavior



## ⚡ Quick Start (Local)

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API Docs:
```
http://127.0.0.1:8000/docs
```

### Frontend
```bash
cd rag-ui
npm install
npm run dev
```

UI:
```
http://127.0.0.1:5173
```

---

## 🐳 Run with Docker

Build and run everything:
```bash
docker compose up --build
```

Stop:
```bash
docker compose down
```

---

## 🔗 Key API Routes

### Chat / Query
- `POST /query` — Non-streaming response
- `POST /query/stream` — Streaming response

### Conversations
- `POST /conversations` — Create new conversation
- `GET /conversations` — List conversations
- `GET /conversations/{id}` — Get conversation + messages
- `DELETE /conversations/{id}` — Delete conversation

### Ingestion
- `POST /ingest` — Upload file
- `POST /ingest/url` — Ingest URL



## 📌 Roadmap (Next Improvements)
- OCR ingestion (scanned PDFs + images)
- Better table extraction and table-aware chunking
- Better citations (page numbers + metadata)
- Guardrails for RAG

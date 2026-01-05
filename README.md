#  Multi‑Source RAG 

A lightweight **Retrieval Augmented Generation (RAG)** system that lets
you ingest knowledge from files and websites then chat with an AI
grounded in your data.

##  Features

-   Multi‑source ingestion (PDF, DOCX, TXT, Web URLs)
-   Dense retrieval with embeddings
-   Multi‑Query Expansion & cross‑encoder reranking
-   Conversation history & memory (PostgreSQL)
-   Vector search via ChromaDB
-   React chat UI (Vite) + FastAPI backend
-   Secure config via `.env`

##  Quick Start

### Backend

``` bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open API docs → `http://127.0.0.1:8000/docs`

### Frontend

``` bash
cd rag-ui
npm install
npm run dev
```

Open → `http://127.0.0.1:5173`

## 🔗 Key API Routes

-   `POST /query` --- Chat with RAG
-   `POST /conversations` --- New chat
-   `GET  /conversations` --- List chats
-   `GET  /conversations/{id}` --- Chat history
-   `POST /ingest/file` --- Upload documents
-   `POST /ingest/url` --- Ingest website


##  Stack

FastAPI • React (Vite) • PostgreSQL • ChromaDB • OpenAI API •
HuggingFace Cross‑Encoder

##  Roadmap

-   File + URL upload in UI
-   Show retrieved sources
-   Streaming bot responses
-   Reduce latency
-   Polish UI
-   Docker & deployment


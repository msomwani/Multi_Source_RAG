from fastapi import APIRouter, UploadFile, HTTPException, File, Query
from io import BytesIO
from app.ingestion.text_splitter import chunk_text
from app.llm.embeddings import embed
from app.vectorstore.store import add_chunks

from PyPDF2 import PdfReader
import docx
import requests
from bs4 import BeautifulSoup

router = APIRouter()


# ---------- HELPERS ----------

def load_pdf_bytes(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n".join([p.extract_text() or "" for p in reader.pages])


def load_docx_bytes(data: bytes) -> str:
    document = docx.Document(BytesIO(data))
    return "\n".join([p.text for p in document.paragraphs])


def load_web_page(url: str) -> str:
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # remove script & style tags
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()

    text = soup.get_text(separator="\n")
    cleaned = "\n".join(
        line.strip() for line in text.splitlines() if line.strip()
    )

    return cleaned


# ---------- FILE INGEST ----------

@router.post("/ingest")
async def ingest_file(conversation_id:int,file: UploadFile = File(...)):

    raw = await file.read()
    name = file.filename.lower()

    if name.endswith(".pdf"):
        text = load_pdf_bytes(raw)

    elif name.endswith(".docx"):
        text = load_docx_bytes(raw)

    elif name.endswith(".txt"):
        text = raw.decode("utf-8", errors="ignore")

    else:
        raise HTTPException(400, detail="Unsupported file type")

    # chunk + embed
    chunks = chunk_text(text)
    vectors = embed(chunks)

    add_chunks(
        file.filename,
        chunks,
        vectors,
        [{"source": file.filename}] * len(chunks),
        conversation_id=conversation_id
    )


    return {"status": "ok", "chunks": len(chunks)}


# ---------- URL INGEST ----------

@router.post("/ingest/url")
async def ingest_url(conversation_id:int,url: str = Query(..., description="Web page URL")):
    """
    Ingest a web page by URL.
    Expected call format (React):
    POST /ingest/url?url=https://example.com
    """

    text = load_web_page(url)

    chunks = chunk_text(text)
    vectors = embed(chunks)

    add_chunks(
        url,
        chunks,
        vectors,
        [{"source": url}] * len(chunks),
        conversation_id=conversation_id
    )

    return {"status": "ok", "source": url, "chunks": len(chunks)}

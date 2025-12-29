from fastapi import APIRouter, UploadFile, HTTPException
from io import BytesIO
from app.ingestion.text_splitter import chunk_text
from app.llm.embeddings import embed
from app.vectorstore.store import add_chunks

from PyPDF2 import PdfReader
import docx
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel


router = APIRouter()


def load_pdf_bytes(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n".join([p.extract_text() or "" for p in reader.pages])


def load_docx_bytes(data: bytes) -> str:
    document = docx.Document(BytesIO(data))
    return "\n".join([p.text for p in document.paragraphs])


@router.post("/ingest")
async def ingest_file(file: UploadFile):

    raw = await file.read()

    # pick loader based on extension
    name = file.filename.lower()

    if name.endswith(".pdf"):
        text = load_pdf_bytes(raw)

    elif name.endswith(".docx"):
        text = load_docx_bytes(raw)

    elif name.endswith(".txt"):
        # tolerate weird encodings
        text = raw.decode("utf-8", errors="ignore")

    else:
        raise HTTPException(400, detail="Unsupported file type")

    # --- chunk + embed ---
    chunks = chunk_text(text)
    vectors = embed(chunks)

    add_chunks(
        file.filename,
        chunks,
        vectors,
        [{"source": file.filename}] * len(chunks),
    )

    return {"status": "ok", "chunks": len(chunks)}


class URLIngestRequest(BaseModel):
    url:str

def load_web_page(url: str) -> str:
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # remove script & style tags
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()

    text = soup.get_text(separator="\n")
    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    return cleaned



@router.post("/ingest/url")
async def ingest_url(body: URLIngestRequest):

    text = load_web_page(body.url)

    chunks = chunk_text(text)
    vectors = embed(chunks)

    add_chunks(
        body.url,
        chunks,
        vectors,
        [{"source": body.url}] * len(chunks),
    )

    return {"status": "ok", "source": body.url, "chunks": len(chunks)}

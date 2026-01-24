from fastapi import APIRouter, UploadFile, HTTPException, File, Query
from io import BytesIO
from typing import List, Dict

from app.ingestion.text_splitter import chunk_text
from app.ingestion.table_utils import make_table_json, table_to_row_chunks
from app.llm.embeddings import embed
from app.vectorstore.store import add_chunks

from PyPDF2 import PdfReader
import docx
import requests
from bs4 import BeautifulSoup

from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from pdf2image import convert_from_bytes
import pdfplumber

router = APIRouter()

# ---------- HELPERS ----------

def load_pdf_bytes(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n".join(p.extract_text() or "" for p in reader.pages)


def load_docx_bytes(data: bytes) -> str:
    document = docx.Document(BytesIO(data))
    return "\n".join(p.text for p in document.paragraphs)


def load_docx_tables_structured(data: bytes) -> List[Dict]:
    """
    Returns:
      [
        { "title": "DOCX TABLE 1", "rows": [[...header...], [...row...]] }
      ]
    """
    document = docx.Document(BytesIO(data))
    tables = []

    for t_index, table in enumerate(document.tables):
        rows = []
        for row in table.rows:
            cells = [(cell.text or "").strip().replace("\n", " ") for cell in row.cells]
            rows.append(cells)

        if not rows or len(rows) < 2:
            continue

        tables.append(
            {
                "title": f"DOCX TABLE {t_index + 1}",
                "rows": rows,
            }
        )

    return tables


def load_pdf_tables_structured(data: bytes, max_pages: int = 10) -> List[Dict]:
    """
    Returns:
      [
        { "title": "PDF TABLE (Page 1, Table 1)", "rows": [[...header...], [...row...]] }
      ]
    """
    tables_out = []

    with pdfplumber.open(BytesIO(data)) as pdf:
        total_pages = min(len(pdf.pages), max_pages)

        for p_index in range(total_pages):
            page = pdf.pages[p_index]
            tables = page.extract_tables()

            if not tables:
                continue

            for t_index, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue

                rows = []
                for row in table:
                    clean_row = [(c or "").strip().replace("\n", " ") for c in row]
                    rows.append(clean_row)

                tables_out.append(
                    {
                        "title": f"PDF TABLE (Page {p_index + 1}, Table {t_index + 1})",
                        "rows": rows,
                    }
                )

    return tables_out


def load_web_page(url: str) -> str:
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()

    text = soup.get_text(separator="\n")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def load_image_bytes_ocr(data: bytes) -> str:
    img = Image.open(BytesIO(data)).convert("RGB")
    text = pytesseract.image_to_string(img, config="--oem 3 --psm 6")
    return text.strip()


def preprocess_for_ocr(img: Image.Image) -> Image.Image:
    img = img.convert("L")  # grayscale
    img = ImageEnhance.Contrast(img).enhance(2.0)  # contrast boost
    img = img.filter(ImageFilter.SHARPEN)  # sharpening

    w, h = img.size
    img = img.resize((w * 2, h * 2))  # upscale

    return img.convert("L")


def load_pdf_bytes_with_ocr_fallback(data: bytes, max_pages: int = 15) -> str:
    extracted_text = load_pdf_bytes(data)

    # ✅ if text exists, don't waste time doing OCR
    if extracted_text and len(extracted_text.strip()) > 50:
        return extracted_text

    images = convert_from_bytes(data, dpi=300, first_page=1, last_page=max_pages)
    ocr_texts = []

    for idx, img in enumerate(images):
        img = preprocess_for_ocr(img)
        page_text = pytesseract.image_to_string(img, config="--oem 3 --psm 6").strip()

        if page_text:
            ocr_texts.append(f"\n\n--- Page {idx + 1} ---\n{page_text}")

    return "\n".join(ocr_texts).strip()


# ---------- FILE INGEST ----------

@router.post("/ingest")
async def ingest_file(
    conversation_id: int = Query(...),
    file: UploadFile = File(...)
):
    raw = await file.read()
    name = file.filename.lower()

    chunks: List[str] = []
    metas: List[dict] = []

    tables_structured: List[Dict] = []
    text_main = ""

    if name.endswith(".pdf"):
        text_main = load_pdf_bytes_with_ocr_fallback(raw)
        tables_structured = load_pdf_tables_structured(raw)

    elif name.endswith(".docx"):
        text_main = load_docx_bytes(raw)
        tables_structured = load_docx_tables_structured(raw)

    elif name.endswith(".txt"):
        text_main = raw.decode("utf-8", errors="ignore").strip()

    elif name.endswith((".png", ".jpg", ".jpeg")):
        text_main = load_image_bytes_ocr(raw).strip()

    else:
        raise HTTPException(400, detail="Unsupported file type")

    if not text_main.strip() and not tables_structured:
        raise HTTPException(400, detail="No text extracted from file")

    # ✅ Chunk normal text (safe for RAG)
    if text_main.strip():
        main_chunks = chunk_text(text_main)
        chunks.extend(main_chunks)
        metas.extend(
            [
                {
                    "source": file.filename,
                    "type": "text",
                }
            ]
            * len(main_chunks)
        )

    # ✅ Table rows become searchable chunks
    for t in tables_structured:
        table_json = make_table_json(t["title"], t["rows"])
        if not table_json:
            continue

        row_chunks = table_to_row_chunks(table_json)

        for rc in row_chunks:
            chunks.append(rc)
            metas.append(
                {
                    "source": file.filename,
                    "type": "table_row",
                    "table": table_json,  # ✅ store full structured table JSON
                }
            )

    if not chunks:
        raise HTTPException(400, detail="No chunks produced from file")

    vectors = embed(chunks)

    add_chunks(
        file.filename,
        chunks,
        vectors,
        metas,
        conversation_id=conversation_id,
    )

    return {
        "status": "ok",
        "chunks": len(chunks),
        "tables": len(tables_structured),
    }


# ---------- URL INGEST ----------

@router.post("/ingest/url")
async def ingest_url(
    conversation_id: int = Query(...),
    url: str = Query(...),
):
    text = load_web_page(url)

    if not text.strip():
        raise HTTPException(400, detail="No text extracted from URL")

    chunks = chunk_text(text)
    vectors = embed(chunks)

    add_chunks(
        url,
        chunks,
        vectors,
        [{"source": url, "type": "text"}] * len(chunks),
        conversation_id=conversation_id,
    )

    return {"status": "ok", "source": url, "chunks": len(chunks)}

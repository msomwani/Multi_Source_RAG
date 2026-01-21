from fastapi import APIRouter, UploadFile, HTTPException, File, Query
from io import BytesIO
from app.ingestion.text_splitter import chunk_text
from app.llm.embeddings import embed
from app.vectorstore.store import add_chunks

from PyPDF2 import PdfReader
import docx
import requests
from bs4 import BeautifulSoup

from PIL import Image,ImageEnhance,ImageFilter
import pytesseract
from pdf2image import convert_from_bytes
import pdfplumber

router = APIRouter()

# ---------- HELPERS ----------

def load_pdf_bytes(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n".join(p.extract_text() or "" for p in reader.pages)

def load_pdf_tables_bytes(data:bytes,max_pages:int=20):
    tables_text=[]
    with pdfplumber.open(BytesIO(data)) as pdf:
        total_pages=min(len(pdf.pages),max_pages)

        for p_index in range(total_pages):
            page=pdf.pages[p_index]
            tables=page.extract_tables()

            if not tables:
                continue

            tables_text.append(f"\n\n--- PDF TABLES (Page {p_index + 1}) ---")

            for t_index, table in enumerate(tables):
                tables_text.append(f"[Table {t_index + 1}]")

                for row in table:
                    if not row:
                        continue
                    clean_row = [(c or "").strip().replace("\n", " ") for c in row]
                    line = " | ".join(clean_row)
                    if line.strip():
                        tables_text.append(line)

    return "\n".join(tables_text).strip()

def load_docx_bytes(data: bytes) -> str:
    document = docx.Document(BytesIO(data))
    return "\n".join(p.text for p in document.paragraphs)

def load_docx_tables_bytes(data: bytes) -> str:
    
    document = docx.Document(BytesIO(data))
    tables_text = []

    for t_index, table in enumerate(document.tables):
        tables_text.append(f"\n\n--- DOCX TABLE {t_index + 1} ---")

        for row in table.rows:
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            line = " | ".join(cells)
            if line.strip():
                tables_text.append(line)

    print("✅ DOCX tables found:", len(document.tables))

    return "\n".join(tables_text).strip()

def load_web_page(url: str) -> str:
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()

    text = soup.get_text(separator="\n")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())

def load_image_bytes_ocr(data:bytes)->str:
    img=Image.open(BytesIO(data)).convert("RGB")
    text=pytesseract.image_to_string(img,config="--oem 3 --psm 6")
    return text.strip()

def preprocess_for_ocr(img:Image.Image)->Image.Image:
    img=img.convert("L")#grayscale

    img=ImageEnhance.Contrast(img).enhance(2.0)#contrast boost
    img=img.filter(ImageFilter.SHARPEN)#sharpening
    w,h=img.size
    img=img.resize((w*2,h*2))#upscale
    # img=img.point(lambda x:0 if x < 140 else 255 ,"1")#thresholding

    return img.convert("L")

def load_pdf_bytes_with_ocr_fallback(data:bytes,max_pages:int=15)->str:
    extracted_text=load_pdf_bytes(data)

    if extracted_text and len(extracted_text.strip())>50:
        return extracted_text
    
    images=convert_from_bytes(data,dpi=300,first_page=1,last_page=max_pages)
    ocr_texts=[]

    for idx, img in enumerate(images):
        img=preprocess_for_ocr(img)
        page_text = pytesseract.image_to_string(img,config="--oem 3 --psm 6")
        page_text = page_text.strip()

        if page_text:
            ocr_texts.append(f"\n\n--- Page {idx + 1} ---\n{page_text}")

    final_text = "\n".join(ocr_texts).strip()
    return final_text

# ---------- FILE INGEST ----------

@router.post("/ingest")
async def ingest_file(
    conversation_id: int = Query(...),
    file: UploadFile = File(...)
):
    raw = await file.read()
    name = file.filename.lower()

    if name.endswith(".pdf"):
        text_main = load_pdf_bytes_with_ocr_fallback(raw)
        text_tables = load_pdf_tables_bytes(raw)#tables extraction
        text = (text_main + "\n\n" + text_tables).strip()
    elif name.endswith(".docx"):
        text_main = load_docx_bytes(raw)
        text_tables = load_docx_tables_bytes(raw)#tables extraction
        text = (text_main + "\n\n" + text_tables).strip()
    elif name.endswith(".txt"):
        text = raw.decode("utf-8", errors="ignore")
    elif name.endswith((".png",".jpg",".jpeg")):
        text=load_image_bytes_ocr(raw)
        
    else:
        raise HTTPException(400, detail="Unsupported file type")
    
    #text.strip is blank
    if not text.strip():
        raise HTTPException(400, detail="No text extracted from file")

    chunks = chunk_text(text)
    vectors = embed(chunks)

    add_chunks(
        file.filename,
        chunks,
        vectors,
        [{"source": file.filename}] * len(chunks),
        conversation_id=conversation_id,
    )

    return {"status": "ok", "chunks": len(chunks)}

# ---------- URL INGEST ----------

@router.post("/ingest/url")
async def ingest_url(
    conversation_id: int = Query(...),
    url: str = Query(...),
):
    text = load_web_page(url)

    chunks = chunk_text(text)
    vectors = embed(chunks)

    add_chunks(
        url,
        chunks,
        vectors,
        [{"source": url}] * len(chunks),
        conversation_id=conversation_id,
    )

    return {"status": "ok", "source": url, "chunks": len(chunks)}

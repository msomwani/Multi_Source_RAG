import docx
import requests
from PyPDF2 import PdfReader
from pathlib import Path

def load_pdf(path:Path):
    reader=PdfReader(path)
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def load_docx(path:Path):
    doc=docx.Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

def load_txt(path):
    return open(path).read()

def load_web(url):
    return requests.get(url).text


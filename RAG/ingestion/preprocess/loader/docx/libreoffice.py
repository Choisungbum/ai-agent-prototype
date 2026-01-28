import subprocess
from pathlib import Path
import json, uuid, os, hashlib
import time

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
chunk_dir = os.path.join(BASE_DIR, "chunk")
# docx_dir = os.path.join(BASE_DIR, "testfile","docx")
docx_dir = '/app/ingestion/testfile/docx/'
pdf_dir = '/app/ingestion/testfile/pdf/docxtopdf'

os.makedirs(chunk_dir, exist_ok=True)

docx_path = "/app/ingestion/testfile/docx/테스트 AI Agent 실행 가이드.docx"


def docx_to_pdf(docx_path: str, out_dir: str):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    docx_path = Path(docx_path).resolve()
    pdf_path = out_dir / (docx_path.stem + ".pdf")

    # 1) DOCX → PDF
    subprocess.run([
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",      # 변환 명령
        str(docx_path),             # 변환 대상 파일
        "--outdir", str(out_dir)    # 결과 PDF 저장 위치 지정
    ], check=True)

    # 2) Ghostscript 정규화
    tmp_pdf = pdf_path.with_suffix(".tmp.pdf")

    subprocess.run([
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/prepress",
        "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={tmp_pdf}",
        str(pdf_path)
    ], check=True)

    tmp_pdf.replace(pdf_path)  # clean → 원본 pdf로 교체

    return pdf_path


# 파일명 
# 1.영어
# 2.공백 X 
for name in os.listdir(docx_dir):
    if not name.endswith(".docx"):
        continue

    docx_path = str(Path(docx_dir, name).resolve())
    print(docx_path)
    print(Path(docx_path).exists())

    docx_to_pdf(docx_path, pdf_dir)

print('end')
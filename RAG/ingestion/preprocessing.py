from preprocessing.loader.pdf.lib_pymupdf import parse_pdf_for_rag_json
from preprocessing.chunker.chunking import extract_paragraphs, semantic_chunking

import json, uuid, os, hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
chunk_dir = os.path.join(BASE_DIR, "chunk")
test_dir = os.path.join(BASE_DIR, "testfile")

os.makedirs(chunk_dir, exist_ok=True)

def chunk_file(pdf_path):
    # 1. 문서 로드 -> 구조화된 json 데이터로 출력 (텍스트, 표) 
    document= parse_pdf_for_rag_json(pdf_path)

    # 2-1. paragraph 추출 및 heading 결합 (blocks → paragraph, 제목 → 다음 문단에 붙이기)
    paragrephs = extract_paragraphs(document)

    # 2-2. semantic chunking (길이 기준, 의미 유지)
    chunks = semantic_chunking(paragrephs)
    print(chunks)

    name = pdf_path.rsplit("/")
    file_name = name[-1]
    dir_name = name[-2]

    with open(f"{chunk_dir}/{dir_name}/{file_name}.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


exts = ['/pdf']

for ext in exts:
    full_test_dir = test_dir + ext
    # test 파일 디렉토리 순회하며 파일 open
    for name in os.listdir(full_test_dir):
        if '.' not in name:
            continue

        chunk_file(full_test_dir + '/' + name)



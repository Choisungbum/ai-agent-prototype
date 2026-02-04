from ingestion.loaders.pdf_loader import parse_pdf_for_rag_json
from ingestion.loaders.libreoffice import convert_docs_in_dir
from ingestion.preprocess.chunker.chunking import extract_paragraphs, semantic_chunking_by_section, build_2level_summaries

import json, uuid, os, hashlib
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
raw_dir = os.path.join(BASE_DIR, "raw_dir")                               # 원본 문서가 있는 dir
staging_dir = os.path.join(BASE_DIR, "working_dir", "staging_dir")        # 사용할 파일을 복사해오는 dir
converted_dir = os.path.join(BASE_DIR, "working_dir", "converted_dir")    # 사용할 파일을 변환하는 dir
chunk_dir = os.path.join(BASE_DIR, "chunk")

os.makedirs(chunk_dir, exist_ok=True)


def get_ext(filename):
    return os.path.splitext(filename)[1]

def chunk_file(pdf_path):
    ext = get_ext(pdf_path)

    # elif ext == "docx":
    #     return load_docx(path)
    # elif ext == "hwp":
    #     return load_hwp(path)
    # 1. 문서 로드 -> 구조화된 json 데이터로 출력 (텍스트, 표) 
    if ext == "pdf":
        document= parse_pdf_for_rag_json(pdf_path)

    # 원문 chunk
    # with open(f"document.json", "w", encoding="utf-8") as f:
    #     json.dump(document, f, ensure_ascii=False, indent=2)

    # 2-1. paragraph 추출 및 heading 결합 (blocks → paragraph, 제목 → 다음 문단에 붙이기)
    paragrephs = extract_paragraphs(document)

    # 2-2. semantic chunking (section 및 title 기준 )
    chunks = semantic_chunking_by_section(paragrephs)

    # 3. summary(top, mid), 원문 chunk 생성
    content_chunks, mid_summary_chunks, top_summary_chunks = build_2level_summaries(chunks)

    name = pdf_path.rsplit("/")
    file_name = name[-1]
    #  collection 필요시 name[-2]

    # dir 생성
    os.makedirs(chunk_dir, exist_ok=True)
    os.makedirs(chunk_dir + '/content', exist_ok=True)
    os.makedirs(chunk_dir + '/top_summary', exist_ok=True)
    os.makedirs(chunk_dir + '/mid_summary', exist_ok=True)

    # 원문 chunk
    with open(f"{chunk_dir}/content/{file_name}.json", "w", encoding="utf-8") as f:
        json.dump(content_chunks, f, ensure_ascii=False, indent=2)

    # top 요약 chunk
    with open(f"{chunk_dir}/top_summary/{file_name}.json", "w", encoding="utf-8") as f:
        json.dump(top_summary_chunks, f, ensure_ascii=False, indent=2)

    # mid 요약 chunk
    with open(f"{chunk_dir}/mid_summary/{file_name}.json", "w", encoding="utf-8") as f:
        json.dump(mid_summary_chunks, f, ensure_ascii=False, indent=2)

##################################
# collection 필요 시 추후 추가
##################################
# preprocessing 실행
def run_preprocessing(test_dir: str):

    # 1. 작엄 문서 작업할 디렉토리로 copy
    # raw
    # ↓ (copy)
    # staging
    # ↓ (ahk)
    # converted
    # ↓
    # PDF loader
    # convert_docs_in_dir(raw_dir, staging_dir, converted_dir)
     
    # 시작 시간
    start = time.time()
    print(f'### [preprocessing] start')

    for name in os.listdir(converted_dir):
        if '.' not in name:
            continue

        # chunk_file(test_dir + '/' + name)
        # print(f'### {test_dir}/{name}')
    
    print(f'### [preprocessing] end')
    # 종료 시간  
    end = time.time()
    print(f'### [preprocessing] 총 걸린시간: {end-start}초')


# 1. 작엄 문서 작업할 디렉토리로 copy
# convert_docs_in_dir(raw_dir, staging_dir, converted_dir)

document= parse_pdf_for_rag_json(os.path.join(converted_dir , os.listdir(converted_dir)[0]))
# def run_preprocessing(test_dir: str):
#      # 시작 시간
#     start = time.time()
#     print(f'### [preprocessing] start')

#     for name in os.listdir(test_dir):
#         if '.' not in name:
#             continue

#         chunk_file(test_dir + '/' + name)
#         print(f'### {test_dir}/{name}')

#     print(f'### [preprocessing] end')
#     # 종료 시간  
#     end = time.time()
#     print(f'### [preprocessing] 총 걸린시간: {end-start}초')
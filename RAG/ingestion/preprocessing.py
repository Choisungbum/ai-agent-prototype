from ingestion.preprocess.loader.pdf.lib_pymupdf import parse_pdf_for_rag_json
from ingestion.preprocess.chunker.chunking import extract_paragraphs, semantic_chunking_by_section, build_2level_summaries

import json, uuid, os, hashlib
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
chunk_dir = os.path.join(BASE_DIR, "chunk")
test_dir = os.path.join(BASE_DIR, "testfile")

os.makedirs(chunk_dir, exist_ok=True)

def chunk_file(pdf_path):
    # 1. 문서 로드 -> 구조화된 json 데이터로 출력 (텍스트, 표) 
    document= parse_pdf_for_rag_json(pdf_path)

    # 2-1. paragraph 추출 및 heading 결합 (blocks → paragraph, 제목 → 다음 문단에 붙이기)
    paragrephs = extract_paragraphs(document)

    # 2-2. semantic chunking (section 및 title 기준 )
    chunks = semantic_chunking_by_section(paragrephs)

    # 3. summary(top, mid), 원문 chunk 생성
    content_chunks, mid_summary_chunks, top_summary_chunks = build_2level_summaries(chunks)

    name = pdf_path.rsplit("/")
    file_name = name[-1]
    collection_name = name[-2]
    dir_name = name[-3]

    # dir 생성
    os.makedirs(chunk_dir +'/'+ dir_name, exist_ok=True)
    os.makedirs(chunk_dir +'/'+ dir_name +'/'+ collection_name + '/content', exist_ok=True)
    os.makedirs(chunk_dir +'/'+ dir_name +'/'+ collection_name + '/top_summary', exist_ok=True)
    os.makedirs(chunk_dir +'/'+ dir_name +'/'+ collection_name + '/mid_summary', exist_ok=True)

    # 원문 chunk
    with open(f"{chunk_dir}/{dir_name}/{collection_name}/content/{file_name}.json", "w", encoding="utf-8") as f:
        json.dump(content_chunks, f, ensure_ascii=False, indent=2)

    # top 요약 chunk
    with open(f"{chunk_dir}/{dir_name}/{collection_name}/top_summary/{file_name}.json", "w", encoding="utf-8") as f:
        json.dump(top_summary_chunks, f, ensure_ascii=False, indent=2)

    # mid 요약 chunk
    with open(f"{chunk_dir}/{dir_name}/{collection_name}/mid_summary/{file_name}.json", "w", encoding="utf-8") as f:
        json.dump(mid_summary_chunks, f, ensure_ascii=False, indent=2)


    


# 디렉토리 순서
# ext 확장자
# 컬렉션 
exts = ['/pdf']
collections = ['/wiseirag']

# 시작 시간
start = time.time()
print(f'### [preprocessing] start')
for ext in exts:
    for collection in collections:
        full_test_dir = test_dir + ext + collection
        # test 파일 디렉토리 순회하며 파일 open
        for name in os.listdir(full_test_dir):
            if '.' not in name:
                continue

            chunk_file(full_test_dir + '/' + name)
            print(f'### {full_test_dir}/{name}')

print(f'### [preprocessing] end')
# 종료 시간  
end = time.time()
print(f'### [preprocessing] 총 걸린시간: {end-start}초')

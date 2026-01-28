from ingestion.storage.builder import LangChainDocumentBuilder
from ingestion.common.common import db_conn
from ingestion.common.LLMClient import call_llm
import asyncio
import json, uuid, os, hashlib, re, time

# from rich.console import Console
# from rich.markdown import Markdow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
chunk_dir = os.path.join(BASE_DIR, "chunk")


os.makedirs(chunk_dir, exist_ok=True)

# builder
builder = LangChainDocumentBuilder()

# 컬렉션 
collections = ['/wiseirag']

# retriever 파이프라인
# 질의 시 top_summary에 유사한 답이 있으면 mid_summary -> content 까지 검색 흐름을 이어가고
# top_summary에 유사 답변이 없으면 바로 content 검색
def retrieve_pipeline(query: str, collection: str,
                      k_top=5,
                      k_mid=5,
                      k_content=5,
                      top_score_threshold=0.75):
    """
    query
     ↓
    TOP summary 검색 (시도)
     ↓ (의미 있으면)
    MID summary 검색
     ↓
    CONTENT 검색

    ❗ top이 의미 없으면 → CONTENT fallback
    """

    # 1. TOP summary 검색
    top_vs = db_conn(collection + "/top_summary")

    top_docs = top_vs.db.similarity_search_with_score(
        query=query,
        k=k_top
    )

    # score 기준 필터링
    valid_top_docs = [
        d for d, score in top_docs
        if score >= top_score_threshold
    ]

    # top이 의미 없으면 → content 직행 (핵심)
    if not valid_top_docs:
        content_vs = db_conn(collection + "/content")
        return content_vs.db.similarity_search(
            query=query,
            k=k_content,
            filter={"role": {"$in": ["general", "action"]}}
        )

    top_ids = [
        d.metadata.get("summary_id")
        for d in valid_top_docs
        if d.metadata.get("summary_id")
    ]

    # 3. MID summary 검색
    mid_vs = db_conn(collection + "/mid_summary")

    mid_docs = mid_vs.db.similarity_search(
        query=query,
        k=k_mid,
        filter={"parent_id": {"$in": top_ids}}
    )

    mid_ids = [
        d.metadata.get("summary_id")
        for d in mid_docs
        if d.metadata.get("summary_id")
    ]

    # mid도 없으면 content fallback
    if not mid_ids:
        content_vs = db_conn(collection + "/content")
        return content_vs.db.similarity_search(
            query=query,
            k=k_content,
            filter={"role": {"$in": ["general", "action"]}}
        )

    # 4. CONTENT 검색
    content_vs = db_conn(collection + "/content")

    content_docs_with_score = content_vs.db.similarity_search_with_score(
        query=query,
        k=k_content,
        filter={
            "summary_id": {"$in": mid_ids},
            "role": {"$in": ["general", "action"]},
        }
    )

    CONTENT_THRESHOLD = 0.6

    # 5. 검색결과 rerank 검색
    reranked_docs = [
        doc for doc, score in
        sorted(
            (
                (doc, score)
                for doc, score in content_docs_with_score
                if score >= CONTENT_THRESHOLD
            ),
            key=lambda x: x[1],
            reverse=True
        )
    ]

    return reranked_docs



# 결과 태그 제거 
def strip_tags_for_display(text: str) -> str:
    return re.sub(r"\[(ACTION|WISE_iRAG|SECTION_PATH)[^\]]*\]\s*", "", text)


print(f'### input quert')
# LLM 서버 모델 목록
# 관리도구 학습데이터 조회
while True:
    print(f'\n\n\n')
    query = input("")

    if query == "exit":
        break

    if not query:
        continue

    # 시작 시간
    start = time.time()
    print(f'### [retriever] start')

    raw_results = retrieve_pipeline(query, collections[0])

    results = [
        {
            "source": result.metadata.get("source"),
            "page_content": result.page_content,
            "section_title": result.metadata.get("section_title"),
        }
        for result in raw_results
    ]

    print(f'### [retriever] end')
    # 종료 시간  
    end = time.time()
    print(f'### [retriever] 총 걸린시간: {end-start}초')

    # 컨텍스트 및 질의 
    context = ''

    for i, doc in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        page_context = strip_tags_for_display(doc['page_content'])
        # print(strip_tags_for_display(doc.page_content[:300]))
        # print('\n\n')
        print(doc['source'])
        print(page_context)
        # print(doc['pages'])
        # print(doc['section_title'])
        print('\n\n')
        context += f"""
        ### Answer {i}
        {doc['section_title']}

        {page_context}
        """
    print(f'### query: {query}')
    raw_response = asyncio.run(call_llm(query, context))
    response = raw_response['choices'][0]['message']['content']
    print(response)
    
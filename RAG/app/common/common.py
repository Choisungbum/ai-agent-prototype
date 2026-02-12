from app.storage.vectorStoreManager import VectorStoreManager
from app.storage.builder import LangChainDocumentBuilder
from app.loaders.pdf_loader import parse_pdf_for_rag_json
from app.chunkers.chunking import (
    extract_paragraphs,
    semantic_chunking_by_section,
    build_summaries_chunk,
    attach_parent_ids,
)

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres.vectorstores import PGVector
from pathlib import Path
import json, os, re


# ══════════════════════════════════════════════════════
#  공통 경로 설정
# ══════════════════════════════════════════════════════

# common.py 기준 경로:  RAG/app/common/common.py
BASE_DIR = Path(__file__).resolve().parents[2]
# parents[0] = common
# parents[1] = app
# parents[2] = RAG (프로젝트 루트)

raw_dir = os.path.join(BASE_DIR, "raw_dir")                               # 원본 문서가 있는 dir
staging_dir = os.path.join(BASE_DIR, "working_dir", "staging_dir")        # 사용할 파일을 복사해오는 dir
converted_dir = os.path.join(BASE_DIR, "working_dir", "converted_dir")    # 사용할 파일을 변환하는 dir
chunk_dir = os.path.join(BASE_DIR, "chunk")

os.makedirs(chunk_dir, exist_ok=True)

# LangChain Document 빌더 (from_chunks 정적 메서드 사용)
builder = LangChainDocumentBuilder()


# ══════════════════════════════════════════════════════
#  DB 연결 설정
# ══════════════════════════════════════════════════════

# PostgreSQL + PGVector 연결 문자열
connection = 'postgresql+psycopg://langchain:langchain@pgvector-container:5432/langchain'

# HuggingFace 임베딩 모델 (bge-m3)
embedding = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={
        "device": "cpu",
        # HuggingFace 모델이 커스텀 파이썬 코드를 포함하고 있을 때 그걸 허용하는 옵션 
        # 일부 환경에서 필요
        "trust_remote_code": True,   
    },
    encode_kwargs={
        "normalize_embeddings": True,
        # 한 번에 임베딩하는 문서 개수 
        # 문서 많으면 체감 차이 큼
        "batch_size": 16             
    }
)



def db_conn(collection_name: str) -> VectorStoreManager:
    """PGVector 기반 VectorStoreManager 인스턴스를 생성하여 반환한다.

    Args:
        collection_name: Vector DB 컬렉션 이름 (예: '/content', '/summary')

    Returns:
        VectorStoreManager: 해당 컬렉션에 연결된 매니저 객체
    """
    return VectorStoreManager(connection
                              , embedding
                              , collection_name)


# ══════════════════════════════════════════════════════
#  Preprocessing 관련 함수
# ══════════════════════════════════════════════════════

def get_ext(filename):
    """파일명에서 확장자를 추출하여 반환한다. (예: '.pdf')

    Args:
        filename: 확장자를 추출할 파일명 또는 경로

    Returns:
        str: 확장자 문자열 (dot 포함)
    """
    return os.path.splitext(filename)[1]


def chunk_file(pdf_path):
    """PDF 문서를 로드하고 청킹하여 content/summary JSON 파일로 저장한다.

    처리 흐름:
        1. PDF 로드 → 구조화된 JSON 데이터 (텍스트, 표)
        2-1. paragraph 추출 및 heading 결합
        2-2. semantic chunking (section/title 기준) → content chunk
        3-1. summary chunk 생성
        3-2. content ↔ summary 간 parent_id 연결
        4. chunk_dir/content/, chunk_dir/summary/ 에 JSON 저장

    Args:
        pdf_path: 청킹할 PDF 파일의 절대 경로
    """
    ext = get_ext(pdf_path)

    # 지원 예정 포맷 (현재 미구현)
    # elif ext == "docx":
    #     return load_docx(path)
    # elif ext == "hwp":
    #     return load_hwp(path)

    # 1. 문서 로드 → 구조화된 JSON 데이터로 출력 (텍스트, 표)
    if ext == "pdf":
        document= parse_pdf_for_rag_json(pdf_path)

    # 디버그용 원문 JSON 저장 (비활성)
    # with open(f"document.json", "w", encoding="utf-8") as f:
    #     json.dump(document, f, ensure_ascii=False, indent=2)

    # 2-1. paragraph 추출 및 heading 결합 (blocks → paragraph, 제목 → 다음 문단에 붙이기)
    paragrephs = extract_paragraphs(document)

    # 2-2. semantic chunking (section 및 title 기준) content chunk 생성
    content_chunks = semantic_chunking_by_section(paragrephs)

    # 3-1. summary chunk 생성
    summary_chunks, summary_id_map = build_summaries_chunk(content_chunks)

    # 3-2. content → summary parent ID 연결
    content_chunks = attach_parent_ids(content_chunks, summary_id_map)

    name = pdf_path.rsplit("/")
    file_name = name[-1]
    #  collection 필요시 name[-2]

    # 출력 디렉토리 생성
    os.makedirs(chunk_dir, exist_ok=True)
    os.makedirs(chunk_dir + '/content', exist_ok=True)
    os.makedirs(chunk_dir + '/summary', exist_ok=True)

    # 원문 chunk JSON 저장
    with open(f"{chunk_dir}/content/{file_name}.json", "w", encoding="utf-8") as f:
        json.dump(content_chunks, f, ensure_ascii=False, indent=2)

    # 요약 chunk JSON 저장
    with open(f"{chunk_dir}/summary/{file_name}.json", "w", encoding="utf-8") as f:
        json.dump(summary_chunks, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════
#  Embedding 관련 함수
# ══════════════════════════════════════════════════════

def sanitize_text(s: str) -> str:
    """문자열에서 PostgreSQL이 허용하지 않는 제어 문자를 제거한다.

    임베딩 대상 document.page_content 또는 metadata 안에
    \\x00 (NULL byte) 등이 포함되면 PGVector INSERT 시 에러가 발생한다.

    Args:
        s: 정제할 문자열

    Returns:
        str: 제어 문자(\\x00, \\x01, \\x02)가 제거된 문자열
    """
    if not s:
        return s
    return s.replace("\x00", "").replace("\x01", "").replace("\x02", "")


def load_chunks_from_json(chunk_path):
    """JSON 파일에서 chunk 데이터를 로드하여 반환한다.

    Args:
        chunk_path: chunk JSON 파일 경로

    Returns:
        list[dict]: chunk 딕셔너리 리스트
    """
    with open(chunk_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_documents_from_chunk_file(json_path):
    """chunk JSON 파일을 LangChain Document 리스트로 변환한다.

    Args:
        json_path: chunk JSON 파일 경로

    Returns:
        list[Document]: LangChain Document 객체 리스트
    """
    chunks = load_chunks_from_json(json_path)
    return LangChainDocumentBuilder.from_chunks(chunks)


def ingest_chunk_file(json_path, db, vector_type):
    """chunk JSON 파일을 임베딩하여 Vector DB에 저장한다.

    처리 흐름:
        1. JSON → LangChain Document 변환
        2. page_content 텍스트 정제 (NULL byte 제거)
        3. metadata에 vector_type 태깅
        4. DB에 임베딩 + 저장

    Args:
        json_path:    chunk JSON 파일 경로
        db:           VectorStoreManager 인스턴스 (대상 컬렉션)
        vector_type:  메타데이터에 기록할 벡터 유형 ('content' | 'summary')
    """
    docs = build_documents_from_chunk_file(json_path)
    if not docs:
        return

    for d in docs:
        d.page_content = sanitize_text(d.page_content)
        d.metadata["vector_type"] = vector_type

    db.add_documents(docs)
    print(f"[INGESTED] {os.path.basename(json_path)} ({len(docs)} chunks)")


# ══════════════════════════════════════════════════════
#  Retriever 관련 함수
# ══════════════════════════════════════════════════════

def retrieve_pipeline(query: str,
                      k_summary=5,
                      k_content=5,
                      top_score_threshold=0.75):
    """2단계 계층 검색 파이프라인을 실행한다.

    검색 흐름:
        query → summary 검색 → score 필터링 → content 검색 → rerank
        summary에서 유사 답변이 없으면 content로 바로 fallback

    Args:
        query:                사용자 질의 문자열
        k_summary:            summary 검색 시 반환할 상위 문서 수 (기본 5)
        k_content:            content 검색 시 반환할 상위 문서 수 (기본 5)
        top_score_threshold:  summary 유효 판단 기준 score (기본 0.75)

    Returns:
        list[Document]: score 기준 내림차순 정렬된 content Document 리스트
    """

    # 1. summary 검색
    summary_vs = db_conn("/summary")

    summary_docs = summary_vs.db.similarity_search_with_score(
        query=query,
        k=k_summary
    )

    # score 기준 필터링
    valid_top_docs = [
        d for d, score in summary_docs
        if score >= top_score_threshold
    ]

    # summary 의미 없으면 → content 직행 (fallback)
    if not valid_top_docs:
        content_vs = db_conn("/content")
        return content_vs.db.similarity_search(
            query=query,
            k=k_content,
            filter={"role": {"$in": ["general", "action"]}}
        )

    # 2. 유효한 summary의 ID 수집
    summary_ids = [
        d.metadata.get("summary_id")
        for d in valid_top_docs
        if d.metadata.get("summary_id")
    ]

    # 3. summary_id 기반 content 검색
    content_vs = db_conn("/content")

    content_docs_with_score = content_vs.db.similarity_search_with_score(
        query=query,
        k=k_content,
        filter={
            "summary_id": {"$in": summary_ids},
            "role": {"$in": ["general", "action"]},
        }
    )

    CONTENT_THRESHOLD = 0.6

    # 4. score 기준 필터링 + 내림차순 rerank
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


def strip_tags_for_display(text: str) -> str:
    """검색 결과 텍스트에서 내부 태그를 제거한다.

    제거 대상: [ACTION ...], [WISE_iRAG ...], [SECTION_PATH ...]

    Args:
        text: 태그가 포함된 원본 텍스트

    Returns:
        str: 태그가 제거된 텍스트
    """
    return re.sub(r"\[(ACTION|WISE_iRAG|SECTION_PATH)[^\]]*\]\s*", "", text)


def build_context(raw_results):
    """검색 결과를 LLM 프롬프트용 context 문자열로 조립한다.

    각 검색 결과에서 source, page_content, section_title을 추출하고,
    번호 매긴 Answer 형식으로 context를 구성한다.

    Args:
        raw_results: retrieve_pipeline이 반환한 Document 리스트

    Returns:
        tuple[list[dict], str]:
            - results:  source, page_content, section_title 딕셔너리 리스트
            - context:  LLM에 전달할 Answer 형식의 문자열
    """
    results = [
        {
            "source": result.metadata.get("source"),
            "page_content": result.page_content,
            "section_title": result.metadata.get("section_title"),
        }
        for result in raw_results
    ]
    context = ''
    for i, doc in enumerate(results, 1):
        page_context = strip_tags_for_display(doc['page_content'])
        context += f"""
        ### Answer {i}
        {doc['section_title']}

        {page_context}
        """
    return results, context
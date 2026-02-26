# ai-agent-prototype

LangChain 기반 AI Agent와 RAG(Retrieval-Augmented Generation) 파이프라인을 포함한 AI 프로토타입 프로젝트입니다.

---

## 📁 전체 프로젝트 구조

```
ai-agent-prototype/
├── frontend/              # React.js 기반 Chat UI
├── gateway/               # Spring Boot API Gateway
├── agent/                 # Python LangChain Agent (FastAPI)
├── RAG/                   # Python RAG 파이프라인 (FastAPI)
├── RAG_UI/                # React.js 기반 RAG Chat UI
├── mcp-server/            # Spring Boot MCP Server
├── docker-compose.yml     # 전체 컨테이너 정의
└── .env                   # 환경변수 설정
```

### 서비스 구성 요약

| 서비스 | 기술 스택 | 역할 | 포트 |
|---|---|---|---|
| frontend | Node.js (React) | Agent 사용자 UI | 3000 |
| gateway | Spring Boot (Java 17) | 인증/로깅, 요청 중계 | 8080 |
| agent | Python + LangChain + FastAPI | LLM 기반 Tool 호출 / 응답 생성 | 8000 |
| RAG | Python + LangChain + FastAPI | 문서 전처리 / 임베딩 / 검색 | 8001 |
| RAG_UI | Node.js (React) | RAG 사용자 UI | 3001 |
| mcp-server | Spring Boot (Java 17) | 내부 DB/API 연동 Tool 서버 | 9090 |

---

## 🤖 Part 1. Agent

LangChain 기반 ReAct 패턴 에이전트입니다. MCP Server에서 Tool 목록을 받아 LLM이 자율적으로 Tool을 선택하고 호출합니다.

### 아키텍처

```
[User]
  │
  ▼
[Gateway :8080]
  │
  ▼
[Agent :8000]  ──────────────────────────┐
  │  FastAPI + LangChain                  │
  │                                       ▼
  │  ┌─────────────────────────┐    [MCP Server :9090]
  │  │  ReACt + Agentic Loop   │          │  JSON-RPC
  │  │                         │          │  tools/call
  │  │                         │     [PostgreSQL]
  │  │                         │
  │  │  Phase 1: 데이터 수집     │
  │  │  Phase 2: 답변 생성       │
  │  └─────────────────────────┘
  │
  ▼
[Redis]  ← 세션별 대화 이력 / Tool 목록 / 요약 저장
```

### 디렉토리 구조

```
agent/
├── main.py                        # FastAPI 앱 진입점
├── core/
│   └── config.py                  # 환경변수 설정 (pydantic-settings)
├── models/
│   ├── chat_models.py             # Request / Response 스키마
│   ├── chat_memory.py             # Redis 기반 대화 메모리 관리
│   └── makeParam.py               # 파라미터 생성 유틸
├── routers/
│   └── chat_router.py             # /chat, /chat/initialize 엔드포인트
├── services/
│   └── chat_service.py            # 핵심 Agent 로직 (TARL Loop)
├── requirements.txt
└── .env
```

### 핵심 동작 흐름

```
1. POST /chat/initialize
   └─ MCP Server에 initialize 요청 → Tool 목록 조회 → Redis 저장

2. POST /chat
   ├─ [Phase 1] LLM + Agentic Loop
   │    ├─ Redis에서 대화 이력(summary + recent) 로드
   │    ├─ ReAct 프롬프트 구성 (Tool 목록 + History + 사용자 질문)
   │    ├─ LLM 추론 → Action / Action Input 파싱
   │    ├─ MCP Server 호출 (JSON-RPC: tools/call)
   │    ├─ Observation 추가 → 다음 스텝으로 반복
   │    └─ Action: DONE / None 감지 시 루프 종료 (max 10회)
   │
   └─ [Phase 2] 최종 답변 생성
        ├─ 수집된 데이터(collected_data)를 context로 구성
        ├─ 2번째 LLM 호출로 자연어 답변 생성
        └─ Redis에 대화 이력 저장 + 필요 시 요약(summarize_if_needed)
```

### 프롬프트 전략

ReAct 패턴 기반으로 다음 규칙을 적용합니다.

- **언어 분리**: 추론/행동 결정은 영어, 최종 답변은 한국어
- **단일 타겟 원칙**: 한 번에 하나의 대상만 검색 (다중 타겟 시 순차 처리)
- **중복 방지**: `executed_actions` set으로 동일 Tool+파라미터 재호출 차단
- **실패 복구**: 결과 없음(NO_RESULT) 시에도 루프를 멈추지 않고 다음 타겟 진행
- **파라미터 규칙**: 사용자가 명시한 값만 사용, 추측 금지 / 한영 혼용어 원문 그대로 전달

### 대화 메모리 구조 (Redis)

| Key | 내용 |
|---|---|
| `session:{id}:message` | 대화 이력 (role / content / tokens) |
| `session:{id}:summary` | 누적 요약 텍스트 |
| `session:{id}:tools` | 세션에서 사용 가능한 Tool 목록 |
| `session:{id}:token_total` | 누적 토큰 수 |

### API 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| POST | `/chat/initialize` | MCP 연결 초기화 및 Tool 목록 로드 |
| POST | `/chat` | 사용자 메시지 처리 및 응답 반환 |

**Request Header**: `X-Session-Id: {세션 ID}`

### 개발 환경 설정

**요구사항**
- Python 3.11
- Ollama (`llama3.1:8b` 모델)
- Redis
- PostgreSQL (MCP Server용)

---

## 📚 Part 2. RAG

PDF 문서를 수집·전처리·임베딩하여 Vector DB에 저장하고, 사용자 질문에 대해 계층형 검색(summary → content)으로 관련 문서를 찾아 LLM이 답변을 생성하는 파이프라인입니다.

### 아키텍처

```
[문서 투입]              [RAG_UI :3001]
    │                        │
    ▼                        ▼
[RAG :8001]  ◄──── POST /api/retrieve
    │
    ├─ GET  /api/preprocessing   # 문서 변환 + 청킹
    ├─ GET  /api/embedding       # 청크 임베딩 → Vector DB 저장
    └─ POST /api/retrieve        # 검색 + LLM 응답 생성
         │
         ▼
[PGVector (PostgreSQL)]
   ├─ collection: /summary    ← 섹션 요약 벡터
   └─ collection: /content    ← 본문 청크 벡터
```

### 디렉토리 구조

```
RAG/
├── main.py                            # FastAPI 앱 진입점
├── routers/
│   └── router.py                      # /preprocessing, /embedding, /retrieve 엔드포인트
├── service/
│   ├── preprocessing.py               # 전처리 실행 진입점
│   ├── embedding.py                   # 임베딩 실행 진입점
│   └── retriever.py                   # 검색 실행 진입점 (CLI 테스트 포함)
├── loaders/
│   └── pdf_loader.py                  # pdf 문서 로드 
├── chunkers/
│   └── chunking.py                    # 청킹 / 요약 청크 생성
├── storage/
│   ├── vectorStoreManager.py          # PGVector 연결 및 저장 관리
│   └── builder.py                     # LangChain Document 객체 빌더
├── common/
│   ├── common.py                      # 공통 경로 / DB 연결 / 전처리·임베딩·검색 함수
│   └── LLMClient.py                   # Ollama LLM 호출 클라이언트
├── raw_dir/                           # 원본 문서 투입 디렉토리
├── working_dir/
│   ├── staging_dir/                   # 변환 대기 중간 디렉토리
│   └── converted_dir/                 # 변환 완료 PDF 저장 디렉토리
├── chunk/
│   ├── content/                       # 본문 청크 JSON
│   └── summary/                       # 요약 청크 JSON
├── requirements.txt
└── .env
```

### 핵심 동작 흐름

#### Step 1. 전처리 (Preprocessing)

```
raw_dir/  (원본 문서: PDF, DOCX 등)
    │
    ▼  LibreOffice 자동 변환 (DOCX → PDF)
converted_dir/
    │
    ▼  PDF Loader (PyMuPDF / pdfplumber)
구조화된 JSON (doc_id, source, sections, blocks)
    │
    ├─ extract_paragraphs()       # block → paragraph 분해, 제목 병합
    ├─ semantic_chunking_by_section()  # section 기준 의미 단위 청킹 (max 1000자, overlap 150자)
    ├─ build_summaries_chunk()    # 섹션 계층 구조 기반 summary 청크 생성
    └─ attach_parent_ids()        # content ↔ summary 간 parent_id 연결
         │
         ▼
chunk/content/{filename}.json    # 본문 청크
chunk/summary/{filename}.json    # 요약 청크
```

#### Step 2. 임베딩 (Embedding)

```
chunk/content/*.json  +  chunk/summary/*.json
    │
    ▼  LangChain Document 빌드 (LangChainDocumentBuilder)
    │  NULL byte 정제 (sanitize_text)
    │  vector_type 메타데이터 태깅 ('content' | 'summary')
    ▼
PGVector
    ├─ collection: rag_test  (content 벡터)
    └─ collection: /summary  (summary 벡터)

임베딩 모델: BAAI/bge-m3 (HuggingFace, CUDA, normalize=True, batch=16)
```

#### Step 3. 검색 + 답변 생성 (Retrieve)

```
[사용자 질문]
    │
    ▼
summary 검색 (k=5, score ≥ 0.75 필터링)
    │
    ├─ 유효 summary 없음 → content 직행 fallback
    │
    └─ 유효 summary 있음
          │
          ▼
         summary_id 기반 content 검색 (k=5)
          │  role 필터: general | action
          │  score ≥ 0.60 필터링
          │  score 내림차순 rerank
          ▼
         context 조립 (build_context)
          │  "### Answer N / section_title / page_content"
          ▼
         LLM 호출 (Ollama: llama3.1:8b)
          │  Context에 있는 Answer만 선택해서 답변
          ▼
        [응답 반환: response + sources + elapsed_sec]
```

### 청킹 전략

청크에 role 태그를 부여하여 검색 품질을 높입니다.

| role | 조건 | 설명 |
|---|---|---|
| `action` | "삭제", "생성", "수정" 등 키워드 포함 | 실행 관련 단계 설명 |
| `general` | 그 외 | 일반 설명 본문 |
| `summary` | build_summaries_chunk 생성 | 섹션 계층 구조 요약 |

각 청크의 텍스트 구조 예시:
```
[SECTION_PATH]1. 설치 > 1.1. 환경 구성
[ACTION]
환경 구성을 위해 다음 명령어를 실행합니다.
...
```

### RAG_UI

RAG API와 연동되는 React 기반 채팅 UI입니다.

```
RAG_UI/
├── main.jsx
├── App.jsx
├── components/
│   ├── ChatLayout.jsx    # 전체 레이아웃 (메시지 목록 + 입력창)
│   ├── ChatInput.jsx     # 메시지 입력 컴포넌트
│   ├── MessageList.jsx   # 메시지 목록 렌더링
│   └── MessageItem.jsx   # 단일 메시지 렌더링
└── hooks/
    ├── sendMessageHook.js   # 메시지 전송 / 스트리밍 처리
    └── scrollHook.js        # 자동 스크롤 / 최신 메시지 이동
```

### API 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/preprocessing` | 문서 변환 및 청킹 실행 |
| GET | `/api/embedding` | 청크 임베딩 및 Vector DB 저장 |
| POST | `/api/retrieve` | 검색 + LLM 답변 생성 |

**Retrieve Request / Response**
```json
// Request
{ "query": "설치 방법을 알려줘" }

// Response
{
  "query": "설치 방법을 알려줘",
  "response": "설치는 다음 단계로 진행합니다...",
  "sources": [
    { "source": "manual.pdf", "section_title": "1.1. 환경 구성", "page_content": "..." }
  ],
  "elapsed_sec": 3.42
}
```

### 개발 환경 설정

**요구사항**
- Python 3.11
- CUDA 지원 GPU (bge-m3 임베딩 모델용)
- PostgreSQL + pgvector extension
- Ollama (`llama3.1:8b` 모델)

---

## 🗄️ DB 및 LLM

### PostgreSQL

**MCP Server용 Tool 관리 테이블**

```sql
CREATE TABLE tool_info (
    tool_id      SERIAL PRIMARY KEY,
    tool_name    VARCHAR(100) UNIQUE NOT NULL,   -- Tool 이름 (예: select_user)
    tool_desc    VARCHAR(255),                   -- Tool 설명
    tool_type    VARCHAR(50)  DEFAULT 'DB',      -- Tool 유형 (DB, API 등)
    exec_target  TEXT         NOT NULL,          -- 실행 대상 (SQL / Mapper.method / API URL)
    query_params JSONB        DEFAULT '[]',      -- 조건으로 사용 가능한 컬럼 목록
    enabled      CHAR(1)      DEFAULT 'Y'        -- 사용 여부
);
```

**RAG용 Vector DB** (pgvector extension 필요)

```sql
-- LangChain PGVector가 자동 생성
-- collection: /content  (본문 청크 벡터)
-- collection: /summary  (요약 청크 벡터)
```

### LLM

| 모델 | 용도 | 비고 |
|---|---|---|
| `llama3.1:8b` (Ollama) | Agent Tool 호출 / 답변 생성 | |
| `llama3.1:8b` (Ollama) | RAG 검색 답변 생성 |  |
| `BAAI/bge-m3` (HuggingFace) | 문서 임베딩 | CUDA GPU 필요 |

---

---

## 🔧 Frontend (React Chat UI)

**개발 환경**
- Node.js 20.x 이상 (LTS) — https://nodejs.org
- npm (Node.js 설치 시 자동 포함)

**실행 방법**
```bash
cd frontend
npm install
PORT=3000 npm start
```

---

## ⚙️ Gateway (Spring Boot)

**개발 환경**
- JDK 17+
- Maven 3.9.x
- Spring Boot 3.5.7

**주요 역할**
- 사용자 인증 및 요청 로깅
- Frontend → Agent / RAG 요청 중계
- `X-Session-Id` 헤더 처리

---

## 🛠️ MCP Server (Spring Boot)

**개발 환경**
- JDK 17+
- Maven 3.9.x
- Spring Boot 3.5.7

**주요 역할**
- JSON-RPC 2.0 프로토콜 기반 Tool 서버
- `initialize`: 사용 가능한 Tool 목록 반환
- `tools/list`: Tool 목록 조회
- `tools/call`: Tool 실행 (DB 조회 / API 호출)

---

## ✅ TODO

### Agent
- [ ] Tool 호출 실패 시 재시도 로직 추가
- [ ] 토큰 사용량 모니터링 대시보드 연동
- [ ] MCP Tool 동적 등록 기능 구현

### RAG
- [ ] Reranker 모델 도입 (Cross-Encoder 등)
- [ ] 스트리밍 응답 지원 (RAG_UI 스트리밍 수신 구현 연계)
- [ ] 청크 메타데이터 기반 필터 UI 제공

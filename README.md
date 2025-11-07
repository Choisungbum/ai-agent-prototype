# ai-agent-prototype
ai-agent-prototype 생성

# 전체 구성 요약
**서비스	주요 기술	역할**
- frontend	Node.js (React)	사용자 UI
- gateway	Spring Boot (Java 17)	인증/로그, 요청 중계
- agent	Python + LangChain + FastAPI	LLM 기반 Tool 호출/응답 생성
- mcp-server	Spring Boot (Java 17)	내부 DB/API 연동 Tool 서버

**전체구조**
```
ai-agent-prototype/
├─ frontend/           # React.js 기반 Chat UI
├─ gateway/            # Spring Boot API Gateway
├─ agent/              # Python LangChain Agent
├─ mcp-server/         # Spring Boot MCP Server
├─ docker-compose.yml  # 전체 컨테이너 정의
└─ .env                # 환경변수 설정
```

---

## Frontend (React.js)
개발환경
- Node.js 24.11.0
  - https://nodejs.org에서 LTS 버전 (예: 20.x 이상) 설치)
  - npm 자동설치
- PORT=3000 npm start
- port : 3000

## Gateway (Spring Boot API Gateway)
개발환경
- JDK 17+
- Maven 또는 Gradle (Maven 기준 예시) - 3.9.x
- Spring Boot 3.5.7
- port : 8080

## Agent (FastAPI + langchain + LLM)
개발환경
- python 3.11
- vscode(개발 및 디버깅 실행 가능)
- FastAPI
- langchain (1.0.3 버전 사용, 구버전과 라이브러리 호출방식이 다름)
- llama3(ollama)
- 실행 디렉토리에 venv 생성 및 실행
  - python -m venv venv (가상환경생성)
  - venv\Scripts\activate (가상환경실행)
- 필요한 라이브러리 다운 (requirements.txt 파일에 리스트형식으로 저장된 것을 설치)
  - pip install -r requirements.txt
- port : 8000

## MCP Server 
개발환경
- JDK 17+
- Maven 또는 Gradle (Maven 기준 예시) - 3.9.x
- Spring Boot 3.5.7
- port : 9090

## DB & LLM
### DB
- PostgreSQL
- tool table
```SQL
  CREATE TABLE tool_info (
    tool_id SERIAL PRIMARY KEY,                           -- 고유 ID (자동 증가)
    tool_name VARCHAR(100) UNIQUE NOT NULL,               -- Tool 이름 (예: select_user)
    tool_desc VARCHAR(255),                               -- Tool 설명
    tool_type VARCHAR(50) DEFAULT 'DB',                   -- Tool 유형 (DB, API 등)
    exec_target TEXT NOT NULL,                            -- 실행 대상(SQL문 / Mapper.method / API URL)
    query_params JSONB DEFAULT '[]'::jsonb,               -- 조건으로 사용 가능한 컬럼 목록
    enabled CHAR(1) DEFAULT 'Y'                          -- 사용 여부
);

```

### LLM
- ollama - llama3:8b (6GB GPU 메모리에서 사용하기 적합) 



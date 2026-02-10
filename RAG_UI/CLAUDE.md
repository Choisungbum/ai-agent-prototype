# CLAUDE.md

이 파일은 이 저장소에서 작업할 때 **Claude Code가 따라야 할 가이드**를 정의한다.

---

## 프로젝트 개요

이 프로젝트는 **RAG(Retrieval-Augmented Generation)를 사용하는 프론트엔드 UI 프로토타입**이다.

- **React + JavaScript** 기반
- **ChatGPT와 유사한 채팅형 생성형 AI UI**
- 사용자는 채팅 형태로 질의하고, RAG 기반으로 생성된 응답을 확인한다
- UI 목적의 저장소이며, **백엔드는 포함되지 않는다**

백엔드는 이미 구현되어 있는 **FastAPI 기반 Python 서버**이며,  
프론트엔드는 해당 백엔드와 **REST API 방식으로 통신**하는 구조를 전제로 한다.  
(현재는 mock/streaming 응답을 사용 중이며 실제 API 연동은 미완)

---

## 기술 스택

- Frontend: React 19 (함수형 컴포넌트, hooks만 사용)
- Language: JavaScript / JSX (TypeScript 미사용)
- Build Tool: Vite (SWC 사용, Babel 아님)
- Styling: Plain CSS (CSS-in-JS, 전처리기 사용 안 함)
- Lint: ESLint 9 (flat config)
- Backend: FastAPI (Python, 별도 프로젝트)

---

## 아키텍처 개요

### 컴포넌트 구조

App
└─ ChatLayout
├─ MessageList
│ └─ MessageItem[]
└─ ChatInput

- `ChatLayout`이 전체 상태를 관리한다
- `messages`, `isTyping` 등의 상태는 `useState`로 관리
- Context API나 외부 상태 관리 라이브러리는 사용하지 않는다

### 메시지 데이터 구조

```js
{
  role: "user" | "assistant",
  content: string
}

스트리밍 방식
- 빈 assistant 메시지를 먼저 추가
- 이후 setInterval 기반으로 글자를 하나씩 누적
- setMessages의 functional updater 패턴 사용

커스텀 훅 (src/hooks/)
- useChatScroll
  - 자동 스크롤 + 사용자 수동 스크롤 감지
  - useRef 기반 DOM 제어

- sendMessageFunc
  - 메시지 전송 및 mock 스트리밍 처리
  - 이름은 함수처럼 보이지만 실제로는 hook처럼 사용됨

### 프로젝트 목표
RAG UI 구현
- ChatGPT 스타일의 채팅형 인터페이스 제공
- 인스타그램 수준의 세련되고 깔끔한 UI
- 빠른 실험과 프로토타이핑
- 코드 가독성 최우선

### UI / UX 방향성
- 채팅 기반 인터페이스
- 사용자 메시지 / AI 응답의 명확한 구분
- 미니멀하고 정돈된 레이아웃
- 불필요한 UI 요소 배제
- 부드러운 인터랙션과 전환 효과

### Claude 사용 규칙 (중요)
- ❗ Claude와의 모든 대화는 반드시 한글로 진행한다
- ❌ 불필요한 리팩토링 금지
- ✅ 목적이 명확한 수정만 수행
- ✅ 코드 수정 시 반드시 다음을 명확히 설명할 것:
  - 변경된 파일 목록
  - 변경 이유

- ❌ 요청하지 않은 파일 수정 금지
- ✅ 기존 프로젝트 구조와 스타일을 존중할 것

### 작업 방식 가이드
- 한 번에 과도한 변경을 하지 않는다
- 단계별로 확인하면서 작업한다
- 추측 기반 변경은 하지 않는다
- 필요한 경우 먼저 질문하고 작업한다

### 명령어
npm run dev       # Vite 개발 서버 실행 (HMR)
npm run build     # 프로덕션 빌드
npm run lint      # ESLint 실행
npm run preview   # 빌드 결과 미리보기
테스트 러너는 현재 설정되어 있지 않다.

---

## 지금 해야 할 것 (아주 짧게)

1. 이 내용으로 `CLAUDE.md` **전체 덮어쓰기**
2. 저장
3. Claude에게 한 번만 확인 질문:

이 프로젝트의 목표와 Claude 사용 규칙을 요약해줘

→ **한글로**,  
→ **RAG UI / 불필요한 리팩토링 금지 / UI 목표** 나오면 완료.

이제 이 프로젝트는  
**“한글로 대화하는 RAG UI 전담 Claude” 상태**다.
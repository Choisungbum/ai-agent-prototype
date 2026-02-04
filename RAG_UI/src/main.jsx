import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'


// RAG_UI/
// 1. 디렉터리 구조
// ├─ node_modules/        # 라이브러리들 (신경 X)
// ├─ public/              # 정적 파일 (아이콘, 이미지)
// ├─ src/                 # ⭐ 우리가 거의 전부 다룰 곳
// │  ├─ main.jsx          # React 시작점
// │  ├─ App.jsx           # 메인 화면 컴포넌트
// │  ├─ index.css         # 전역 CSS
// │  └─ assets/           # 이미지 등
// ├─ index.html           # 브라우저 진입 HTML
// ├─ package.json         # 프로젝트 설정/스크립트
// └─ vite.config.js       # Vite 설정

// 2. props 
// 부모 컴포넌트가 자식에게 내려주는 “읽기 전용 데이터”
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

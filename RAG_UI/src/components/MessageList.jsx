import {useEffect, useRef, useState} from "react"
import MessageItem from "./MessageItem";

// useEffect = “렌더링이 끝난 뒤 실행되는 코드”
// 1. 역할
// DOM 조작
// 스크롤 이동
// API 호출

// 2. 실행 시점
// 컴포넌트 최초 렌더
// messages state 변경

function MessageList({ messages, isTyping }) {
    
    return (
        // <> </> 는 React Fragment
        // 불필요한 div를 만들지 않고
        // 여러 JSX 요소를 한 번에 반환하기 위해 쓰는 껍데기
        // DOM에는 아무것도 생성 안 됨
        <>
            {messages.map((msg, index) => (
            <MessageItem
                key={index}
                role={msg.role}
                content={msg.content}
            />
            ))}

            {/* assistant typing 표시 */}
            {/* {
                isTyping && (
                <div className="msg-row left">
                    <div className="bubble assistant">
                    <span className="typing">
                        <span className="dot"></span>
                        <span className="dot"></span>
                        <span className="dot"></span>
                    </span>
                    </div>
                </div>
            )} */}
        </>
    );
}

export default MessageList;
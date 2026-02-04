import {useState} from "react"
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";
import { useChatScroll, sendMessageFunc } from "../hooks/scrollHook";

function ChatLayout() {
    // 메시지 상태 및 입력 대기 상태
    const [messages, setMessages] = useState([
        { role: "assistant", content: "안녕하세요, 무엇을 도와드릴까요?" }
    ]);
    const [isTyping, setIsTyping] = useState(false);

    // 스크롤 관련 custom hook 사용
    const {
        autoScroll,
        bottomRef,
        containerRef,
        handleScroll,
        scrollToBottom
    } = useChatScroll(messages, isTyping);

    const {
         // 핸들러 함수
         appendAssistantContent,
         streamAssistantMessage,
         handleSendMessage
    } = sendMessageFunc(messages, isTyping);

    return (
        <div className="app-container">
            <div className="chat-wrapper">
                <header className="chat-header">
                RAG 응답 출력
                </header>

                <div className="chat-main"
                 ref={containerRef}
                 onScroll={handleScroll}     
                >
                    <MessageList messages={messages} isTyping={isTyping} />

                    {/* 스크롤 기준점 */}
                    <div ref={bottomRef} />
                </div>
                    {/* 최신 메시지로 이동 */}
                    {!autoScroll && (
                        <button
                            className="scroll-to-bottom"
                            onClick={scrollToBottom}
                        >
                            ↓ 최근 메세지
                        </button>
                    )}

                <footer className="chat-footer">
                <ChatInput onSend={handleSendMessage} />
                </footer>
            </div>
        </div>
  );
}

export default ChatLayout;
import { useState } from "react";

function ChatInput({ onSend }) {
    const [text, setText] = useState("");

    const handleSend = () => {
        if (!text.trim()) return;
    
        onSend(text);
        setText("");
    }


    return(
        <div className="input-row">
            <input
                className="chat-input"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="메시지를 입력하세요"
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
            />
            <button className=" send-button" onClick={handleSend}>
                전송
            </button>
            </div>
        );
}

export default ChatInput;
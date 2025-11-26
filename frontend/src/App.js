import React, {useState, useEffect} from "react";
import "./App.css";
import {sendToAgent} from "./api.js";

function App(){
  const [messages, setMessages] = useState([
    { sender: "bot", text: "안녕하세요. 무엇을 도와드릴까요?"}
  ]);

  const [input, setInput] = useState("");
  const [currentSessionId, setCurrentSessionId] = useState("");

  // 세션 초기화
  useEffect(() => {
    const initializeSession = async () => {
      console.log("세션 초기화");

      // gateway 에서 ID를 응답해줘야함
      const initialResponse = await sendToAgent("SESSION_INIT"); // 최초 요청
      const newSessionId = initialResponse || 'temp-session-' + Date.now();
  
      setCurrentSessionId(newSessionId.session);
      console.log("세션 ID 설정 완료: ", newSessionId.session);
    };
    
    if (!currentSessionId) {
      initializeSession();
    }
  }, []) // 빈 배열 -> 마운트 시 한 번만 실행

  const sendMessage = async() => {
    if(!input.trim() || !currentSessionId) return;
    setInput("");

    const newMessage = {sender: "user", text: input};
    setMessages([...messages, newMessage]);
  
    // gateway 전달

    const answer = await sendToAgent(input, currentSessionId);
    const response = {text: answer.response};
    setMessages([...messages,newMessage, { sender: "bot", text: response.text}]);
    
  }


return (
  <div className="chat-container">
    <div className="chat-box">
      {messages.map((m, i) => (
        <div key={i} className={`message ${m.sender}`}>
          {m.text}
        </div>
      ))}
  </div>
  <div className="input-box">
    <input 
    value={input}
    onChange={(e) => setInput(e.target.value)}
    onKeyDown={(e) => e.key === "Enter" && sendMessage()}
    placeholder="메시지를 입력하세요..."
    />
    <button onClick={sendMessage}>보내기</button>
    </div>
  </div>
  );
};

export default App;
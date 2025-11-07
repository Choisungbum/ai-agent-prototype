import React, {useState} from "react";
import "./App.css";
import {sendToAgent} from "./api.js";

function App(){
  const [messages, setMessages] = useState([
    { sender: "bot", text: "안녕하세요. 무엇을 도와드릴까요?"}
  ]);

  const [input, setInput] = useState("");

  const sendMessage = async() => {
    if(!input.trim()) return;
    setInput("");

    const newMessage = {sender: "user", text: input};
    setMessages([...messages, newMessage]);
  
    // gateway 전달

    const answer = await sendToAgent(input);
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
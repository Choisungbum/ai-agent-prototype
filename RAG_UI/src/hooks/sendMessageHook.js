import {useEffect, useRef, useState} from "react"

// 스크롤 관리 custom hook
export function sendMessageFunc(messages, isTyping, setMessages, setIsTyping) {
    // 응답 스트리밍 출력 updater
  const appendAssistantContent = (chunk) => {
      setMessages(prev => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;
    
        updated[lastIndex] = {
          ...updated[lastIndex],
          content: updated[lastIndex].content + chunk,
        };
    
        return updated;
      });
    };

  // mock 스트리밍
  const streamAssistantMessage = (fullText) => {
      setIsTyping(true);
    
      // assistant 메시지 먼저 생성
      setMessages(prev => [
        ...prev,
        { role: "assistant", content: "" }
      ]);
    
      let i = 0;
    
      const interval = setInterval(() => {
        appendAssistantContent(fullText[i]);
        i++;
    
        if (i >= fullText.length) {
          clearInterval(interval);
          setIsTyping(false);
        }
      }, 40);
  };

  // 메시지 전송 핸들러
  const handleSendMessage = (text) => {
      // 사용자 메시지 추가
      setMessages(prevMessages => [
          ...prevMessages,
          { role: "user", content: text }
      ]);

      // assistant typing 효과 시작
      setIsTyping(true);

      // 스트리밍 응답
      streamAssistantMessage("이건 스트리밍으로 출력되는 답변입니다.");
  };


  return {
      // 핸들러 함수
      appendAssistantContent,
      streamAssistantMessage,
      handleSendMessage
  };
}

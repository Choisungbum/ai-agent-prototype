import {useEffect, useRef, useState} from "react"

// 스크롤 관리 custom hook
export function useChatScroll(messages, isTyping) {
    // 자동 스크롤 상태
    const [autoScroll, setAutoScroll] = useState(true);

    // DOM 참조
    const bottomRef = useRef(null);
    const containerRef = useRef(null);
    const isAutoScrollingRef = useRef(false);

    // 스크롤 이벤트 핸들러
    const handleScroll = () => {
        const el = containerRef.current;
        if (!el) return;
      
        const distanceFromBottom =
          el.scrollHeight - el.scrollTop - el.clientHeight;
      
        if (isAutoScrollingRef.current) {
          if (distanceFromBottom <= 40) return;
          isAutoScrollingRef.current = false;
        }
      
        setAutoScroll(distanceFromBottom < 10);
    };
      

    // 최신 메시지로 스크롤 이동
    const scrollToBottom = () => {
        isAutoScrollingRef.current = true;

        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
        setAutoScroll(true);

        // smooth scroll 끝날 시간 후 해제
        setTimeout(() => {
            isAutoScrollingRef.current = false;
        }, 300);
    };

    // useRef = DOM을 직접 가리키는 포인터
    // bottomRef.current = 실제 DOM 요소
    useEffect(() => {
        if (!autoScroll) return;

        isAutoScrollingRef.current = true;

        // scrollIntoView({ behavior: "smooth" }); -> 이 요소가 보이도록 부모 스크롤 컨테이너를 움직여라
        bottomRef.current?.scrollIntoView({behavior: "smooth"});

        const timer = setTimeout(() => {
            isAutoScrollingRef.current = false;
        }, 300);
        
        return () => clearTimeout(timer);

    }, [messages, isTyping, autoScroll]);

    return {
        // 상태
        autoScroll,
        
        // DOM 참조
        bottomRef,
        containerRef,
        
        // 핸들러 함수
        handleScroll,
        scrollToBottom
    };
}

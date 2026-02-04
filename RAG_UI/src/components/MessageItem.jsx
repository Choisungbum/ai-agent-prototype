function MessageItem({ role, content }) {
    const isUser = role === "user";


    return(
        <div className  ={`msg-row ${isUser ? "right" : "left"}`}>
            <div className={`bubble ${isUser ? "user" : "assistant"}`}>
                {content}
            </div>
    </div>
  );
}

export default MessageItem;
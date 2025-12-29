export const sendToAgent = async(userMessage, sessionId) => {
  try{
    const response = await fetch(process.env.REACT_APP_GATEWAY_URL + "/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json",
        "X-Session-ID": sessionId
       },
      body: JSON.stringify({ message: userMessage }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();

  }catch (error) {
    console.error("Failed to fetch user data:", error);
    // 에러 발생 시 null이나 빈 객체 등을 반환할 수 있습니다.
    return null;
  }  
}
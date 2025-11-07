export const sendToAgent = async(userMessage) => {
  try{
    const response = await fetch("http://localhost:8080/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
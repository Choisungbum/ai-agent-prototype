from fastapi import APIRouter, HTTPException, Header, Response, status
from app.models.chat_models import ChatRequest, ChatResponse
from app.services.chat_service import process_chat
from app.services.chat_service import initialize
from fastapi import Request
import json


# langSmith 
# from app.services.chat_langSmith_service import process_chat_llama3
# from app.services.chat_langSmith_service import get_tool_list

# langFuse .evn 로드 후 호출
# () 괄호 안에 아무런 인자(argument)를 넣지 않으면, Langfuse 클래스는 자동으로 시스템 환경 변수에서 
# LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY라는 이름의 변수를 찾아서 자신을 설정합니다.


router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("")
async def chat(request: ChatRequest
               , x_session_id: str = Header(None)) -> ChatResponse:
    """
    사용자 메시지를 받아 처리 후 응답을 반환하는 API
    """
    sessionId = x_session_id
    response_text = await process_chat(request.message, sessionId)
    return ChatResponse(response=response_text)
        
@router.post("/initialize")
async def chatInitialize(x_session_id: str = Header(None)):
    sessionId = x_session_id
    response_text = await initialize(sessionId)
    return Response(status_code=status.HTTP_200_OK)
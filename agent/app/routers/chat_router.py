from fastapi import APIRouter
from app.models.chat_models import ChatRequest, ChatResponse
from app.services.chat_service import process_chat
from app.services.chat_service import get_tool_list

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("")
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    사용자 메시지를 받아 처리 후 응답을 반환하는 API
    """
    response_text = await process_chat(request.message)
    return ChatResponse(response=response_text)
    
@router.get("/getToolList")
async def gettoolList() -> str:
    """
    사용자 메시지를 받아 처리 후 응답을 반환하는 API
    """
    response_text = await get_tool_list()
    return response_text
    
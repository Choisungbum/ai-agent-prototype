from fastapi import APIRouter
from app.models.chat_models import ChatRequest, ChatResponse
import os
import logging
from dotenv import load_dotenv

from app.services.chat_service import process_chat

# LangFuse v3
from langfuse import get_client

# .env 먼저 로드
load_dotenv()

# OSS LangFuse 서버용 클라이언트 생성
langfuse = get_client()

router = APIRouter(prefix="/chat", tags=["Chat"])


# ======================================
#  Chat Endpoint (LangFuse v3 방식)
# ======================================
@router.post("")
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    user_id = getattr(request, "user_id", "sungbum")

    # 루트 span (이게 사실상 trace 역할)
    with langfuse.start_as_current_span(
        name="chat-endpoint",
        input={"message": request.message},
    ) as span:

        # trace 정보 업데이트 (v3에서 trace는 update_trace로 관리)
        span.update_trace(
            user_id=user_id,
            metadata={"tags": ["chat", "llama3"]}
        )

        # LLM 호출 generation
        with langfuse.start_as_current_generation(
            name="llama3-generation",
            model=os.getenv("LLM_MODEL"),
            input=request.message
        ) as gen:
            try:
                response_text = await process_chat(request.message)
                gen.update(output=response_text)

            except Exception as e:
                logging.error(f"[CHAT ERROR] {e}")
                gen.update(level="ERROR", status_message=str(e))
                span.update(level="ERROR", status_message=str(e))
                return ChatResponse(response=f"An error occurred: {str(e)}")

        # 전체 결과를 span에 기록
        span.update(output={"response": response_text})

        return ChatResponse(response=response_text)



# ======================================
#  Tool List Endpoint (LangFuse v3)
# ======================================
@router.get("/getToolList")
async def gettoolList() -> str:

    with langfuse.start_as_current_span(
        name="get-tool-list",
        input={"comment": "Fetching tool list"},
    ) as span:

        span.update_trace(
            user_id="system-call",
            metadata={"tags": ["tools"]}
        )

        try:
            response_text = await get_tool_list()
            span.update(output={"tool_list": response_text})
            return response_text

        except Exception as e:
            logging.error(f"[GET TOOL LIST ERROR] {e}")
            span.update(level="ERROR", status_message=str(e))
            return f"An error occurred: {str(e)}"
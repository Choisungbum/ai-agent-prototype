import os
from dotenv import load_dotenv
import json
import httpx  # ◀= 'requests' 대신 비동기 'httpx' 사용 권장
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langsmith.run_helpers import traceable  # ◀= @traceable 임포트

load_dotenv()

# --- 1. LangSmith 환경 변수 설정 ---
# .env 파일에 정의

# --- 2. (가상) MCP 서버 URL 및 get_tool_list 정의 ---
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")  #

@traceable  # ◀= LangSmith가 이 함수 실행을 추적
async def get_tool_list() -> str:
    """
    (LangSmith 추적 예시) 툴 리스트를 비동기로 가져옵니다.
    """
    print("... (Traceable) 툴 리스트 가져오는 중 ...")
    # 실제로는 DB 조회나 API 호출 로직이 들어갑니다.
    return """
    [
        {"toolName": "get_user_info", "toolType": "DB_MAPPER", "description": "사용자 이름, 성별, 나이로 사용자 정보 조회"},
        {"toolName": "get_weather", "toolType": "API", "description": "특정 도시의 현재 날씨 조회"}
    ]
    """

@traceable  # ◀= LangSmith가 이 API 호출을 추적
async def call_mcp_server(tool_name: str, tool_type: str, params: dict) -> httpx.Response:
    """
    (LangSmith 추적을 위해 API 호출을 별도 async 함수로 분리)
    'requests' 대신 'httpx'를 사용하여 비동기 호출
    """
    print("... (Traceable) MCP 서버 비동기 호출 중 ...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MCP_SERVER_URL}/tools/invoke",
            json={"toolName": tool_name, "toolType": tool_type, "reqParams": params},
            headers={"Content-Type": "application/json"}
        )
    return response

# --- 3. 메인 함수 수정 ---

@traceable(run_type="chain")  # ◀= 전체 함수를 "chain" 타입의 상위 실행으로 묶음
async def process_chat_llama3(message: str) -> str:
    """
    사용자 입력을 받아 단순히 가공하여 응답 반환 (LangSmith 추적 적용됨)
    """

    print("---------process_chat start---------")

    # tool list 호출 (이제 LangSmith에 의해 추적됨)
    tool_list_text = await get_tool_list()
    print(f"tool list 호출 \n{tool_list_text}")
    print(f"message 호출 \n{message}")

    # 로컬 LLM 사용
    # (환경 변수가 설정되어 이 LLM 호출은 자동으로 LangSmith에 추적됨)
    llm = ChatOllama(
        model=os.getenv("LLM_MODEL"),
        base_url="http://localhost:11434",
        system=(
            "You are an AI agent that responds to the user..\n"
            "Rules:\n"
            "- Do NOT analyze the given code or text.\n"
            "- You must only follow the instructions below.\n"
            "- Respond in Korean.\n"
            "- Output ONLY the JSON response requested, nothing else.\n"
        ), options={
            "temperature": 0,
            "num_ctx": 8192,
            "top_p": 0.9,
            "repeat_penalty": 1.05
        }
    )

    # 프롬프트 템플릿
    prompt = PromptTemplate.from_template(
        """
        너는 사용자의 질문을 분석하여 JSON 객체를 반환하는 AI 도우미야.
        반드시 아래 규칙을 **엄격히** 지켜.

        ## 규칙
        1. 오직 JSON 형식만 출력해. (불필요한 문장, 설명, 말투 모두 금지)
        2. JSON 외 텍스트, 코드블록 마크다운(`````, ```json``` 등)도 절대 출력하지 마.
        3. 사용자의 질문과 아래 함수 리스트를 비교해 가장 관련 있는 함수를 선택 후 "result": "0".
        4. 질문에서 추출할 수 있는 값만 queryParams에 넣어.
        5. 함수 설명이 없거나 매칭이 불분명하면, `"result": "-1"` 형식으로 출력해.
        6. **한 번에 하나의 JSON만 출력.**

        ## 함수 리스트
        {tool_list_text}

        ## 출력 형식 예시
        {{
            "toolName": "get_user_info",
            "toolType": "DB_MAPPER",
            "queryParams": {{
                "name": "홍길동",
                "gender": "M",
                "age": 30
            }},
            "result": "0"
        }}

        ## 사용자 질문
        {question}

        ## 출력
        오직 JSON 형식으로만 응답해.
        """
    )

    # 체인 생성 (이 체인 실행은 자동으로 LangSmith에 추적됨)
    chain = prompt | llm | StrOutputParser()

    # LLM 실행 -> 어떤 Tool을 써야하는지 판단
    llm_result = await chain.ainvoke({
        "question": message,
        "tool_list_text": tool_list_text
    })

    print(f"[LLM 응답] {llm_result}")

    # 결과 파싱 -> 실제 MCP 호출
    try:
        parsed = json.loads(llm_result)
        if (parsed["result"] == '0'):
            if "toolName" in parsed:
                
                # ◀= 'requests.post' 대신 @traceable 함수 호출로 변경
                response = await call_mcp_server(
                    parsed["toolName"],
                    parsed["toolType"],
                    parsed["queryParams"]
                )
                
                print(f'response json : {response}')

                # reAct 기능 구현
                tool_result = response.text
                if response.status_code == 200:
                    tool_result = response.text
                    print(f"[2️⃣ MCP 결과] {tool_result}")

                    # 5️⃣ Reflect 단계 (이 체인 실행도 자동으로 추적됨)
                    reflect_prompt = PromptTemplate.from_template("""
                        너는 친절한 AI 어시스턴트야.
                        다음은 사용자가 처음 한 질문이야:
                        "{question}"

                        그리고 아래는 MCP 서버에서 조회한 결과야:
                        {tool_result}

                        위의 정보를 바탕으로 자연스럽고 간결하게 답변해줘.
                        답변:
                    """)

                    reflect_chain = reflect_prompt | llm | StrOutputParser()
                    final_answer = await reflect_chain.ainvoke({
                        "question": message,
                        "tool_result": tool_result
                    })
                    print(f"[3️⃣ Reflect 결과] {final_answer}")
                    return final_answer
                else:
                    return f"⚠️ MCP 호출 실패 ({response.status_code})"

        elif (parsed["result"] == '-1'):
            # (이 체인 실행도 자동으로 추적됨)
            reflect_prompt = PromptTemplate.from_template("""
                        너는 친절한 AI 어시스턴트야.
                        사용자 질의에 답해줘
                        {question}
                        답변:
                    """)

            reflect_chain = reflect_prompt | llm | StrOutputParser()
            final_answer = await reflect_chain.ainvoke({"question": message})
            print(f"[3️⃣ Reflect 결과] {final_answer}")
            return final_answer
    except json.JSONDecodeError:
        return llm_result

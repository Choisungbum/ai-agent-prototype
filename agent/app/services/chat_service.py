import asyncio

import json
import requests
#  langchain_core 최신 버전 (v0.2.x ~ v0.3.x 이후) 1.0.3 사용
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM # langchain-ollama 1.0.0 버전 문법 단문형 인터페이스라 채팅형에 어울리지 않음
from langchain_ollama import ChatOllama

MCP_SERVER_URL="http://localhost:9090"


async def get_tool_list() -> str:
    """
    MCP 목록 불러오기

    tool list 호출
    출력형식 
    - toolName(snake_case) | toolDesc | execTarget | toolType | queryParams
    ex)
    "- get_user_info | 사용자의 정보를 조회 | getUserInfo | DB_MAPPER | [\"name\", \"age\", \"gender\", \"email\", \"job_id\"]"
    """ 
    try:
        res = requests.get(f"{MCP_SERVER_URL}/tools/toolList")
        if res.status_code == 200:
            tools = res.json()
            tool_text = "/n".join(
                [
                    f"- {t['toolName']} | {t.get('toolDesc', '')} | {t['toolType']} | {t.get('queryParams','')}"
                    for t in tools
                ] 
            )
            return tool_text
    except Exception as e:
        print("⚠️ MCP Tool 목록 조회 실패:", e)
        return ''




async def process_chat(message: str) -> str:
    """
    사용자 입력을 받아 단순히 가공하여 응답 반환
    """

    print("---------process_chat start---------")
    
    # tool list 호출
    tool_list_text = await get_tool_list()
    print(f"tool list 호출 \n{tool_list_text}")
    print(f"message 호출 \n{message}")
    # 로컬 LLM 사용
    llm = ChatOllama ( # langchain-ollama 1.0.0 버전 문법 
        model="llama3.1:8b",
        base_url="http://localhost:11434", # ✅ 바로 지정
        system=(
                "You are an AI agent that responds to the user..\n"
                "Rules:\n"
                "- Do NOT analyze the given code or text.\n"
                "- You must only follow the instructions below.\n"
                "- Respond in Korean.\n"
                "- Output ONLY the JSON response requested, nothing else.\n"
        ), options={
        "temperature": 0,
        "num_ctx": 8192,  # context 길이
        "top_p": 0.9,
        "repeat_penalty": 1.05
        }
    )

    # 프롬프트 템플릿
    # PromptTemplate.from_template()는 내부적으로 .format()과 비슷하게 동작
    # f string 안써도 동작
    prompt = PromptTemplate.from_template(
         """
        너는 사용자의 질문을 분석하여 JSON 객체를 반환하는 AI 도우미야.
        반드시 아래 규칙을 **엄격히** 지켜.

        ## 규칙
        1. 오직 JSON 형식만 출력해. (불필요한 문장, 설명, 말투 모두 금지)
        2. JSON 외 텍스트, 코드블록 마크다운(`````, ```json``` 등)도 절대 출력하지 마.
        3. 사용자의 질문과 아래 함수 리스트를 비교해 가장 관련 있는 함수를 선택 후 "response": "0".
        4. 질문에서 추출할 수 있는 값만 queryParams에 넣어.
        5. 함수 설명이 없거나 매칭이 불분명하면, `"response": "-1"` 형식으로 출력해.
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
            "response": "0"
        }}

        ## 사용자 질문
        {question}

        ## 출력
        오직 JSON 형식으로만 응답해.
        """
    )
    
    # print(prompt.format(question=message, tool_list_text=tool_list_text))

    # 체인 생성
    # chain 은 “프롬프트에 질문을 넣으면 → LLM이 응답 → 문자열로 반환” 하는 단일 실행 체인 객체
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
        if (parsed["response"] == '0'):
            if "toolName" in parsed:
                response = requests.post(
                    f"{MCP_SERVER_URL}/tools/invoke"
                , json={"toolName":parsed["toolName"], "toolType":parsed["toolType"], "reqParams": parsed["queryParams"]}
                , headers={"Content-Type": "application/json"}
                )
            print(f'response json : {response}')

            # reAct 기능 구현 
            tool_result = response.text
            if response.status_code == 200:
                tool_result = response.text
                print(f"[2️⃣ MCP 결과] {tool_result}")

                # 5️⃣ Reflect 단계: 처음 질문 + MCP 결과를 함께 전달
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
            
        elif (parsed["response"] == '-1'):
            reflect_prompt = PromptTemplate.from_template("""
                    너는 친절한 AI 어시스턴트야.
                    사용자 질의에 답해줘 
                    {question}                                      
                    답변:
                """)

            reflect_chain = reflect_prompt | llm | StrOutputParser()
            final_answer = await reflect_chain.ainvoke({ "question": message})
            print(f"[3️⃣ Reflect 결과] {final_answer}")
            return final_answer
    except json.JSONDecodeError:
        return llm_result
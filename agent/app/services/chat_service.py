import asyncio

import os
import json
import ast
import requests
import datetime
import httpx
from pprint import pprint
from fastapi import HTTPException

#  langchain_core 최신 버전 (v0.2.x ~ v0.3.x 이후) 1.0.3 사용
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_ollama import OllamaLLM # langchain-ollama 1.0.0 버전 문법 단문형 인터페이스라 채팅형에 어울리지 않음
from langchain_ollama import ChatOllama

# redis 
from app.models.database import redis_client
from app.models.chat_memory import ChatMemory, SimpleTokenCounter, count_tokens_with_ollama, summarize_if_needed


from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
REQUEST_TOOLS_LIST = os.getenv("REQUEST_TOOLS_LIST")
REQUEST_INITIALIZE = os.getenv("REQUEST_INITIALIZE")

# 토큰 계산기
token_counter = SimpleTokenCounter()

# 전역 LLM 사용
llm = ChatOllama ( # langchain-ollama 1.0.0 버전 문법 
    model=os.getenv("LLM_MODEL"),
    base_url="http://localhost:11434", # ✅ 바로 지정
    temperature=0,
    num_ctx=4096,  # context 길이
    top_p=0.9,
    repeat_penalty=1.05,
    callbacks=[token_counter]
)

async def initialize(sessionId:str) -> str:
    """
    initialize
    연결 초기화 및 사용가능한 tools 목록 조회

    {
        "jsonrpc": "2.0",
        "method": "initialize",
        "id": "1"
    }
    """ 
    request_data = json.loads(REQUEST_INITIALIZE)
    request_data["id"] = sessionId

    # initialize 요청
    async with httpx.AsyncClient() as client:
        memory = ChatMemory(sessionId)
        try:
            response = await client.post(f"{MCP_SERVER_URL}/invoke"
                                         , headers={"Content-Type": "application/json",
                                                    "X_Session_Id": sessionId}
                                         , json=request_data)
            response.raise_for_status() # 정상 동작 확인 
            result = response.json()
            # redis tool 목록 추가
            memory.add_tool_list(result)
            return {"response": result}
        
        except requests.exceptions.HTTPError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Target server returned an error: {exc.response.text}"
            )
        except requests.exceptions.RequestException as exc:
            raise HTTPException(
                status_code=503,
                detail=f"An error occurred while requesting the target server: {exc}"
            )


async def getToolList(sessionId: str) -> str:
    """
    tools/list
    사용가능한 tools 목록 조회

    {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": "1"
    }
    """ 
    request_data = json.loads(REQUEST_TOOLS_LIST)
    request_data["id"] = sessionId

    # initialize 요청
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{MCP_SERVER_URL}/invoke"
                                         , headers={"Content-Type": "application/json",
                                                    "X_Session_Id": sessionId}
                                         , json=request_data)
            response.raise_for_status() # 정상 동작 확인 

            return {"response": response.json()}
        
        except requests.exceptions.HTTPError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Target server returned an error: {exc.response.text}"
            )
        except requests.exceptions.RequestException as exc:
            raise HTTPException(
                status_code=503,
                detail=f"An error occurred while requesting the target server: {exc}"
            )



async def process_chat(message: str, sessionId: str) -> str:
    """
    사용자 입력을 받아 단순히 가공하여 응답 반환
    """

    print("---------process_chat start---------")

    print("--------- 이전 대화 내역 호출---------")
    memory = ChatMemory(sessionId)

    summary = memory.get_summary()
    recent = memory.get_messages(limit=10)
    
    # history = f"요약: {summary}\n 최근대화:\n" + \
    #                  "\n".join([f"{m['role']}: {m['content']}" for m in recent])

    history_list = []
    history_list.append(SystemMessage (content=f"요약: {summary} \n"))

    for m in recent:
        if m['role'] == "human":
            history_list.append(HumanMessage(content=m["content"]))
        else:
            history_list.append(AIMessage(content=m["content"]))
    
    history = history_list

    pprint(f"history : {history}")


    print("--------- tool list 호출---------")
    # tool_list = await getToolList(sessionId)
    tool_list = memory.get_tool_list()

    print(f"[tool list] \n")
    # data_step1 = json.loads(tool_list)
    # real_data = json.loads(data_step1['response'])
    pretty_tool_data(tool_list)
    print(f"[message] \n{message}")
    print(f"[sessionId] \n{sessionId}")
    

    # 프롬프트 템플릿
    prompt = ChatPromptTemplate.from_messages([
        # LLM이 system/human/assistant 구조를 가장 잘 이해
        # 시스템 메시지: AI의 역할, 규칙, 도구 정의, 출력 포맷
        ("system", """
            너는 사용자의 질문을 분석하여 JSON 객체를 반환하는 AI 도우미야.

            ### 절대 규칙
            - "flag"는 반드시 최상위 depth 위치로.
            - JSON-RPC 기본 요청 형식으로 출력해

            ### 입력 데이터 규칙
            - {history} 는 서버에서 실제 대화 내용 문자열로 치환되어 전달된다.
            - {sessionId} 는 서버에서 실제 세션 ID 값으로 치환되어 전달된다.
            - {tool_list} 는 사용 가능한 함수 리스트 JSON 텍스트이며 서버에서 치환된다.
            - {history}, {tool_list}는 그대로 출력하지 말고 참고만 한다.

            ### 로직 규칙
            - 사용자의 질문과 [함수 리스트]({tool_list})를 비교하여 가장 관련 있는 함수를 선택.
            - 함수가 명확히 매칭되면 "flag": "0".
            - 매칭된 함수 이름은 "params.tool" 에 넣는다.
            - 질문에서 추출 가능한 값만 "params.args" 에 키-값 형태로 넣는다.
            - 함수가 없거나 모호하면 모든 필드는 "" 로 만들고 "flag": "-1"만 출력해.
            - args 에 값을 넣을 때 똑같은 항목이 있다면 억지로 매핑하지말고 한 번 더 호출해 

            ### 출력 형식 (무조건 동일하게 사용)
            {{
            "jsonrpc": "2.0",
            "id": {sessionId},
            "method": "tools/call",
            "flag": "0",
            "params": {{
                    "tool": "",
                    "toolCallId": "",
                    "args": {{}}
                }}
            }}

            ### 참고
            - "toolCallId" 는 "call_001" 형식의 고유 문자열 생성
            - JSON의 구조와 key 이름을 절대 바꾸지 마.
            - result, error, success, status 등은 절대 추가하지 마.

            ### 최근 대화
            {history}

            이제 다음 사용자 질문에 대해 위 JSON 형식만 반환해:
        """),
        # 휴먼 메시지: 실제 사용자의 입력
        ("human", "{question}")
    ])
    

    # 체인 생성
    # LCEL
    chain = prompt | llm | JsonOutputParser() 
    
    # chain 실행
    llm_result = await chain.ainvoke({
        "tool_list": tool_list,
        "sessionId":sessionId,
        "history":history,
        "question": message
    }) 

    
    print(f"[LLM 응답]\n")
    print(json.dumps(llm_result, indent=2, ensure_ascii=False)) 
    

    # 결과 파싱 -> 실제 MCP 호출
    try:
        # 0 -> mcp 서버 호출, 1 -> 일반 응답 
        if (llm_result["flag"] == '0'):
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"{MCP_SERVER_URL}/invoke"
                        , json=llm_result
                        , headers={"Content-Type": "application/json"}
                        , timeout=30.0
                    )
                                
                    tool_result = response.text
                    if response.status_code == 200:
                        tool_result = response.text
                        print(f"[MCP 결과] {tool_result}")

                        # 5️⃣ Reflect 단계: 처음 질문 + MCP 결과를 함께 전달
                        reflect_prompt = ChatPromptTemplate.from_messages([
                            ("system", """
                            너는 친절한 AI 어시스턴트야.

                            야래 MCP 서버에서 조회한 결과를 바탕으로 자연스럽고 간결하게 사용자 질문에 답변해줘.
                            {tool_result}
                            """),
                            ("human", "{question}")
                        ])

                        reflect_chain = reflect_prompt | llm | StrOutputParser()
                        final_answer = await reflect_chain.ainvoke({
                            "tool_result": tool_result,
                            "question": message
                        })
    
                    else:
                        print(f"⚠️ MCP 호출 실패 ({response.status_code})")
                        return f"제가 잘모르는 부분입니다."
                except requests.exceptions.HTTPError as exc:
                    raise HTTPException(
                        status_code=exc.response.status_code,
                        detail=f"Target server returned an error: {exc.response.text}"
                    )
                except requests.exceptions.RequestException as exc:
                    raise HTTPException(
                        status_code=503,
                        detail=f"An error occurred while requesting the target server: {exc}"
                    )
                except httpx.ReadTimeout:
                    # 10초 이상 걸리면 여기로 떨어짐
                    raise HTTPException(status_code=504, detail="Upstream request timeout (30s exceeded)")
        
        # elif (llm_result["flag"] == '-1'):
        else:
            reflect_prompt = ChatPromptTemplate.from_messages([
                            ("system", """
                            너는 친절한 AI 어시스턴트야. 사용자 질문에 답변해줘.
                            """),
                            ("human", "{question}")
                        ])

            reflect_chain = reflect_prompt | llm | StrOutputParser()
            final_answer = await reflect_chain.ainvoke({ "question": message})

    except json.JSONDecodeError:
        return llm_result
    
    prompt_tokens = token_counter.input_tokens
    human_tokens = count_tokens_with_ollama(message)
    assistant_tokens = token_counter.output_tokens

    print(f"입력 토큰 수 (프롬프트): {prompt_tokens}개")
    print(f"입력 토큰 수 (사용자 메세지): {human_tokens}개")
    print(f"출력 토큰 수 (응답): {assistant_tokens}개")

     # redis 추가
    memory.add_message("human", message, human_tokens)
    memory.add_message("assistant", final_answer, assistant_tokens)

    ## 기존 
    await summarize_if_needed(memory, llm)

    print(f"[Reflect 결과] {final_answer}")
    return final_answer
    
# def pretty_tool_data(data):
#     # tools 내부 params만 다시 파싱해서 dict로 변환
#     for tool in data["response"]["result"]["tools"]:
#         try:
#             tool["params"] = json.loads(tool["params"])   # 문자열 → dict
#         except:
#             pass

#     # 전체 다시 예쁘게 출력
#     print(json.dumps(data, indent=2, ensure_ascii=False))  

def pretty_tool_data(data):
    # 1. 입력받은 data가 '리스트'인지 '딕셔너리'인지 확인하여 타겟을 정합니다.
    if isinstance(data, list):
        # 리스트가 들어오면 바로 tools 목록으로 간주
        target_tools = data
    else:
        # 딕셔너리가 들어오면 기존처럼 안쪽 경로를 찾아 들어감
        # (혹시 경로가 없을 수 있으니 try-except나 get을 쓰면 더 안전합니다)
        target_tools = data["response"]["result"]["tools"]

    # 2. 공통 로직: params 문자열을 딕셔너리로 변환
    for tool in target_tools:
        try:
            # params가 있고, 타입이 문자열일 때만 변환 시도
            if "params" in tool and isinstance(tool["params"], str):
                tool["params"] = json.loads(tool["params"])
        except Exception as e:
            # 파싱 에러나면 그냥 원본 유지 (pass)
            pass

    # 3. 전체 예쁘게 출력
    print(json.dumps(data, indent=2, ensure_ascii=False))

# 
# initialize 요청
    
#      요청 형식
#      {
#         "jsonrpc": "2.0",
#         "id": 1,
#         "method": "initialize",
#         "params": {
#             "client": "ai-agent",
#             "version": "1.0",
#             "capabilities": {
#                 "toolUse": true
#             }
#         }
#      }

#      응답 형식
#      {
#         "jsonrpc": "2.0",
#         "id": 1,
#         "result": {
#             "session": "sess_1234",
#             "tools": [
#                 {
#                 "name": "getUserInfo",
#                 "desc": "사용자 정보 조회",
#                 "params": ["name", "age?"]
#                 }
#             ]
#         }
#     }
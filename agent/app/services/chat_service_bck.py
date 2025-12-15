import asyncio

import re
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
from langchain_core.runnables import RunnableLambda

# redis 
from app.models.database import redis_client
from app.models.chat_memory import ChatMemory, SimpleTokenCounter, count_tokens_with_ollama, summarize_if_needed


from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
REQUEST_TOOLS_LIST = os.getenv("REQUEST_TOOLS_LIST")
REQUEST_INITIALIZE = os.getenv("REQUEST_INITIALIZE")

NO_RESULT = os.getenv("NO_RESULT")

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
            pretty_tool_data(result)
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


    pprint(f"history : {history_list}")


    print("--------- tool list 호출---------")
    tool_list = memory.get_tool_list()

    print(f"[tool list] \n")
    print(f"[message] \n{message}")
    print(f"[sessionId] \n{sessionId}")
    

    # 프롬프트 템플릿
    prompt = ChatPromptTemplate.from_messages([
    ("system", """
        You are a smart assistant capable of using tools.

        # TOOLS
        {tool_list}

        # INSTRUCTION (Follow Strictly)
        1. **Language Strategy**: 
        - THINK and DECIDE tools in **ENGLISH** (Logic works best in English).
        - OUTPUT 'Final Answer' in **KOREAN** (Must answer in Korean).
     
        2. **Format**:
        Thought: [Reasoning in English]
        Action: [Tool Name] (or None)
        Action Input: [JSON format, param in Korean]
        Observation: [Wait for result]
        ... (Repeat if needed) ...
        Final Answer: [Answer in Korean]
     
        3. **Rules**:
        - If user greets (e.g., "안녕"), Action: None -> Final Answer.
        - **NO LOOP**: Before calling a tool, CHECK {history}. If you already searched for it, DO NOT search again.
        - **NO FAKE TOOLS**: Use ONLY provided tools.
        - **STOP**: Once you have the info, output 'Final Answer' immediately.
        - **SINGLE TARGET PER ACTION**:
            - You MUST search for **ONE target at a time**.
            - NEVER try to search for multiple people/dates in a single Action.
            - INVALID: {{"name": "A", "name": "B"}} (System Crash!)
            - INVALID: {{"name": ["A", "B"]}} (System Crash!)
            - **VALID**: Search "A" -> Wait -> Search "B".
     
        4. **[Multi-Object Check]**:
       - If user asks for Multiple People (e.g., A and B), you MUST search for **BOTH**.
       - Before writing 'Final Answer', ask yourself: "Did I find info for EVERYONE?"
       - If you only found A, **DO NOT STOP**. Search for B immediately.

        # FEW-SHOT EXAMPLES

        [Case 1: Simple Greeting]
        User: 안녕 반가워 
        Thought: User is greeting. No tool needed.
        Action: None
        Final Answer: 안녕하세요! 무엇을 도와드릴까요?

        [Case 2: Single Tool Search]
        User: 2025년 10월 30일 날씨 어때? 
        Thought: Need to search weather records.
        Action: search_weather_records
        Action Input: {{"target_date": "20251030"}}
        Observation: Weather Info: [Date: 20251030, Weather: Sunny, Temp: 29C]
        Thought: I have the weather info.
        Final Answer: 2025년 10월 30일 날씨는 맑고 기온은 29도입니다.

        [Case 3: Multi-step Search]
        User: 수지와 공유의 나이를 알려줘. 
    
        Thought: User wants info for two people: 수지 and 공유. I must search ONE BY ONE. First, 수지.
        Action: search_users
        Action Input: {{"name": "수지"}}
        Observation: User Info: [Name: 수지, Age: 29]
        
        Thought: I found 수지. Now I MUST search for 공유.
        Action: search_users
        Action Input: {{"name": "공유"}}
        Observation: User Info: [Name: 공유, Age: 44]
        
        Thought: I have info for both.
        Final Answer: 수지는 29세이고, 공유는 44세입니다.
    """),
    ("human", """
        # HISTORY
        {history}

        # CURRENT QUESTION
        User: {question}

        # AGENT SCRATCHPAD
        {agent_scratchpad}
    """)
    ])

    # TARL (Tool-Augmented Reasoning Loop) 시작
    agent_scratchpad = "" # 생각의 누적 기록 공간
    step_count = 0
    max_steps = 10 # 무한 루프 방지용
    final_answer = ""

    # 중복방지 key set
    executed_actions = set()

    while step_count < max_steps:
        step_count += 1
        print(f"\n--- [Step {step_count}] Reasoning 시작 ---") 

        print(f"\n[이전기억]:\n{agent_scratchpad}")

        # LLM 호출 (생각하기)
        # bind를 사용하여 stop 시퀀스 사용
        # LLM이 "Observation:" 이라고 쓰려는 순간 강제로 출력을 끝냄
        # 그렇지 않을 경우 Observation 할루시네이션을 통해 Final Answer까지 가버림
        # chain = prompt | llm.bind(stop=["Observation:"]) | StrOutputParser()
        chain = prompt | llm.bind(stop=["Observation:"]) | RunnableLambda(raw)

        # AIMessage(
        #   content="에이전트 답변 텍스트",
        #   response_metadata={
        #       "prompt_eval_count": 123,
        #       "eval_count": 47,
        #       "model": "llama3.1:8b",
        #       ...
        #   }
        # )

        result = await chain.ainvoke({
            "tool_list": tool_list,
            "history": history_list, 
            "question": message,
            "agent_scratchpad": agent_scratchpad
        })

        response_text = result.content

        # 토큰 계산
        input_tokens = result.response_metadata.get("prompt_eval_count", 0)
        output_tokens = result.response_metadata.get("eval_count", 0)

        print(f"[LLM 생각]:\n{response_text} \n")
        print(f"[LLM input_tokens]: {input_tokens} \n")
        print(f"[LLM output_tokens]: {output_tokens} \n")

        # 종료 조건 확인 (Final Answer 감지)
        if "Final Answer:" in response_text:
            agent_scratchpad = ''
            final_answer = response_text.split("Final Answer:")[-1].strip()

            final_last_brace_index = final_answer.rfind("}")
            if final_last_brace_index != -1:
                final_answer = final_answer[:final_last_brace_index+1]
            print(f"✅ 최종 답변 도출 완료")
            break
 
        action_match = re.search(r"Action:\s*(.*?)\n", response_text)
        input_match = re.search(r"Action Input:\s*(.*)", response_text, re.DOTALL)

        # Action 파싱 (정규표현식 사용)
        # LLM이 뱉은 텍스트에서 'Action:'과 'Action Input:'을 찾아냄
        if action_match!="None" and input_match:
            try:
                tool_name = action_match.group(1).strip()
                raw_args = input_match.group(1).strip()

                # Action Input 뒤에 붙은 불필요한 문자 제거 및 dict 형태로 변환
                last_brace_index = raw_args.rfind("}")
                if last_brace_index != -1:
                    cleaned_args = raw_args[:last_brace_index+1]
                
                tool_args_dict = json.loads(cleaned_args)


                print(f"👉 도구 실행 요청: {tool_name}")
                print(f"👉 파싱된 인자(Object): {tool_args_dict}") 

                current_action_key = f"{tool_name}:{json.dumps(tool_args_dict, sort_keys=True)}"

                # 2. 명단에 있는지 확인 (중복 검사)
                if current_action_key in executed_actions:
                    print(f"⛔ 중복 행동 감지.")
                    
                    # 3. AI한테 경고장 날리기 (절대 API 호출 안 해줌)
                    error_msg = "(System: You ALREADY executed this action. DO NOT TRY AGAIN. Check the 'Observation' above. Output 'Final Answer' in Korean immediately.)"
                    
                    # 4. 기억에 박고 다음 턴으로 강제 이동 (continue)
                    agent_scratchpad += f"\nObservation: {error_msg}\n"
                    continue 
                
                # 3. 처음 하는 거면 명단에 등록
                executed_actions.add(current_action_key)

            except json.JSONDecodeError as e:
                print(f"⚠️ JSON 파싱 실패: {raw_args}")
                agent_scratchpad += f"\nObservation: JSON 형식이 잘못되었습니다. ({cleaned_args}) 올바른 JSON으로 다시 시도하세요.\n"
                continue
            except Exception as e:
                agent_scratchpad += f"\nObservation: 파싱 중 에러 발생 ({str(e)})\n"
                continue
        else:         
            print("⛔ [시스템 감지] Action: None 선언됨.")
            if "result:" in agent_scratchpad:
                print("⚠️ 데이터는 있는데 답 안 하고 도망감 -> 강제 복귀")
                
                # 멱살 잡는 메시지 (이게 들어가야 다음 턴에 바로 답이 나옴)
                force_msg = "(System: You found the data in the 'Observation' above. DO NOT say 'Action: None'. You MUST generate 'Final Answer:' in Korean based on that data immediately.)"
                
                agent_scratchpad += f"\nObservation: {force_msg}\n"
                break
                
            else:
                # 데이터도 없는데 None이면 진짜 할 거 없는 거임 (이건 보내주자)
                print("⛔ 데이터도 없고 할 것도 없음 -> 종료")
                final_answer = "죄송합니다. 관련 정보를 찾을 수 없습니다."
                break

        # MCP 서버 호출 (Acting)
        tool_result = ""
        tool_call_id = f"call_{step_count}"

        try:
            # MCP 서버 스펙에 맞춘 JSON-RPC 생성
            mcp_payload = {
                "jsonrpc": "2.0",
                "id": sessionId,
                "method": "tools/call",
                "params": {
                    "tool": tool_name,
                    "toolCallId": tool_call_id, # 유니크 ID
                    "args": tool_args_dict # LLM이 만든 JSON 문자열 그대로 전달
                }
            }

            async with httpx.AsyncClient() as client:
                mcp_response = await client.post(
                    f"{MCP_SERVER_URL}/invoke",
                    json=mcp_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )

                if mcp_response.status_code == 200:
                    result_json = mcp_response.json()

                    try:
                        real_data = result_json.get("result", {}).get("content", {}).get("data", [])
                        
                        if not real_data:
                            tool_result = NO_RESULT
                        else:
                            # 결과
                            tool_result = f"result: {str(real_data)}"
                            
                    except Exception as e:
                        tool_result = f"데이터 파싱 에러: {mcp_response.text}"
                else:
                    tool_result = f"Error: 도구 호출 실패 (Status {mcp_response.status_code})"

        except Exception as e:
            tool_result = f"Error: 도구 실행 중 예외 발생 ({str(e)})"
            print(f"⚠️ {tool_result}")

        # [디버깅용 출력]
        print(f"[관찰 결과]: {tool_result}")

        # Final Anwser 얻기위한 추가 메세지
        system_nudge = ""

        # 1. 검색결과 존재 -> 검색결과를 통해 Final Answer 출력
        if "result:" in tool_result:
            print("✅ [시스템] 데이터 확보됨. 답안 작성 강요.")
            system_nudge = "(System: Search results are provided above. Analyze the data and summarize it to output 'Final Answer:' in Korean immediately.)"
        
        # 2. 검색결과 없음 -> 검색결과가 없으니 데이터 검색 포기 후 Final Answer 출력
        elif NO_RESULT in tool_result:
             print("⛔ [시스템] 데이터 없음. 포기 강요.")
             system_nudge = "(System: No results found. DO NOT try again. Output 'Final Answer' stating that no info was found.)"

        # 3. 데이터 결과와 추가 메세지 조합
        agent_scratchpad += f"\nObservation: {tool_result}\n{system_nudge}\n"
        
        print(f"현재까지 기억 : {agent_scratchpad}")

    # 루프 종료 후 처리
    if not final_answer:
        agent_scratchpad = ''
        final_answer = "죄송합니다. 도구 실행 횟수가 초과되어 답변을 생성하지 못했습니다."

    print("--------- 토큰 계산---------")

    #  # redis 추가
    memory.add_message("human", message, input_tokens)
    memory.add_message("assistant", final_answer, output_tokens)

    ## 기존 
    await summarize_if_needed(memory, llm)

    print(f"[최종 결과] {final_answer}")
    return final_answer
 

def pretty_tool_data(data):
    # 1. 입력받은 data가 '리스트'인지 '딕셔너리'인지 확인하여 타겟을 정합니다.
    if isinstance(data, list):
        # 리스트가 들어오면 바로 tools 목록으로 간주
        target_tools = data
    else:
        # 딕셔너리가 들어오면 기존처럼 안쪽 경로를 찾아 들어감
        # (혹시 경로가 없을 수 있으니 try-except나 get을 쓰면 더 안전합니다)
        # target_tools = data["response"]["result"]["tools"]
        target_tools = data["result"]["tools"]

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

def raw(msg: AIMessage):
    return msg

# def pretty_tool_data(data):
#     # tools 내부 params만 다시 파싱해서 dict로 변환
#     for tool in data["response"]["result"]["tools"]:
#         try:
#             tool["params"] = json.loads(tool["params"])   # 문자열 → dict
#         except:
#             pass

#     # 전체 다시 예쁘게 출력
#     print(json.dumps(data, indent=2, ensure_ascii=False)) 

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
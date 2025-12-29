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
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_ollama import OllamaLLM # langchain-ollama 1.0.0 버전 문법 단문형 인터페이스라 채팅형에 어울리지 않음
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnableLambda

# redis 
from app.models.chat_memory import ChatMemory, SimpleTokenCounter, count_tokens_with_ollama, summarize_if_needed

from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
REQUEST_TOOLS_LIST = os.getenv("REQUEST_TOOLS_LIST")
REQUEST_INITIALIZE = os.getenv("REQUEST_INITIALIZE")

NO_RESULT = os.getenv("NO_RESULT")

# 토큰 계산
total_session_tokens = {"input": 0, "output": 0}

# 전역 LLM 사용
llm = ChatOllama ( # langchain-ollama 1.0.0 버전 문법 
    model=os.getenv("LLM_MODEL"),
    base_url=os.getenv("OLLAMA_BASE_URL"), 
    temperature=0,
    num_ctx=4096,  # context 길이
    top_p=0.9,
    repeat_penalty=1.05
)

async def initialize(sessionId:str) -> str:
    """
    initialize
    연결 초기화 및 사용가능한 tools 목록 조회

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "client": "ai-agent",
            "version": "1.0",
            "capabilities": {
                "toolUse": true
            }
        }
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

    memory = ChatMemory(sessionId)

    summary = memory.get_summary()
    recent = memory.get_messages(limit=10)

    # history 저장 시 HumanMessage, AIMessage 사용이유 
    # 1. 현재 llama3.1 사용하다 다른 AI로 넘어갈 때 포맷이 다를 수 있지만 해당객체로 관리하면 어디서든 사용가능
    # 2. metadata 저장가능 
    history_list = []
    history_list.append(SystemMessage (content=f"요약: {summary} \n"))

    # 매핑테이블 정의
    role_map = {
        "human": HumanMessage,
        "user": HumanMessage,      
        "system": SystemMessage,
        "ai": AIMessage,
        "assistant": AIMessage
    }

    for m in recent:
        msg_class = role_map.get(m["role"], AIMessage)
        history_list.append(msg_class(content=m["content"]))

    print(f"\n[history]")
    for msg in history_list:
    # msg.type은 'human', 'ai', 'system'을 반환함
        print(f"[{msg.type}]: {msg.content}")

    print(f"\n[message] \n{message}")
    print(f"\n[sessionId] \n{sessionId}")
    
    tool_list = memory.get_tool_list()

    # 프롬프트 템플릿
    # 1. 생각 및 결정은 영어로
    # 2. ReAct 패턴의 Format 지정
    # 3. 실행 규칙 지정
    # 4. 타켓이 하나가 아닐 경우의 전략 
    # 5. 문맥 참조 및 출력 범위 제한 
    # 6. 파라미터 규칙 지정
    prompt = ChatPromptTemplate.from_messages([
    ("system", """
        You are a smart assistant capable of using tools.

        # TOOLS
        {tool_list}

        # SYSTEM INSTRUCTIONS
        1. **Language**: THINK and DECIDE tools in **ENGLISH**.
        
        2. **Format**: Use the following format STRICTLY. Pure Text only (No Markdown headers like #).
        Thought: [Reasoning in English]
        Action: [Tool Name] (or None)
        Action Input: [JSON String]
        Observation: [Wait for result]

         3. **Rules**:
        - If user greets (e.g., "안녕"), Action: None 
        - **NO LOOP**: Before calling a tool, CHECK {history}. If you already searched for it, DO NOT search again.
        - **NO FAKE TOOLS**: Use ONLY provided tools.
        - **SINGLE TARGET PER ACTION**:
            - You MUST search for **ONE target at a time**.
            - NEVER try to search for multiple people/dates in a single Action.
            - INVALID: {{"name": "A", "name": "B"}} (System Crash!)
            - INVALID: {{"name": ["A", "B"]}} (System Crash!)
            - **VALID**: Search "A" -> Wait -> Search "B".
     
        4. **[Multi-Target Search Strategy]**
        - **Checklist Creation:** If the user asks for multiple targets (e.g., "Find A and B"), mentally create a checklist: `[A, B]`.
        - **Independent Execution:** Search for each target **independently**.
            - If the result for A is "Empty/Not Found": Mark A as "Missing", but **DO NOT STOP**.
            - **IMMEDIATELY** proceed to search for B. (A's failure does not affect B).
        - **Completion Condition:** You are NOT allowed to generate a "Action: DONE" until you have iterated through **ALL** targets in your checklist.
        - **Final Reporting:** In your "Action: DONE", clearly summarize the status of EACH target (e.g., "A: Found (Details...), B: Not Found").

       5. **[CONTEXT & SCOPE RULE]** (Read Carefully)
        - **Step 1: Context Understanding (Input)**
            - You MUST look at **History** to understand pronouns like "he", "she", "that person", or "same as before".
            - Example: If History has "Search for A", and User says "What is his age?", you MUST search for "A".
        
        - **Step 2: Output Control (Output)**
            - If the user explicitly changes the topic (e.g., "Now find B"), do NOT include info about "A" in the "Action: DONE".
            - **Rule of Thumb:** Use History to *understand* the question, but answer ONLY what is *currently* asked.
     
        6. **[Argument Value Rules]**
        - **NO GUESSING**: Do NOT fill in optional parameters with assumed values.
        - **User Explicit Only**: Use a value ONLY if the user explicitly stated it in the query
        - If the user input contains a mixed Korean/English term
                (e.g., "DevOps 엔지니어", "IT 컨설턴트"):
                - You MUST copy the term EXACTLY as it appears in the user input.
                - DO NOT translate, normalize, or standardize the term.
                - If you output a translated or normalized version,
                    the output is considered INVALID.
     

        # FEW-SHOT EXAMPLES (Follow these patterns)

        [Case 1: Simple Greeting]
        User: 안녕 반가워
        Thought: User is greeting. No tool needed.
        Action: None

        [Case 2: Single Tool Search]
        User: 2025년 10월 30일 날씨 어때? 
        Thought: Need to search weather records.
        Action: search_weather_records
        Action Input: {{"target_date": "20251030"}}
        Observation: Weather Info: [Date: 20251030, Weather: Sunny, Temp: 29C]
        Thought: I have the weather info.
        Action: DONE

        [Case 3: Multi-step / Fail-Recovery]
        User: 윈터와 카리나의 나이를 알려줘. 
    
        Thought: User wants info for two people: 윈터 and 카리나. I will attempt to search for them sequentially. 
                First, I will check 윈터. If 윈터 is not found, I will mark it as missing and immediately proceed to 카리나
        Action: search_users
        Action Input: {{"name": "윈터"}}
        Observation: User Info: [Name: 윈터, Age: 29]
        
        Thought: I found 윈터. Now I MUST search for 카리나.
        Action: search_users
        Action Input: {{"name": "카리나"}}
        Observation: User Info: [Name: 카리나, Age: 44]
        
        Thought: I have info for both.
        Action: DONE
     
        [Case: Preventing Translation]
        User: "IT 컨설턴트 연봉은?"
        Thought: User used the Korean term "IT 컨설턴트".
        Action: search_jobs
        Action Input: {{"job_title": "IT 컨설턴트"}}
     
    """),
     MessagesPlaceholder(variable_name="history"),
    ("human", """

        # CURRENT MESSAGE
        User: {question}

        # AGENT SCRATCHPAD
        {agent_scratchpad}
        """)
    ])

    # --- [Phase 1] 데이터 수집 단계 ---
    print("\n--- [Phase 1] 데이터 수집 단계  ---")

    # TARL (Tool-Augmented Reasoning Loop) 시작
    # 생각의 누적 기록 공간
    agent_scratchpad = "" 
    step_count = 0
    # 무한 루프 방지용
    max_steps = 10 
    final_answer = ""
    # 장바구니 = tool 결과 데이터
    collected_data = []   
    isAction = False
    current_action_key = ""
    # 중복방지 key set
    executed_actions = set()

    ##########################
    # Agentic Loop 시작
    ##########################
    while step_count < max_steps:
        step_count += 1
        print(f"\n--- [Step {step_count}] Reasoning 시작 ---") 
        print(f"현재까지 기억 \n {agent_scratchpad}")

        ##########################
        # LLM 호출 (Reasoning)
        ##########################
        # chain = prompt | llm.bind(stop=["Observation:"]) | StrOutputParser()
        chain = prompt | llm.bind(stop=["Observation:"]) | RunnableLambda(raw_accumulate) | StrOutputParser()
        response_text = await chain.ainvoke({
            "tool_list": tool_list,
            "history": history_list, 
            "question": message,
            "agent_scratchpad": agent_scratchpad
        })

        print(f"[LLM 생각]:\n{response_text} \n")

        ####################################################
        # 종료 조건: AI가 'DONE' / 'None' 출력할 경우
        ####################################################
        if "Action: DONE" in response_text or "Action: None" in response_text:
            print("검색 종료 선언 (DONE/None) 1")
            break

        ####################################################
        # Action 파싱 (정규표현식 사용)
        ####################################################
        action_match = re.search(r"Action:\s*(.*?)\n", response_text)
        input_match = re.search(r"Action Input:\s*(.*)", response_text, re.DOTALL)

        ####################################################
        # 사용할 도구 및 파라미터 존재하는 경우 
        ####################################################
        if action_match and input_match:
            isAction = True
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

                #####################
                # 중복검사 키 생성
                #####################
                current_action_key = f"{tool_name}:{json.dumps(tool_args_dict, sort_keys=True, ensure_ascii=False)}"

                # 중복 검사
                if current_action_key in executed_actions:
                    print(f"중복 행동 감지.")
                    
                    # AI한테 경고
                    error_msg = "(System: You ALREADY executed this action. DO NOT TRY AGAIN. If you have info, output 'Action: DONE'.)"
                    agent_scratchpad += f"\nObservation: {error_msg}\n"
                    continue 
                
                # 새로운 키 등록 
                executed_actions.add(current_action_key)

            except json.JSONDecodeError as e:
                print(f"⚠️ JSON 파싱 실패: {raw_args}")
                agent_scratchpad += f"\nObservation: JSON 형식이 잘못되었습니다. ({cleaned_args}) 올바른 JSON으로 다시 시도하세요.\n"
                continue
            except Exception as e:
                agent_scratchpad += f"\nObservation: 파싱 중 에러 발생 ({str(e)})\n"
                continue
        else:         
            print("검색 종료 선언 (DONE/None) 2")
            if "result:" in agent_scratchpad:
                print("⚠️ 데이터는 있는데 답 안 하고 도망감 -> 강제 복귀")
                
                # 멱살 잡는 메시지 (이게 들어가야 다음 턴에 바로 답이 나옴)
                force_msg = "(System: You found the data in the 'Observation' above.)"
                
                agent_scratchpad += f"\nObservation: {force_msg}\n"
                break
                
            else:
                # 데이터도 없는데 None이면 진짜 할 거 없는 거임 (이건 보내주자)
                print("데이터도 없고 할 것도 없음 -> 종료")
                msg = "죄송합니다. 관련 정보를 찾을 수 없습니다."
                agent_scratchpad += f"\nObservation: {msg}\n"
                break

        # MCP 서버 호출 (Acting)
        tool_result = ""
        tool_call_id = f"call_{step_count}"

        try:
            ###################################
            # MCP 서버 스펙에 맞춘 JSON-RPC 생성 
            ###################################
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

            #################
            # MCP 서버 호출 
            #################
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

        #################
        # 검색결과 처리
        #################

        # 검색결과 존재 -> 장바구니에 검색결과 담기
        if "result:" in tool_result:
            collected_data.append(current_action_key)
            collected_data.append(tool_result)
            
        # 검색결과 없음 -> 장바구니에 검색결과 NO_RESULT 저장
        elif NO_RESULT in tool_result:
            collected_data.append(current_action_key)
            collected_data.append(NO_RESULT)
             
        print(f"데이터 현황: {tool_result}")
        
        # Observation 검색 결과 추가
        agent_scratchpad += f"\n{response_text}\nObservation: {collected_data}\n"
        
        

    # --- [Phase 2] 답변 생성 단계 ---
    print("\n--- [Phase 2] 최종 답변 생성 중 ---")

    if isAction == True:

        # 장바구니 출력
        context_text = "\n".join(collected_data) 
        print(f"\ncontext_text\n {context_text}")
        
        # 2번째 LLM을 위한 심플한 프롬프트
        summary_prompt = f"""
        You are a friendly AI assistant.
        Based on the 'Collected Data' below, please answer the user's question naturally in Korean.

        [Collected Data]
        {context_text}

        [User Question]
        {message}

        [Writing Guidelines]
        - Do not fabricate information.
        - Summarize and explain using only the content provided in the data.
        - If the provided data does not contain the answer, explicitly state that no information was found.
        """
            
        # LLM 호출
        final_chain = llm
        # final_answer = llm.invoke(summary_prompt).content

    else:
        summary_prompt = f"""
            You are a friendly AI assistant.
            please answer the user's question naturally in Korean.

            
            [User Question]
            {message}

        [Writing Guidelines]
        - Do not fabricate information.
            """
        ##########################
        # LLM 호출 (Final Answer 생성)
        ##########################
        # final_chain = llm | RunnableLambda(raw_accumulate) | StrOutputParser()
        final_chain = llm | RunnableLambda(raw_accumulate)
    
    final_answer = final_chain.invoke(summary_prompt).content
    print(f"최종 답변: {final_answer}")

    ## 기존 
    await summarize_if_needed(memory, llm)

    # redis 추가
    memory.add_message("human", message, total_session_tokens["input"])
    memory.add_message("system", current_action_key, 0)
    memory.add_message("assistant", final_answer, total_session_tokens["output"])

    # 전역변수 토큰 초기화
    total_session_tokens["input"] = 0
    total_session_tokens["output"] = 0

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

def raw_accumulate(ai_message):
    metadata = ai_message.response_metadata
    
    # Llama 3.1 (Ollama) 기준 키값
    input_cnt = metadata.get("prompt_eval_count", 0)
    output_cnt = metadata.get("eval_count", 0)
    
    # 🚨 여기가 핵심: 전역 변수에 더하기
    total_session_tokens["input"] += input_cnt
    total_session_tokens["output"] += output_cnt
    
    print(f"🦙 [Llama] 이번 턴: {input_cnt + output_cnt} (누적: {total_session_tokens['input'] + total_session_tokens['output']})")
    print(f"🦙 [Llama] 이번 턴: {input_cnt}")
    print(f"🦙 [Llama] 이번 턴: {output_cnt}")
    
    return ai_message  # 체인 연결용 반환

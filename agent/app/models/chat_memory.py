import redis
import json
import requests
import os

# from app.core.config import settings

from langchain_core.callbacks.base import BaseCallbackHandler

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


r = redis.Redis(host="localhost", port=6379, db=0, password="wisenut1!")

class ChatMemory:
    def __init__(self, session_id: str):
        self.session_id = session_id

        self.init_key = f"session:{session_id}:init"
        self.msg_key = f"session:{session_id}:message"
        self.sum_key = f"session:{session_id}:summary"
        self.token_key = f"session:{session_id}:token_total"
        self.tools_key =  f"session:{session_id}:tools"

    def add_init(self, init_list:list):
         print(f"init_list : {init_list}")
         r.rpush(self.init_key, init_list)

    def add_message(self, role:str, content: str, tokens: int):
        msg = json.dumps({
            "role": role,
            "content": content,
            "tokens": tokens
        })

        # Redis 리스트(list)에 메시지를 오른쪽(push)으로 추가
        r.rpush(self.msg_key, msg)
        # token_total 값을 tokens 만큼 증가
        r.incrby(self.token_key, tokens)

    def get_messages(self, limit=10):
        # Redis 리스트에서 뒤에서 limit 개수만 가져옴
        msgs = r.lrange(self.msg_key, -limit, -1)
        return [json.loads(m) for m in msgs]

    def get_summary(self):
        data = r.get(self.sum_key)
        return data.decode() if data else ""
    
    def update_summary(self, summary: str):
        r.set(self.sum_key, summary)
    
    def get_total_tokens(self):
        t = r.get(self.token_key)
        return int(t) if t else 0
    
    def clear_message(self):
        r.delete(self.msg_key)
    
    def add_tool_list(self, tools: list):
        tools_text = json.dumps([
            tools
        ])

        # Redis 리스트(list)에 메시지를 오른쪽(push)으로 추가
        r.rpush(self.tools_key, tools_text)

    def get_tool_list(self):
        # Redis 리스트에서 뒤에서 limit 개수만 가져옴
        tools = r.lrange(self.tools_key, 0, -1)
        return [json.loads(m) for m in tools]

class SimpleTokenCounter(BaseCallbackHandler):
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0

    def on_llm_end(self, response, **kwargs):
        # LLM 응답에서 토큰 정보를 추출
        try:
            for generation in response.generations:
                metadata = generation[0].generation_info
                if metadata and 'prompt_eval_count' in metadata:
                    self.input_tokens += metadata.get('prompt_eval_count', 0)
                    self.output_tokens += metadata.get('eval_count', 0)
        except Exception:
            pass


def count_tokens_with_ollama(text: str):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1:8b",
            "prompt": text,
            "stream": False,
            "options": {
                "num_predict": 0  # 출력 생성 안 함
            }
        }
    )

    data = response.json()

    # Ollama가 계산해준 입력 토큰 수
    # Llama3.1은 한국어 1글자 ≈ 1 토큰에 더 가깝다.
    # 4글자 = 1토큰"은 영어 기준 근사
    return data.get("prompt_eval_count", 0)

async def summarize_if_needed(memory: ChatMemory, llm):
    total_token = memory.get_total_tokens()
    max_history_tokens = int(os.getenv("MAX_HISTORY_TOKENS"))

    print(f"현재 프롬프트 토큰 수: {total_token}")

    if total_token < max_history_tokens:
        return
    
    # 1. 전체 메세지 가져오기
    all_messages = memory.get_messages()
    # 2. LLM에게 요약 요청
    message = "\n".join(f"{m['role']}:{m['content']}" for m in all_messages)
    summary_prompt = PromptTemplate.from_template("""
        다음 대화를 1~3문단으로 핵심만 요약해줘.

        대화:
        ----
        {messages}
        """)

    chain = summary_prompt | llm | StrOutputParser()
    summary = chain.invoke({"messages": message})

    # 3. redis 갱신
    memory.update_summary(summary)
    memory.clear_message()
    r.set(memory.token_key, len(summary))
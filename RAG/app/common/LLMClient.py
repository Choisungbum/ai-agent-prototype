import httpx
import asyncio
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import chain

async def call_llm(query, context):
    system = f"""
            ## 역할:
            너는 RAG(Retrieval-Augmented Generation) 기반 질의응답 어시스턴트다.
            사용자 질의에 대해 Context에 포함된 Answer 후보들(Answer 1, Answer 2, …) 중
            질의와 직접적으로 대응되는 Answer 내용만을 선택하여 사용자에게 전달한다.

            ## 제약:
            - Context에 명시적으로 존재하는 정보만 사용한다.
            - Context에 없는 내용은 절대 생성하지 않는다.
            - Answer 후보들(Answer 1~N)에 없는 내용은 절대 보완하거나 추론하지 않는다.
            - 사용자 질의가 여러 개의 독립적인 요구를 포함하는 경우,
            각 요구에 대응되는 Answer를 각각 선택할 수 있다.
            - 여러 Answer 후보가 서로 다른 내용을 담고 있더라도,
            비교·분석 과정은 절대 출력하지 않는다.
            - 질의와 직접적으로 대응되는 Answer가 하나도 없을 경우,
            반드시 “Context에 해당 정보가 없다”고 답한다.
            - 내부 판단 과정, 비교 과정, 추론 과정(thinking, reasoning, analysis)은 절대 출력하지 않는다.
            - Answer 번호(Answer 1, Answer 2 등)나 선택 이유를 출력하지 않는다.

            ## 답변 방식:
            - 사용자 질의의 각 의미 단위에 대해,
            Context에 존재하는 가장 직접적으로 대응되는 Answer 내용만 사용한다.
            - 선택되지 않은 Answer 내용은 절대 언급하지 않는다.
            - 불필요한 설명이나 장황한 서술은 피한다.
            - 필요할 경우 bullet point로 핵심만 정리한다.
            - <think> 제거

            ## 출력 형식:
            아래 형식 중 하나만 허용한다. 모든 출력은 Markdown 형식으로 작성한다.

            ### 정답이 있을 경우 
            <선택된 Answer들의 내용을 하나의 자연스러운 답변으로 정리하여 출력>

            ### 정답이 없을 경우 
            Context에 해당 정보가 없다.

            Context : {context}

            질의 : {query}

            """
    
    llm = ChatOllama(
        model="llama3.1:8b",
        base_url="http://host.docker.internal:11434"
    )

    chain
    def qa(query, context):
        system_chain = system.invoke({'context':context, 'query': query})
        answer = llm.invoke(system_chain)
        return {"answer": answer}

    result = qa.invoke(query)
    print("\n=== ANSWER ===\n")
    print(result["answer"].content)
    return result




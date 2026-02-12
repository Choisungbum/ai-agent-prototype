from app.common.common import retrieve_pipeline, build_context, strip_tags_for_display
from app.common.LLMClient import call_llm
import asyncio, time

# from rich.console import Console
# from rich.markdown import Markdown


def run_retrieve(query: str):
    """검색 파이프라인 실행 (summary → content 검색 + 컨텍스트 조립)"""
    start = time.time()
    print(f'### [retriever] start')

    raw_results = retrieve_pipeline(query)
    results, context = build_context(raw_results)

    end = time.time()
    print(f'### [retriever] 총 걸린시간: {end-start}초')

    return results, context


if __name__ == "__main__":
    print(f'### input query')
    while True:
        print(f'\n\n\n')
        query = input("")

        if query == "exit":
            break
        if not query:
            continue

        results, context = run_retrieve(query)

        for i, doc in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(doc['source'])
            print(strip_tags_for_display(doc['page_content']))

        print(f'### query: {query}')
        raw_response = asyncio.run(call_llm(query, context))
        response = raw_response['choices'][0]['message']['content']
        print(response)
###################
# 그냥 test
###################
parts = ['1. 소개' ,'1.1. 전망', '1.1.1. 해야할일 ']
parent_path = " > ".join(parts[:2])
print(parent_path)
print(parts[2])


###################
# LLOA 연결 test
###################

# import httpx
# import asyncio

# async def call_api():
#     timeout = httpx.Timeout(60.0)  # 초 단위
#     API_URL =  "http://210.180.82.135:9022/v1/chat/completions"
#     headers = {
#         "Authorization": f"Bearer kFQkP6U-ZtzeGTngkjTi50jIq2f7pNNt38gwAgd2o88",
#         "Content-Type": "application/json"
#     }

#     payload = {
#         "model": "wisenut/wise-lloa-max-1.1.0",
#         "messages": [
#             {"role": "system", "content": "You are a helpful assistant."},
#             {"role": "user", "content": "안녕? 좋은 아침이야"}
#         ],
#         "max_tokens": 1024,
#         "temperature": 0.6,
#         "top_p": 0.95,
#         "frequency_penalty": 1.0
#     }
#     async with httpx.AsyncClient(timeout=timeout) as client:
#         res = await client.post(
#            API_URL,
#            headers=headers,
#            json=payload
            
#         )
#         print(res.status_code)
#         print(res.json())

# asyncio.run(call_api())

# import os


# pdf = '/app/testfile/pdf/WISE_iRAG_V2_Builder_매뉴얼_v1.0.pdf'

# name = pdf.rsplit("/")
# file = name[-1]
# dir = name[-2]

# print(file)
# print(dir)

# import psycopg
# conn = psycopg.connect("postgresql://langchain:langchain@pgvector-container:5432/langchain")
# print("OK")
# conn.close()
#  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#     with open(f"{BASE_DIR}/document.json", "w", encoding="utf-8") as f:
#         json.dump(document, f, ensure_ascii=False, indent=2)


# filepath = os.path.basename(pdf)
# filename = filepath.split('/')[-1]
# print(filename)

###################
# 파일 오픈 test
###################
# # # 예: WISE_iRAG_V2_Builder_매뉴얼_v1.0.pdf
# if filename.startswith("WISE_iRAG"):
#     parts = filename.replace(".pdf", "").split("_")
#     if len(parts) >= 4:
#         print(f"[WISE_iRAG:{parts[3].upper()}]")
#     print("[WISE_iRAG]")
# import fitz

# docx_path = "/app/ingestion/testfile/pdf/AI_Agent_exec_guide.pdf"
# docx_path2 = "/app/ingestion/testfile/pdf/wiseirag/WISE_iRAG_V2_설치_매뉴얼_v1.0.pdf"


# def detect_pdf_type(path):
#     doc = fitz.open(path)
#     meta = (doc.metadata or {})
#     prod = (meta.get("producer","") + meta.get("creator","")).lower()

#     if "libreoffice" in prod:
#         return "libreoffice"

#     fonts = set()
#     for p in doc:
#         for f in p.get_fonts():
#             fonts.add(f[3].lower())

#     if any(k in f for f in fonts for k in ("liberation","dejavu")):
#         return "libreoffice"

#     return "web"


# print(detect_pdf_type(docx_path2))

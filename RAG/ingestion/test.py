# pdf = '/app/testfile/pdf/WISE_iRAG_V2_Builder_매뉴얼_v1.0.pdf'

# name = pdf.rsplit("/")
# file = name[-1]
# dir = name[-2]

# print(file)
# print(dir)

import psycopg
conn = psycopg.connect("postgresql://langchain:langchain@pgvector-container:5432/langchain")
print("OK")
conn.close()

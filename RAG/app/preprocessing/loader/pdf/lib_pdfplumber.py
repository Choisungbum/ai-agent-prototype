import pdfplumber

totCount = ''
tables = []
with pdfplumber.open("/app/testfile/pdf/WISE_iRAG_V2_Builder_매뉴얼_v1.0.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        table_data= page.extract_table()
        if table_data:
            tables.append(table_data)
        totCount += page.extract_text()
        # print(tables)
        # print('-----------------------------------')

with open("output_pdfplumber.txt", "w", encoding="utf-8") as f:
    for table in tables:
        for row in table:
            # row 안의 None 값을 빈 문자열로 바꾸고, 각 셀을 탭(\t)으로 연결
            row_str = "\t".join([str(cell) if cell is not None else "" for cell in row])
            f.write(row_str + "\n")
        f.write("\n" + "="*50 + "\n")  # 표 사이 구분선

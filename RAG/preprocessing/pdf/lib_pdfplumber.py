import pdfplumber

totCount = ''
with pdfplumber.open("C:/Users/csbti/Desktop/농어촌/(사규)document/7급사원인사관리세칙(2022.12.01.)-일부개정.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        tables = page.extract_table()
        totCount += page.extract_text()
        print(tables)
        print('-----------------------------------')
    print(totCount)

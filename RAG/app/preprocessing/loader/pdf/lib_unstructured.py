from unstructured.partition.pdf import partition_pdf

# 문서 로드
elements = partition_pdf("C:/Users/csbti/Desktop/농어촌/(사규)document/7급사원인사관리세칙(2022.12.01.)-일부개정.pdf")

# 섹션별로 구분
section = []
current_section = {"title": None, "contents": []}
use_category = ["NarrativeText", "ListItem", "UncategorizedText"]


for e in elements:
    if e.category =="Title":
        if current_section['contents']:
            section.append(current_section)
        current_section = {
            "title": e.text.strip(),
            "contents":[]
        }
    elif e.category in use_category:
        current_section['contents'].append(e.text.strip())

# 마지막 섹션
if current_section['contents']:
    section.append(current_section)

chunks = []

# 출력
for sec in section:
    text = sec['title'] + '\n' + '\n'.join(sec['contents'])
    # chunks.append(text)
    print(text)
    print('--------------------------------------------------------------------------')

# print(chunks)
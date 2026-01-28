import fitz  # PyMuPDF
from statistics import mean

pdf_path = "C:/Users/csbti/Desktop/농어촌/(사규)document/7급사원인사관리세칙(2022.12.01.)-일부개정.pdf"

# for page in fitz.open(pdf_path):
#     text = page.get_text("blocks")
#     print(text)

# page.get_text('dict') 구조 (해당 페이지 전체 요소)
# dict
#    └─ blocks [ ]
#       ├─ block
#       │  ├─ bbox [x0, y0, x1, y1]
#       │  ├─ type
#       │  └─ lines [ ]
#       │     ├─ line
#       │     │  ├─ bbox
#       │     │  └─ spans [ ]
#       │     │     ├─ span
#       │     │     ├─ span
#       │     │     └─ ...
#       │     │
#       │     └─ ...
#       │
#       └─ ...

# span이 핵심
# span
# ├─ text
# ├─ size
# ├─ font
# ├─ flags
# ├─ bbox

# 문서 로드 (Title + text)
def parse_pdf_for_rag(pdf_path):
# 문서 로드
    doc = fitz.open(pdf_path)


    sections = []
    current = {"title":None, "texts": []}

    for page in doc:
        page_height = page.rect.height
        blocks = page.get_text('dict')['blocks']

        # 페이지내 평균 폰트 크기 계산 
        font_size = []
        for b in blocks:
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    font_size.append(span['size'])
        
        avg_font = mean(font_size) if font_size else 0

        for b in blocks:
            bbox = b['bbox']
            y0, y1 = bbox[1], bbox[3]

            # Header / Footer 제거 
            if y1 < 80 or y0 > page_height - 80:
                continue

            for line in b.get('lines', []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    if not text:
                        continue

                    size = span['size']
                    font = span['font']

                    # Title 판별 규칙
                    is_title = (
                        size > avg_font * 1.2 or 
                        "Bold" in font
                    )

                    if is_title:
                        if current['texts']:
                            sections.append(current)
                        current = {
                            'title' : text,
                            'texts' : []
                        }
                    else:
                        current['texts'].append(text)
    if current['texts']:
        sections.append(current)

    doc.close()
    return sections

# 로드된 문서 분할
def build_chunks(sections, max_chars=800):
    chunks = []

    for sec in sections:
        buffer = sec['title'] + '\n' if sec['title'] else ''

        for t in sec['texts']:
            if len(buffer) + len(t) > max_chars:
                chunks.append(buffer.strip())
                buffer = sec['title'] + '\n' + t
            else:
                buffer += ' ' + t
        
        if buffer.strip():
            chunks.append(buffer.strip())
    
    return chunks


sections = parse_pdf_for_rag(pdf_path)
chunks = build_chunks(sections)

for c in chunks:
    print("----")
    print(c[:300])
                    



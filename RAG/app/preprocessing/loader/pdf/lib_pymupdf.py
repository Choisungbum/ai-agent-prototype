import fitz  # PyMuPDF
import pdfplumber
import re
from statistics import mean
import json, uuid, os, hashlib



# page.get_text('dict') 구조 (해당 페이지 전체 요소)
# Page
#  └─ blocks[]        ← 페이지 내 독립적인 콘텐츠 덩어리
#      └─ block
#          ├─ bbox
#          ├─ type
#          └─ lines[]
#              └─ line
#                  ├─ bbox
#                  └─ spans[]
#                      └─ span  #span이 핵심
#                          ├─ text
#                          ├─ font
#                          ├─ size
#                          ├─ flags
#                          └─ bbox
# 구성요소	의미	실무에서의 역할
# page	페이지	범위 단위
# block	레이아웃 덩어리	문단 / 표 후보
# line	시각적 줄	문장 / 표 row
# span	스타일 최소 단위	제목, 표 셀
# bbox	위치	구조 추론의 근거


SKIP_KEYWORDS = ["목차", "Table of Contents"]

def detect_title_level(text: str):
    """Title 계층 평탄화"""
    text = text.strip()
    if re.match(r'^\d+\.\d+\.\d+', text):
        return 3
    if re.match(r'^\d+\.\d+', text):
        return 2
    if re.match(r'^\d+', text):
        return 1
    return None

def table_fingerprint(table):
    """테이블 내용 기반 고유 키 (중복 제거용)"""
    norm = json.dumps(table, ensure_ascii=False)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def normalize_table_rows(table):
    """병합 셀로 인한 빈칸 보정"""
    rows = [[(c or "").strip() for c in r] for r in table]
    for i in range(1, len(rows)):
        for j in range(len(rows[i])):
            if rows[i][j] == "":
                rows[i][j] = rows[i-1][j]
    return rows


def table_to_sentence(table):
    """테이블 1개 → 문장 1덩어리"""
    if not table or len(table) < 2:
        return ""

    table = normalize_table_rows(table)
    header = table[0]
    body = table[1:]

    # 2열 key-value 테이블
    if len(header) == 2:
        parts = []
        for r in body:
            k, v = r[0].strip(), r[1].strip()
            if k and v:
                parts.append(f"{k}는 {v}")
        return " / ".join(parts)

    # 3열 이상
    rows = []
    for r in body:
        pairs = []
        for h, v in zip(header, r):
            if h and v:
                pairs.append(f"{h}={v}")
        if pairs:
            rows.append(", ".join(pairs))
    return " | ".join(rows)


def save_raw_table(table, out_dir):
    """table.json 생성"""
    os.makedirs(out_dir, exist_ok=True)
    table_id = f"table_{uuid.uuid4().hex[:8]}"
    path = os.path.join(out_dir, f"{table_id}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"table_id": table_id, "rows": table},
            f, ensure_ascii=False, indent=2
        )

    return table_id, path


def parse_pdf_for_rag_json(pdf_path, out_dir="../../extracted"):
    doc_id = str(uuid.uuid4())
    base_dir = os.path.join(out_dir, doc_id)
    tables_dir = os.path.join(base_dir, "tables")
    os.makedirs(tables_dir, exist_ok=True)

    document = {
        "doc": {
            "doc_id": doc_id,
            "source_path": pdf_path
        },
        "sections": []
    }

    current_section = None
    current_titles = {1: None, 2: None, 3: None}

    seen_tables = set()  # 테이블 중복 제거 

    with fitz.open(pdf_path) as doc, pdfplumber.open(pdf_path) as plumber:
        for page in doc:
            if page.number < 1:
                continue

            blocks = page.get_text("dict").get("blocks", [])
            if len(blocks) < 3:
                continue

            # =========================
            # (A) 테이블은 페이지당 1번만
            # =========================
            page_tables = plumber.pages[page.number].extract_tables() or []

            for table in page_tables:
                fp = table_fingerprint(table)
                if fp in seen_tables:
                    continue   # ✅ 중복 제거

                seen_tables.add(fp)

                table_text = table_to_sentence(table)
                if not table_text.strip():
                    continue

                table_id, table_path = save_raw_table(table, tables_dir)

                if current_section:
                    current_section["blocks"].append({
                        "block_id": str(uuid.uuid4()),
                        "type": "table",
                        "page": page.number + 1,
                        "text": table_text,
                        "table_ref": {
                            "table_id": table_id,
                            "path": os.path.relpath(table_path, base_dir)
                        }
                    })

            # =========================
            # (B) PyMuPDF 텍스트 처리
            # =========================
            page_height = page.rect.height
            font_sizes = [
                span["size"]
                for b in blocks
                for line in b.get("lines", [])
                for span in line.get("spans", [])
            ]
            avg_font = mean(font_sizes) if font_sizes else 0

            for b in blocks:
                y0, y1 = b["bbox"][1], b["bbox"][3]
                if y1 < 80 or y0 > page_height - 80:
                    continue

                # table-like 블록은 무조건 skip
                if len(b.get("lines", [])) >= 3:
                    continue

                for line in b.get("lines", []):
                    text = "".join(span["text"] for span in line["spans"]).strip()
                    if not text:
                        continue

                    size = max(span["size"] for span in line["spans"])
                    font = line["spans"][0]["font"]
                    level = detect_title_level(text)

                    is_title = (
                        level is not None and
                        (size > avg_font * 1.1 or "Bold" in font)
                    )

                    if is_title:
                        if current_section and current_section["blocks"]:
                            document["sections"].append(current_section)

                        current_titles[level] = text
                        for l in range(level + 1, 4):
                            current_titles[l] = None

                        full_title = " > ".join(
                            t for t in current_titles.values() if t
                        )

                        current_section = {
                            "section_id": str(uuid.uuid4()),
                            "title": full_title,
                            "blocks": []
                        }
                    else:
                        if current_section:
                            current_section["blocks"].append({
                                "block_id": str(uuid.uuid4()),
                                "type": "text",
                                "page": page.number + 1,
                                "text": text
                            })

    if current_section and current_section["blocks"]:
        document["sections"].append(current_section)

    with open(os.path.join(base_dir, "document.json"), "w", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False, indent=2)

    return document


pdf_path = '/app/testfile/pdf/WISE_iRAG_V2_Builder_매뉴얼_v1.0.pdf'

# 출력
doc_json = parse_pdf_for_rag_json(pdf_path)

# with open("document.json", "w", encoding="utf-8") as f:
#     json.dump(doc_json, f, ensure_ascii=False, indent=2)


# # 출력
# for sec in section:
#     if not sec['title']:
#         continue
#     text = sec['title'] + '\n' + '\n'.join(sec['texts'])
#     # chunks.append(text)
#     print(text)
#     print('--------------------------------------------------------------------------')

# print(chunks)
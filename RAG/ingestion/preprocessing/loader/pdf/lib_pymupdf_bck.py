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


SKIP_KEYWORDS = ["목차", "Table of Contents", "문서 개정 이력"]
def parse_pdf_for_rag_json(pdf_path):
    doc_id = str(uuid.uuid4())

    document = {
        "doc": {
            "doc_id": doc_id,
            "source": pdf_path
        },
        "sections": []
    }

    # title_stack: [{"level": 1, "text": "5. ..."}, {"level": 2, "text": "5.1 ..."} ...]
    title_stack = []
    current_section = None

    seen_tables = set()

    # 첫 title 나오기 전에 나온 테이블/텍스트(있을 수도 있어서)
    orphan_blocks = []

    def start_new_section(level: int, title_text: str):
        nonlocal current_section, title_stack

        # stack 갱신 (같거나 더 깊은 레벨 제거)
        while title_stack and title_stack[-1]["level"] >= level:
            title_stack.pop()
        title_stack.append({"level": level, "text": title_text})

        full_title = " > ".join(t["text"] for t in title_stack)

        current_section = {
            "section_id": str(uuid.uuid4()),
            "title": full_title,
            "blocks": []
        }

        # orphan이 있으면 첫 section 시작할 때 앞에 붙여줌(선택)
        if orphan_blocks:
            for ob in orphan_blocks:
                ob["section_id"] = current_section["section_id"]
                current_section["blocks"].append(ob)
            orphan_blocks.clear()

    def finalize_section():
        nonlocal current_section
        if current_section and current_section["blocks"]:
            document["sections"].append(current_section)
        current_section = None

    def add_block_to_current(block: dict):
        nonlocal current_section
        if current_section:
            block["section_id"] = current_section["section_id"]
            current_section["blocks"].append(block)
        else:
            # title 나오기 전이라면 orphan으로 보관
            orphan_blocks.append(block)

    def bboxes_intersect(b1, b2):
        x0, y0, x1, y1 = b1
        a0, b0, a1, b1_ = b2
        return (x1 > a0 and x0 < a1 and y1 > b0 and y0 < b1_)
    
    def table_fingerprint(table):
        """테이블 내용 기반 고유 키 (중복 제거용)"""
        norm = json.dumps(table, ensure_ascii=False)
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()


    MERGE_COLS = None  # None이면 전체 컬럼, {0,1} 이면 일부만

    def fill_none_cells(rows):
        if not rows:
            return rows

        filled = []
        last_values = [None] * len(rows[0])

        for row in rows:
            new_row = []
            for i, cell in enumerate(row):
                if cell is None and (MERGE_COLS is None or i in MERGE_COLS):
                    new_row.append(last_values[i])
                else:
                    new_row.append(cell)
                    last_values[i] = cell
            filled.append(new_row)

        return filled

        

    def rows_to_markdown(rows: list[list[str]]) -> str:
        """ 2차원 배열 -> Markdown 표형식으로 변환 """
        if not rows:
            return ""
        
        rows = fill_none_cells(rows)

        header = rows[0]
        body = rows[1:]

        lines = []
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")

        for row in body:
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)

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

    with fitz.open(pdf_path) as doc, pdfplumber.open(pdf_path) as plumber:
        for page in doc:
            if page.number < 1:
                continue

            blocks = page.get_text("dict").get("blocks", [])
            if len(blocks) < 3:
                continue

            Header_Title = blocks[0]['lines'][0]['spans'][0]['text']
            if Header_Title.strip() in SKIP_KEYWORDS:
                continue

            page_height = page.rect.height

            # 페이지 평균 폰트
            font_sizes = [
                span["size"]
                for b in blocks
                for line in b.get("lines", [])
                for span in line.get("spans", [])
            ]
            avg_font = mean(font_sizes) if font_sizes else 0

            # =========================
            # (A) table 이벤트 수집 (y0 포함)
            # =========================
            table_events = []
            table_bboxes = []

            try:
                page_plumber = plumber.pages[page.number]
            except Exception as e:
                print("FAILED page:", e)

            for tbl in (page_plumber.find_tables() or []):
                table = tbl.extract()
                if not table:
                    continue

                fp = table_fingerprint(table)
                if fp in seen_tables:
                    continue
                seen_tables.add(fp)

                bbox = tbl.bbox  # (x0, top, x1, bottom) in pdfplumber coords
                table_bboxes.append(bbox)

                table_events.append({
                    "type": "table",
                    "page": page.number + 1,
                    "y0": bbox[1],
                    "payload": {
                        "block_id": str(uuid.uuid4()),
                        "doc_id": doc_id,
                        "page": page.number + 1,
                        "block_type": "table",
                        "text": rows_to_markdown(table),
                        "y0": bbox[1],
                    }
                })

            # =========================
            # (B) text/title 이벤트 수집 (y0 포함)
            #   - 테이블 bbox와 겹치는 텍스트는 스킵
            # =========================
            text_events = []

            # PyMuPDF blocks 자체가 대체로 위->아래이지만, 안전하게 y0로 정렬
            sorted_blocks = sorted(blocks, key=lambda b: b.get("bbox", [0, 0, 0, 0])[1])

            for b in sorted_blocks:
                bbox = b.get("bbox", None)
                if not bbox:
                    continue

                # header/footer 컷
                y0, y1 = bbox[1], bbox[3]
                if y1 < 80 or y0 > page_height - 80:
                    continue

                # 테이블 영역이면 이 block 텍스트는 제외
                if any(bboxes_intersect(bbox, tb) for tb in table_bboxes):
                    continue

                # 기존 조건 유지(너가 넣어둔 필터)
                if len(b.get("lines", [])) >= 3:
                    continue

                for line in b.get("lines", []):
                    text = "".join(span["text"] for span in line.get("spans", [])).strip()
                    if not text:
                        continue

                    spans = line.get("spans", [])
                    if not spans:
                        continue

                    size = max(span.get("size", 0) for span in spans)
                    font = spans[0].get("font", "")

                    level = detect_title_level(text)
                    is_title = (
                        level is not None and
                        (size > avg_font * 1.1 or "Bold" in font)
                    )

                    text_events.append({
                        "type": "title" if is_title else "text",
                        "page": page.number + 1,
                        "y0": bbox[1],
                        "payload": {
                            "text": text,
                            "level": level,
                            "font_size": size,
                            "font": font,
                        }
                    })

            # =========================
            # (C) 이벤트 병합 + y0 순 처리 (핵심)
            # =========================
            events = table_events + text_events
            events.sort(key=lambda e: (e["page"], e["y0"], 0 if e["type"] == "title" else 1))

            for ev in events:
                if ev["type"] == "title":
                    # 새 title이면 이전 section 종료 후 새 section 시작
                    finalize_section()
                    level = ev["payload"]["level"]
                    title_text = ev["payload"]["text"]
                    start_new_section(level, title_text)

                elif ev["type"] == "table":
                    # 현재 활성 section(=title_stack top)에 즉시 귀속
                    add_block_to_current(ev["payload"])

                else:  # text
                    # current_section이 있어야만 텍스트를 넣음(없으면 orphan으로)
                    add_block_to_current({
                        "block_id": str(uuid.uuid4()),
                        "doc_id": doc_id,
                        "page": ev["page"],
                        "block_type": "text",
                        "text": ev["payload"]["text"],
                        "y0": ev["y0"],
                    })

        # 마지막 section flush
        finalize_section()

    # =========================
    # (D) 정렬 + block_index 재부여 (section 내부에서만)
    # =========================
    for section in document["sections"]:
        section["blocks"].sort(key=lambda x: (x["page"], x.get("y0", 0)))
        for idx, block in enumerate(section["blocks"], start=1):
            block["block_index"] = idx

    return document



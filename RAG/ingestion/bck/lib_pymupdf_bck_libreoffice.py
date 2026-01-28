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
    def detect_pdf_type(path):
        doc = fitz.open(path)
        meta = doc.metadata or {}
        prod = (meta.get("producer", "") + meta.get("creator", "")).lower()
        doc.close()
        return "libreoffice" if "libreoffice" in prod else "other"

    pdf_type = detect_pdf_type(pdf_path)
    
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
    orphan_blocks = []

    def start_new_section(level: int, title_text: str):
        nonlocal current_section, title_stack

        while title_stack and title_stack[-1]["level"] >= level:
            title_stack.pop()
        title_stack.append({"level": level, "text": title_text})

        full_title = " > ".join(t["text"] for t in title_stack)

        current_section = {
            "section_id": str(uuid.uuid4()),
            "section_title": full_title,
            "blocks": []
        }

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
            orphan_blocks.append(block)

    def bboxes_intersect(b1, b2):
        x0, y0, x1, y1 = b1
        a0, b0, a1, b1_ = b2
        return (x1 > a0 and x0 < a1 and y1 > b0 and y0 < b1_)

    def table_fingerprint(table):
        norm = json.dumps(table, ensure_ascii=False)
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    MERGE_COLS = None

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

    def rows_to_markdown(rows):
        if not rows:
            return ""

        try:
            rows = fill_none_cells(rows)
            header = rows[0]
            body = rows[1:]

            if any(h is None for h in header):
                raise ValueError("Invalid table header")

            lines = []
            lines.append("| " + " | ".join(header) + " |")
            lines.append("| " + " | ".join(["---"] * len(header)) + " |")

            for row in body:
                if len(row) != len(header) or any(c is None for c in row):
                    raise ValueError("Invalid table row")
                lines.append("| " + " | ".join(row) + " |")

            return "\n".join(lines)

        except Exception:
            joined = " ".join(str(c) for row in rows for c in row if c)

            # 🔥 이 조건이 핵심
            if re.search(r'[\{\}\[\]":]', joined):
                return ""   # JSON / code 예시는 table로 취급하지 않음
            lines = []
            for row in rows:
                line = " ".join(str(c) for c in row if c)
                if line.strip():
                    lines.append(line)
            return "\n".join(lines)

    def detect_title_level(text: str):
        text = text.strip()
        m = re.match(r'^(\d+(?:\.\d+)*)', text)
        if not m:
            return None
        return m.group(1).count('.') + 1
    
    # PumyPDF 오픈 시 block 타입 확인
    # fitz.get_text("dict")에서 block 타입별 구조
    # type	의미	        lines 존재
    # 0	    텍스트	        ⭕ 있음
    # 1	    이미지	        ❌ 없음
    # 2	    도형(line/rect)	❌ 없음
    def extract_header_text(blocks):
        for b in blocks:
            if b.get("type") != 0:
                continue
            lines = b.get("lines")
            if not lines:
                continue
            spans = lines[0].get("spans")
            if not spans:
                continue
            return spans[0].get("text")
        return None

    with fitz.open(pdf_path) as doc, pdfplumber.open(pdf_path) as plumber:
        for page in doc:
            if page.number < 1:
                continue

            blocks = page.get_text("dict").get("blocks", [])
            if len(blocks) < 3:
                continue

            # block 타입 판별
            Header_Title = extract_header_text(blocks)
            if not Header_Title:
                continue

            if Header_Title.strip() in SKIP_KEYWORDS:
                continue


            page_height = page.rect.height

            font_sizes = [
                span["size"]
                for b in blocks
                if b.get("type") == 0
                for line in b.get("lines", [])
                for span in line.get("spans", [])
            ]
            avg_font = mean(font_sizes) if font_sizes else 0

            # =========================
            # (A) table 이벤트 수집
            # =========================
            table_events = []
            table_bboxes = []

            page_plumber = plumber.pages[page.number]

            for tbl in (page_plumber.find_tables() or []):
                table = tbl.extract()
                if not table:
                    continue

                fp = table_fingerprint(table)
                if fp in seen_tables:
                    continue
                seen_tables.add(fp)

                bbox = tbl.bbox
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
            # (A-2) image 이벤트 수집 (추가된 부분)
            # =========================
            image_events = []
            for img in page_plumber.images:
                block_id = str(uuid.uuid4())
                image_events.append({
                    "type": "image",
                    "page": page.number + 1,
                    "y0": img["top"],
                    "payload": {
                        "block_id": block_id,
                        "doc_id": doc_id,
                        "page": page.number + 1,
                        "block_type": "image",
                        "text": f"[IMAGE]{block_id}[/IMAGE]",
                        "y0": img["top"],
                    }
                })

            # =========================
            # (B) text/title 이벤트 수집
            # =========================
            text_events = []

            sorted_blocks = sorted(blocks, key=lambda b: b.get("bbox", [0, 0, 0, 0])[1])

            for b in sorted_blocks:
                if b.get("type") != 0:
                    continue

                lines = b.get("lines")
                if not lines:
                    continue

                bbox = b.get("bbox")
                if not bbox:
                    continue

                y0, y1 = bbox[1], bbox[3]
                if y1 < 80 or y0 > page_height - 80:
                    continue

                if any(bboxes_intersect(bbox, tb) for tb in table_bboxes):
                    continue

                if len(lines) >= 3:
                    continue

                for line in lines:
                    raw_text = "".join(span["text"] for span in line.get("spans", [])).strip()
                    if not raw_text:
                        continue

                    # ✅ 수정 (LibreOffice만 라인 분리)
                    if pdf_type == "libreoffice":
                        texts = [t.strip() for t in raw_text.split("\n") if t.strip()]
                    else:
                        texts = [raw_text]

                    for text in texts:
                        spans = line.get("spans", [])
                        size = max(span.get("size", 0) for span in spans)

                        level = detect_title_level(text)
                        is_title = (
                            level is not None
                            and re.match(r'^\d+(\.\d+)*\s', text)   # 반드시 "9.2.3 " 형태
                            and size > avg_font * 1.05              # 폰트는 보조
                        )
                        text_events.append({
                            "type": "title" if is_title else "text",
                            "page": page.number + 1,
                            "y0": bbox[1],
                            "payload": {
                                "text": text,
                                "level": level if is_title else None,
                            }
                        })
            
            # ✅ 추가 (LibreOffice 전용: 1. + 다음 블록 병합)
            if pdf_type == "libreoffice":
                merged = []
                i = 0
                while i < len(text_events):
                    cur = text_events[i]

                    if (
                        re.fullmatch(r"\d+\.", cur["payload"]["text"])
                        and i + 1 < len(text_events)
                    ):
                        nxt = text_events[i + 1]
                        merged.append({
                            "type": "text",
                            "page": cur["page"],
                            "y0": cur["y0"],
                            "payload": {
                                "text": cur["payload"]["text"] + " " + nxt["payload"]["text"],
                                "level": None
                            }
                        })
                        i += 2
                        continue

                    merged.append(cur)
                    i += 1

                text_events = merged
            # =========================
            # (C) 이벤트 병합
            # =========================
            events = table_events + image_events + text_events
            events.sort(key=lambda e: (e["page"], e["y0"], 0 if e["type"] == "title" else 1))

            for ev in events:
                if ev["type"] == "title":
                    finalize_section()
                    start_new_section(ev["payload"]["level"], ev["payload"]["text"])
                    continue   # title은 block으로 안 보냄

                elif ev["type"] in ("table", "image"):
                    add_block_to_current(ev["payload"])

                else:
                    add_block_to_current({
                        "block_id": str(uuid.uuid4()),
                        "doc_id": doc_id,
                        "page": ev["page"],
                        "block_type": "text",
                        "text": ev["payload"]["text"],
                        "y0": ev["y0"],
                    })

        finalize_section()

    # =========================
    # (D) 정렬 + block_index 재부여
    # =========================
    for section in document["sections"]:
        section["blocks"].sort(key=lambda x: (x["page"], x.get("y0", 0)))
        for idx, block in enumerate(section["blocks"], start=1):
            block["block_index"] = idx

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    with open(f"{BASE_DIR}/{document['doc']['doc_id']}.json", "w", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False, indent=2)

    return document
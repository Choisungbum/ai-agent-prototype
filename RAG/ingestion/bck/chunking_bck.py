import re
import os

ACTION_KEYWORDS = ["삭제", "생성", "수정", "변경", "호출", "설정", "등록"]

# role 태그 추가
def detect_role(text):
    if any(k in text for k in ACTION_KEYWORDS):
        return "action"
    if "예제" in text or "example" in text.lower():
        return "example"
    if "란" in text or "정의" in text:
        return "definition"
    return "general"

def make_manual_tag(source_path):
    filepath = os.path.basename(source_path)
    filename = filepath.split('/')[-1]

    # WISE_iRAG 문서 표기 및 어떤 메뉴얼인지 표기
    # 예: WISE_iRAG_V2_Builder_매뉴얼_v1.0.pdf
    if filename.startswith("WISE_iRAG"):
        parts = filename.replace(".pdf", "").split("_")
        if len(parts) >= 4:
            return f"[WISE_iRAG:{parts[3].upper()}]"
        return "[WISE_iRAG]"
    else: # 다른 문서일 경우 관련 태그 표기
        return None

def extract_paragraphs(doc_json):
    paragraphs = []

    doc_id = doc_json["doc"]["doc_id"]
    source = doc_json["doc"].get("source")

    for section in doc_json["sections"]:
        section_id = section["section_id"]
        section_title = section["section_title"]
        title_attached = False

        for block in section["blocks"]:
            text = block.get("text")
            if not text:
                continue

            # text가 list / str 모두 대응
            if isinstance(text, list):
                if all(len(t) == 1 for t in text):
                    fulltext = "".join(text)
                else:
                    fulltext = " ".join(text)
            else:
                fulltext = text

            fulltext = fulltext.strip()
            if not fulltext:
                continue

            # section title은 section 당 한 번만 prepend
            if section_title and not title_attached:
                fulltext = f"{section_title}\n{fulltext}"
                title_attached = True

            paragraphs.append({
                "text": re.sub(r"[ \t]+", " ", fulltext).strip(),

                # 🔑 핵심 메타데이터
                "doc_id": doc_id,
                "source": source,

                "section_id": section_id,
                "section_title": section_title,

                "page": block.get("page"),
                "block_id": block.get("block_id"),
                "block_index": block.get("block_index"),
                "block_type": block.get("block_type"),

                # 선택 (있으면 순서 복원에 도움)
                "y0": block.get("y0"),
            })

    return paragraphs




def semantic_chunking_by_section(paragraphs, max_chars=1000, overlap=150):
    chunks = []

    buf = ""
    prev_tail = ""

    pages = set()
    block_types = set()
    block_ids = []

    doc_id = source = section_id = section_title = None
    min_block_index = max_block_index = None

    def flush_chunk():
        nonlocal buf, prev_tail, pages, block_types, block_ids
        nonlocal min_block_index, max_block_index

        base_text = (prev_tail + buf).strip()
        if not base_text:
            return

        manual_tag = make_manual_tag(source)
        role = detect_role(base_text)

        action_hint = ""
        if role == "action" and section_title:
            action_hint = f"[ACTION] {section_title}\n"

        final_text = ""
        if manual_tag:
            final_text += manual_tag + "\n"
        if action_hint:
            final_text += action_hint + "\n"

        final_text += base_text
        if not final_text:
            return

        chunks.append({
            "text": f"[SECTION_PATH]{section_title}\n{final_text}",

            "doc_id": doc_id,
            "source": source,
            "section_id": section_id,
            "section_title": section_title,

            "pages": sorted(pages),
            "block_types": sorted(block_types),
            "block_ids": block_ids.copy(),

            "block_index_range": {
                "min": min_block_index,
                "max": max_block_index,
            },

            "role": role,
        })

        prev_tail = final_text[-overlap:]
        buf = ""
        pages.clear()
        block_types.clear()
        block_ids.clear()
        min_block_index = None
        max_block_index = None

    last_section_id = None

    for p in paragraphs:
        # 🔑 section 바뀌면 무조건 flush
        if last_section_id is not None and p["section_id"] != last_section_id:
            flush_chunk()
            prev_tail = ""  # section 바뀌면 overlap 제거

        if not buf:
            doc_id = p["doc_id"]
            source = p["source"]
            section_id = p["section_id"]
            section_title = p["section_title"]

        t = p["text"]

        # 길이 초과 시 section 내부 분할
        if len(buf) + len(t) > max_chars:
            flush_chunk()

            doc_id = p["doc_id"]
            source = p["source"]
            section_id = p["section_id"]
            section_title = p["section_title"]

        buf += t + "\n\n"

        pages.add(p.get("page"))
        block_types.add(p.get("block_type"))
        block_ids.append(p.get("block_id"))

        bi = p.get("block_index")
        if bi is not None:
            min_block_index = bi if min_block_index is None else min(min_block_index, bi)
            max_block_index = bi if max_block_index is None else max(max_block_index, bi)

        last_section_id = p["section_id"]

    if buf.strip():
        flush_chunk()

    return chunks

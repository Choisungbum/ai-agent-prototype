import re

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




def semantic_chunking(paragraphs, max_chars=1000, overlap=150):
    chunks = []

    buf = ""
    prev_tail = ""

    pages = set()
    block_types = set()
    block_ids = []

    # 대표 메타데이터 (chunk 시작 기준)
    doc_id = None
    source = None
    section_id = None
    section_title = None

    min_block_index = None
    max_block_index = None

    def flush_chunk():
        nonlocal buf, prev_tail, pages, block_types, block_ids
        nonlocal min_block_index, max_block_index

        chunk_text = (prev_tail + buf).strip()
        if not chunk_text:
            return

        chunks.append({
            "text": chunk_text,

            # 🔑 핵심 메타데이터
            "doc_id": doc_id,
            "source": source,
            "section_id": section_id,
            "section_title": section_title,

            "pages": sorted(pages),
            "block_types": sorted(block_types),
            "block_ids": block_ids.copy(),

            "min_block_index": min_block_index,
            "max_block_index": max_block_index,
        })

        prev_tail = chunk_text[-overlap:]
        buf = ""
        pages.clear()
        block_types.clear()
        block_ids.clear()
        min_block_index = None
        max_block_index = None

    for p in paragraphs:
        t = p["text"]

        # 대표 메타데이터는 chunk 시작 시점의 paragraph 기준
        if not buf:
            doc_id = p.get("doc_id")
            source = p.get("source")
            section_id = p.get("section_id")
            section_title = p.get("section_title")

        if len(buf) + len(t) > max_chars:
            flush_chunk()

            # 새 chunk 대표 메타데이터 재설정
            doc_id = p.get("doc_id")
            source = p.get("source")
            section_id = p.get("section_id")
            section_title = p.get("section_title")

        buf += t + "\n\n"

        pages.add(p.get("page"))
        block_types.add(p.get("block_type"))
        block_ids.append(p.get("block_id"))

        bi = p.get("block_index")
        if bi is not None:
            min_block_index = bi if min_block_index is None else min(min_block_index, bi)
            max_block_index = bi if max_block_index is None else max(max_block_index, bi)

    if buf.strip():
        flush_chunk()

    return chunks

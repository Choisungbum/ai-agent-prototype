import re
import os
import json, uuid
from collections import defaultdict

ACTION_KEYWORDS = ["삭제", "생성", "수정", "변경", "호출", "설정", "등록"]

# role 태그 추가
def detect_role(text):
    if any(k in text for k in ACTION_KEYWORDS):
        return "action"
    return "general"


def extract_paragraphs(doc_json):
    """가장작은 의미단위로 분해"""
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
    """의미기반 grouping 및 chunking """
    chunks = []

    # 현재 section 내에서 누적 중인 본문 버퍼 (순수 텍스트만)
    buf = ""
    prev_tail = ""

    # 메타데이터 누적
    pages = set()
    block_types = set()
    block_ids = []

    doc_id = source = section_id = section_title = None
    min_block_index = max_block_index = None

    def flush_chunk():
        nonlocal buf, prev_tail, pages, block_types, block_ids
        nonlocal min_block_index, max_block_index

        # 🔑 overlap은 "본문(body)" 기준으로만 사용
        body = (prev_tail + buf).strip()
        if not body:
            return
        
        # section title이 본문에 중복으로 들어온 경우 제거
        if section_title:
            pattern = rf'^\s*{re.escape(section_title)}\s*'
            body = re.sub(pattern, '', body)

        role = detect_role(body)

        # ===== 최종 chunk 텍스트 구성 =====
        parts = []

        # section 경로는 chunk 당 1번만
        if section_title:
            parts.append(f"[SECTION_PATH]{section_title}")

        if role == "action":
            parts.append("[ACTION]")

        parts.append(body)

        final_text = "\n".join(parts)

        chunks.append({
            "text": final_text,

            # 핵심 메타데이터
            "doc_id": doc_id,
            "source": source,
            "section_id": section_id,
            "section_title": section_title,

            # 추적용 메타
            "pages": sorted(pages),
            "block_types": sorted(block_types),
            "block_ids": block_ids.copy(),

            "block_index_range": {
                "min": min_block_index,
                "max": max_block_index,
            },

            "role": role,
        })

        # 다음 chunk overlap 준비 (본문 기준)
        prev_tail = body[-overlap:] if overlap > 0 else ""

        # 버퍼 초기화
        buf = ""
        pages.clear()
        block_types.clear()
        block_ids.clear()
        min_block_index = None
        max_block_index = None

    last_section_id = None

    for p in paragraphs:
        # 🔑 section이 바뀌면 무조건 flush
        if last_section_id is not None and p["section_id"] != last_section_id:
            flush_chunk()
            prev_tail = ""  # section 바뀌면 overlap 제거

        # 새 section 시작 시 메타 세팅
        if not buf:
            doc_id = p["doc_id"]
            source = p["source"]
            section_id = p["section_id"]
            section_title = p["section_title"]

        text = p["text"]
        if not text:
            continue

        # 길이 초과 시 section 내부 분할
        if len(buf) + len(text) > max_chars:
            flush_chunk()

            doc_id = p["doc_id"]
            source = p["source"]
            section_id = p["section_id"]
            section_title = p["section_title"]

        # buf에는 "본문 텍스트만" 누적
        buf += text + "\n\n"

        # 메타 누적
        if p.get("page") is not None:
            pages.add(p["page"])

        if p.get("block_type"):
            block_types.add(p["block_type"])

        if p.get("block_id"):
            block_ids.append(p["block_id"])

        bi = p.get("block_index")
        if bi is not None:
            min_block_index = bi if min_block_index is None else min(min_block_index, bi)
            max_block_index = bi if max_block_index is None else max(max_block_index, bi)

        last_section_id = p["section_id"]

    # 마지막 남은 버퍼 처리
    if buf.strip():
        flush_chunk()

    return chunks


def build_summaries_chunk(content_chunks):
    """원문을 요약하여 chunk 생성"""

    def split_path(section_title: str):
        return [p.strip() for p in section_title.split('>') if p.strip()]
    
    summaries = {}

    # 모든 상위 path를 summary 후보로
    for ch in content_chunks:
        st = ch.get("section_title") or ""
        parts = split_path(st)
        if len(parts) < 2:
            continue

        for depth in range(1, len(parts)):
            summary_path = " > ".join(parts[:depth])
            content_part = parts[depth]


            p = summaries.setdefault(summary_path, {
                "content": set(),
                "doc_id": ch.get("doc_id"),
                "source": ch.get("source"),
                "pages": set()
            })
            p['content'].add(content_part)
            for pg in (ch.get('pages') or []):
                p['pages'].add(pg)
    
    summary_chunks = []
    for summary_path, info in summaries.items():
        content = sorted(info['content'])
        if len(content) < 2:
            continue

        lines = []
        lines.append(f"[SECTION_PATH]{summary_path}")
        lines.append('[SUMMARY]')
        for c in content:
            lines.append(f" - {c}")

        summary_chunks.append({
            "text": "\n".join(lines),
            "doc_id": info["doc_id"],
            "source": info["source"],
            "summary_id": str(uuid.uuid4()),
            "section_title": summary_path,
            "pages": sorted(info["pages"]),
            "block_types": ["summary"],
            "block_ids": [],
            "block_index_range": {"min": None, "max": None},
            "role": "summary",
        })

    return summary_chunks




def build_2level_summaries(content_chunks):
    """원문을 요약하여 top, mid chunk 생성
        content  →  mid summary  →  top summary
        (summary_id)   (parent_id)
    """

    def split_section_path(section_title: str):
        return [p.strip() for p in section_title.split(">") if p.strip()]

    # mid: 요약용 titles + 메타용 chunks 분리
    mid_map = defaultdict(lambda: {
        "titles": set(),
        "chunks": []
    })
    top_map = defaultdict(set)

    # 1. content → mid / top 그룹핑
    for ch in content_chunks:
        parts = split_section_path(ch.get("section_title", ""))
        if len(parts) < 2:
            continue

        top = parts[0]
        mid = " > ".join(parts[:2])

        mid_map[mid]["titles"].add(ch["section_title"])
        mid_map[mid]["chunks"].append(ch)

        top_map[top].add(mid)

    mid_summaries = []
    top_summaries = []

    mid_id_map = {}
    top_id_map = {}

    # 2. mid summary 생성
    for mid, info in mid_map.items():
        mid_id = str(uuid.uuid4())
        mid_id_map[mid] = mid_id

        titles = info["titles"]
        chunks = info["chunks"]

        mid_summaries.append({
            "text": (
                f"[SECTION_PATH]{mid}\n"
                "[SUMMARY]\n" +
                "\n".join(
                    sorted(
                        split_section_path(t)[-1]
                        for t in titles
                    )
                )
            ),
            "doc_id": chunks[0]["doc_id"],
            "source": chunks[0]["source"],

            "summary_id": mid_id,
            "parent_id": None,

            "section_title": mid,
            "pages": sorted({
                p for c in chunks for p in (c.get("pages") or [])
            }),
            "block_types": ["summary"],
            "block_ids": [],
            "block_index_range": {"min": None, "max": None},

            "role": "summary",
            "tier": "mid",
        })

    # 3. top summary 생성
    for top, mids in top_map.items():
        top_id = str(uuid.uuid4())
        top_id_map[top] = top_id

        top_summaries.append({
            "text": (
                f"[SECTION_PATH]{top}\n"
                "[SUMMARY]\n" +
                "\n".join(sorted(mids))
            ),
            "doc_id": content_chunks[0]["doc_id"],
            "source": content_chunks[0]["source"],

            "summary_id": top_id,
            "parent_id": None,

            "section_title": top,
            "pages": sorted({
                p for c in content_chunks
                if c.get("section_title", "").startswith(top)
                for p in (c.get("pages") or [])
            }),
            "block_types": ["summary"],
            "block_ids": [],
            "block_index_range": {"min": None, "max": None},

            "role": "summary",
            "tier": "top",
        })

    # 4. mid → top 연결
    for m in mid_summaries:
        top = split_section_path(m["section_title"])[0]
        m["parent_id"] = top_id_map.get(top)

    # 5. content → mid 연결
    for ch in content_chunks:
        parts = split_section_path(ch.get("section_title", ""))
        if len(parts) >= 2:
            mid = " > ".join(parts[:2])
            ch["summary_id"] = mid_id_map.get(mid)
            ch["tier"] = "content"

    return content_chunks, mid_summaries, top_summaries
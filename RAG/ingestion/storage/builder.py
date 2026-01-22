from langchain_core.documents import Document

class LangChainDocumentBuilder:
    @staticmethod
    def from_chunks(chunks: list[dict]) -> list[Document]:
        docs = []

        for ch in chunks:
            docs.append(
                Document(
                    page_content=ch["text"],
                    metadata={
                        # 🔑 문서 추적
                        "doc_id": ch.get("doc_id"),
                        "source": ch.get("source"),

                        # 🔑 구조 정보
                        "section_id": ch.get("section_id"),
                        "section_title": ch.get("section_title"),

                        # 🔑 위치 정보
                        "pages": ch.get("pages"),
                        "min_block_index": ch.get("min_block_index"),
                        "max_block_index": ch.get("max_block_index"),

                        # 🔑 내용 성격
                        "block_types": ch.get("block_types"),
                        "block_ids": ch.get("block_ids"),
                    }
                )
            )

        return docs

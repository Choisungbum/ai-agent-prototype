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
                        # 문서 식별
                        "doc_id": ch.get("doc_id"),
                        "source": ch.get("source"),

                        # 의미 / 계층
                        "role": ch.get("role"),              # general | action | summary
                        "section_title": ch.get("section_title"),

                        # multi-vector 연결
                        "summary_id": ch.get("summary_id"),
                        "parent_id": ch.get("parent_id"),

                        # 위치 (선택)
                        "pages": ch.get("pages"),
                        "block_index_min": ch.get("block_index_range", {}).get("min"),
                        "block_index_max": ch.get("block_index_range", {}).get("max"),
                    }
                )
            )

        return docs

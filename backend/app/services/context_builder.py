from typing import List, Dict, Any

class ContextBuilder:
    def __init__(self, max_context_chars: int = 8000):
        self.max_context_chars = max_context_chars

    def build_context(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Construct a clean, structured context block from retrieved chunks with deduplication and size limits.
        """
        if not retrieved_chunks:
            return ""

        seen_contents = set()
        blocks = []
        total_chars = 0

        for chunk in retrieved_chunks:
            content = chunk.get("content", "").strip()
            if not content:
                continue

            # Deduplication
            normalized_snippet = content[:120].lower()
            if normalized_snippet in seen_contents:
                continue
            seen_contents.add(normalized_snippet)

            doc_name = chunk.get("document_name", "Unknown Document")
            page_num = chunk.get("page_number")
            page_label = f"Page {page_num}" if page_num is not None else "Document Body"

            block = f"--- [Source: {doc_name} | {page_label} | Chunk #{chunk.get('chunk_index', 0)}] ---\n{content}"

            if total_chars + len(block) > self.max_context_chars:
                break

            blocks.append(block)
            total_chars += len(block)

        return "\n\n".join(blocks)

context_builder = ContextBuilder()

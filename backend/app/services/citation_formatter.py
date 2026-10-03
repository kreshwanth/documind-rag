from typing import List, Dict, Any, Optional
from uuid import UUID
from app.schemas.rag import SourceCitation

class CitationFormatter:
    @staticmethod
    def format_citations(retrieved_chunks: List[Dict[str, Any]]) -> List[SourceCitation]:
        """
        Deduplicate citations by document and page/chunk, preserving highest similarity score, sorted descending.
        """
        if not retrieved_chunks:
            return []

        citation_map = {}

        for chunk in retrieved_chunks:
            doc_id = chunk.get("document_id")
            page_num = chunk.get("page_number")
            key = f"{doc_id}_{page_num}_{chunk.get('chunk_index')}"

            sim_score = float(chunk.get("similarity_score", 0.0))
            snippet = chunk.get("content", "")
            excerpt = snippet[:220].strip() + ("..." if len(snippet) > 220 else "")

            if key not in citation_map or sim_score > citation_map[key].similarity_score:
                citation_map[key] = SourceCitation(
                    document_id=doc_id,
                    document_name=chunk.get("document_name", "Unknown Document"),
                    page_number=page_num,
                    chunk_id=chunk.get("chunk_id"),
                    similarity_score=round(sim_score, 4),
                    excerpt=excerpt
                )

        # Sort by similarity score descending
        sorted_citations = sorted(citation_map.values(), key=lambda c: c.similarity_score, reverse=True)
        return sorted_citations

citation_formatter = CitationFormatter()

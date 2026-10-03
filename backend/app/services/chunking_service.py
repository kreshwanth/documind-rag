import re
from typing import List, Dict, Any, Optional
from uuid import UUID
from app.config import settings
import logging

logger = logging.getLogger("documind.chunking")

class ChunkingService:
    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def clean_text(self, text: str) -> str:
        """Normalize whitespace, tabs, and duplicate blank lines while preserving paragraph breaks."""
        if not text:
            return ""
        text = re.sub(r'[\r\f\v]', '\n', text)
        text = re.sub(r'\t', ' ', text)
        text = re.sub(r'[ ]{2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def chunk_document(
        self,
        pages_content: List[Dict[str, Any]],
        document_id: Optional[UUID] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Deterministic chunking preserving document_id, chunk_index, content, page_number, and metadata.
        """
        c_size = chunk_size or self.chunk_size
        c_overlap = chunk_overlap or self.chunk_overlap
        
        chunks: List[Dict[str, Any]] = []
        global_index = 0

        for page_data in pages_content:
            page_num = page_data.get("page_number")
            raw_text = page_data.get("text", "")
            cleaned = self.clean_text(raw_text)
            
            if not cleaned:
                continue

            split_passages = self._split_text_with_boundaries(cleaned, c_size, c_overlap)

            for passage in split_passages:
                if len(passage.strip()) > 10:  # ignore trivial fragments
                    chunks.append({
                        "document_id": document_id,
                        "chunk_index": global_index,
                        "content": passage.strip(),
                        "page_number": page_num,
                        "metadata": {
                            "length": len(passage.strip()),
                            "has_page_number": page_num is not None
                        }
                    })
                    global_index += 1

        return chunks

    def _split_text_with_boundaries(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Sliding window splitting with boundary preservation."""
        if len(text) <= chunk_size:
            return [text]

        results = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + chunk_size, text_length)

            if end < text_length:
                # Seek natural boundary near the end
                boundary = -1
                for delim in ["\n\n", ".\n", ". ", "?\n", "! ", "\n", " "]:
                    pos = text.rfind(delim, start + int(chunk_size * 0.5), end)
                    if pos != -1:
                        boundary = pos + len(delim)
                        break
                if boundary != -1 and boundary > start:
                    end = boundary

            chunk = text[start:end].strip()
            if chunk:
                results.append(chunk)

            advance = (end - start) - overlap
            if advance <= 0:
                advance = max(1, end - start)
            start += advance

        return results

chunking_service = ChunkingService()

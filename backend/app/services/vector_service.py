from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc
from app.models.chunk import DocumentChunk
from app.models.document import Document
import logging

logger = logging.getLogger("documind.vector")

class VectorService:
    @staticmethod
    def similarity_search(
        db: Session,
        query_embedding: List[float],
        user_id: UUID,
        document_ids: Optional[List[UUID]] = None,
        top_k: int = 4,
        similarity_threshold: float = 0.40
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search against PostgreSQL pgvector.
        Enforces user ownership, optional document filtering, and similarity thresholding.
        Cosine distance in pgvector: distance = 1 - cosine_similarity.
        Therefore similarity = 1 - cosine_distance.
        """
        # Calculate cosine distance
        distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding)
        similarity_expr = (1.0 - distance_expr).label("similarity")

        # Build query joining Document to guarantee user ownership
        query = (
            db.query(
                DocumentChunk,
                Document.original_filename.label("document_name"),
                Document.id.label("doc_id"),
                similarity_expr
            )
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(
                Document.user_id == user_id,
                Document.status == "COMPLETED"
            )
        )

        # Optional document IDs filter
        if document_ids:
            query = query.filter(Document.id.in_(document_ids))

        # Filter by similarity threshold
        query = query.filter(similarity_expr >= similarity_threshold)

        # Order by similarity descending
        query = query.order_by(desc(similarity_expr)).limit(top_k)

        results = query.all()
        
        hits = []
        for chunk, doc_name, doc_id, sim in results:
            hits.append({
                "chunk_id": chunk.id,
                "document_id": doc_id,
                "document_name": doc_name,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "similarity_score": round(float(sim), 4)
            })

        logger.info(f"Vector search for user {user_id}: found {len(hits)} chunks above threshold {similarity_threshold}")
        return hits

vector_service = VectorService()

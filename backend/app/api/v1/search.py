from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.rag import SearchRequest, SearchResponse, SearchResult
from app.services.embedding_service import embedding_service
from app.services.vector_search_service import vector_search_service
from app.api.deps import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger("documind.search_api")

@router.post("", response_model=SearchResponse)
def semantic_search(
    req: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dedicated semantic search endpoint to test and explore underlying pgvector retrieval
    independently from LLM generation.
    """
    query_vector = embedding_service.embed_query(req.query)
    chunks = vector_search_service.search(
        db=db,
        user_id=current_user.id,
        query_embedding=query_vector,
        top_k=req.top_k,
        similarity_threshold=req.similarity_threshold,
        document_ids=req.document_ids,
        query_text=req.query
    )

    results = [
        SearchResult(
            chunk_id=c["chunk_id"],
            document_id=c["document_id"],
            document_name=c["document_name"],
            page_number=c["page_number"],
            chunk_index=c["chunk_index"],
            similarity_score=c["similarity_score"],
            content=c["content"],
            excerpt=c["excerpt"]
        )
        for c in chunks
    ]

    return SearchResponse(
        query=req.query,
        results=results,
        total_found=len(results)
    )

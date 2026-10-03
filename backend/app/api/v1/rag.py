from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, SearchChunksRequest, SearchChunksResponse, ChunkSearchHit
from app.services.rag_service import rag_service
from app.services.vector_service import vector_service
from app.services.gemini_service import gemini_service
from app.api.deps import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger("documind.rag_api")

@router.post("/query", response_model=RAGQueryResponse)
def query_documents(
    query_in: RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform Retrieval-Augmented Generation (RAG):
    1. Embed user query.
    2. Retrieve top-K most similar document chunks with user-isolation.
    3. Apply similarity threshold & anti-hallucination guardrails.
    4. Generate grounded response using Gemini AI.
    5. Return answer with source document and page number citations.
    """
    try:
        response = rag_service.query(
            db=db,
            user=current_user,
            question=query_in.question,
            conversation_id=query_in.conversation_id,
            document_ids=query_in.document_ids,
            top_k=query_in.top_k,
            similarity_threshold=query_in.similarity_threshold
        )
        return response
    except Exception as e:
        logger.error(f"Error executing RAG query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query execution failed: {str(e)}"
        )

@router.post("/search-chunks", response_model=SearchChunksResponse)
def search_chunks(
    search_in: SearchChunksRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Vector similarity search endpoint to inspect retrieved passages and similarity scores directly.
    """
    query_vector = gemini_service.get_query_embedding(search_in.query)
    hits = vector_service.similarity_search(
        db=db,
        query_embedding=query_vector,
        user_id=current_user.id,
        document_ids=search_in.document_ids,
        top_k=search_in.top_k or 5,
        similarity_threshold=search_in.similarity_threshold or 0.30
    )

    results = [
        ChunkSearchHit(
            chunk_id=h["chunk_id"],
            document_id=h["document_id"],
            document_name=h["document_name"],
            page_number=h["page_number"],
            chunk_index=h["chunk_index"],
            similarity_score=h["similarity_score"],
            content=h["content"]
        )
        for h in hits
    ]

    return SearchChunksResponse(
        query=search_in.query,
        results=results,
        total_found=len(results)
    )

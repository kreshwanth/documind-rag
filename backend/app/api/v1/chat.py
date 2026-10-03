from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.rag import ChatRequest, ChatResponse
from app.services.rag_chat_pipeline import rag_chat_pipeline
from app.api.deps import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger("documind.chat_api")

@router.post("", response_model=ChatResponse)
def chat_with_documents(
    chat_req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute full RAG chat workflow:
    1. Authenticate user.
    2. Embed question.
    3. Perform pgvector similarity search on user's documents.
    4. Apply top-K & threshold.
    5. Build grounded prompt and generate answer via Gemini.
    6. Return answer and source citations.
    """
    try:
        response = rag_chat_pipeline.execute(
            db=db,
            user=current_user,
            chat_req=chat_req
        )
        return response
    except Exception as e:
        logger.error(f"Error executing chat pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat pipeline error: {str(e)}"
        )

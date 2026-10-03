from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.schemas.document import DocumentStatsOut
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/stats", response_model=DocumentStatsOut)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve aggregate document and vector metrics for the user dashboard."""
    docs = db.query(Document).filter(Document.user_id == current_user.id).all()

    total_docs = len(docs)
    completed_docs = sum(1 for d in docs if (d.status or "").lower() == "completed")
    processing_docs = sum(1 for d in docs if (d.status or "").lower() in ["pending", "processing"])
    failed_docs = sum(1 for d in docs if (d.status or "").lower() == "failed")
    total_pages = sum(d.total_pages for d in docs)
    total_storage = sum(d.file_size for d in docs)

    # Count chunks owned by user
    total_chunks = (
        db.query(func.count(DocumentChunk.id))
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(Document.user_id == current_user.id)
        .scalar()
    ) or 0

    return DocumentStatsOut(
        total_documents=total_docs,
        completed_documents=completed_docs,
        processing_documents=processing_docs,
        failed_documents=failed_docs,
        total_chunks=total_chunks,
        total_storage_bytes=total_storage,
        total_pages=total_pages
    )

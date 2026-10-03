import os
import uuid
import shutil
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.config import settings
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentDetailResponse, DocumentStatusResponse
from app.services.document_processing_service import document_processing_service
from app.api.deps import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger("documind.documents_api")

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "md"}

def run_async_processing(document_id: UUID):
    """Background task runner for document processing."""
    db = SessionLocal()
    try:
        document_processing_service.process_document(document_id=document_id, db=db)
    except Exception as e:
        logger.error(f"Background processing error for doc {document_id}: {e}")
    finally:
        db.close()

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document (PDF, DOCX, TXT).
    Validates file extension, size, generates safe sanitized storage path, creates pending record,
    and enqueues background ingestion.
    """
    original_filename = file.filename or "untitled_document"
    ext = original_filename.split(".")[-1].lower() if "." in original_filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: '.{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot upload an empty file."
        )

    # Sanitize and generate safe server-side storage filename
    safe_storage_name = f"{uuid.uuid4()}_{os.path.basename(original_filename)}"
    storage_path = os.path.join(settings.UPLOAD_DIRECTORY, safe_storage_name)

    try:
        with open(storage_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to write file to disk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file to storage."
        )

    # Create initial Document record in 'pending' status
    document = Document(
        user_id=current_user.id,
        filename=safe_storage_name,
        original_filename=original_filename,
        file_type=ext,
        file_size=file_size,
        storage_path=storage_path,
        status="pending",
        total_pages=0,
        total_chunks=0
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Dispatch asynchronous document processing
    background_tasks.add_task(run_async_processing, document_id=document.id)

    return DocumentResponse.model_validate(document)

@router.get("", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents owned by current authenticated user."""
    docs = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(Document.created_at.desc()).all()
    return [DocumentResponse.model_validate(d) for d in docs]

@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details and chunk representations of an owned document."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return DocumentDetailResponse.model_validate(doc)

@router.post("/{document_id}/process", response_model=DocumentResponse)
def process_or_retry_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger or retry processing for a document."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    doc.status = "pending"
    doc.error_message = None
    db.commit()

    background_tasks.add_task(run_async_processing, document_id=doc.id)
    return DocumentResponse.model_validate(doc)

@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current processing status and chunk statistics of a document."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return DocumentStatusResponse(
        id=doc.id,
        status=doc.status,
        error_message=doc.error_message,
        total_pages=doc.total_pages,
        total_chunks=doc.total_chunks
    )

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete document, disk storage, and vector chunks (with strict user authorization)."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if doc.storage_path and os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except Exception as e:
            logger.warning(f"Could not delete physical file {doc.storage_path}: {e}")

    db.delete(doc)
    db.commit()
    return {"message": "Document and associated vector chunks deleted successfully."}

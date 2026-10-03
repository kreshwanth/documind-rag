from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class DocumentChunkResponse(BaseModel):
    id: UUID
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    chunk_metadata: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: UUID
    user_id: UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    storage_path: str
    status: str
    error_message: Optional[str] = None
    total_pages: int
    total_chunks: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int

class DocumentStatusResponse(BaseModel):
    id: UUID
    status: str
    error_message: Optional[str] = None
    total_pages: int
    total_chunks: int

class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkResponse] = []

class DocumentStatsResponse(BaseModel):
    total_documents: int
    completed_documents: int
    processing_documents: int
    failed_documents: int
    total_chunks: int
    total_storage_bytes: int
    total_pages: int

# Alias for backward compatibility
DocumentStatsOut = DocumentStatsResponse

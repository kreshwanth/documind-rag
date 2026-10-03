from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class SourceCitation(BaseModel):
    document_id: Optional[UUID] = None
    document_name: str
    page_number: Optional[int] = None
    chunk_id: Optional[UUID] = None
    similarity_score: float
    excerpt: Optional[str] = None

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=4000, description="Question to answer grounded in documents")
    conversation_id: Optional[UUID] = Field(None, description="Optional conversation thread ID")
    document_ids: Optional[List[UUID]] = Field(default=[], description="Optional specific document IDs to restrict search to")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Configurable top-K chunks")
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Configurable cosine threshold")

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    conversation_id: UUID
    message_id: Optional[UUID] = None
    retrieved_chunks_count: int = 0
    is_fallback: bool = False

class SearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_name: str
    page_number: Optional[int] = None
    chunk_index: int
    similarity_score: float
    content: str
    excerpt: str

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    document_ids: Optional[List[UUID]] = Field(default=[])
    top_k: Optional[int] = Field(5, ge=1, le=20)
    similarity_threshold: Optional[float] = Field(0.30, ge=0.0, le=1.0)

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_found: int

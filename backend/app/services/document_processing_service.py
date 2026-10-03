from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.services.parser_service import document_parser
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
import logging

logger = logging.getLogger("documind.document_processing")

class DocumentProcessingService:
    @staticmethod
    def process_document(document_id: UUID, db: Session) -> Document:
        """
        Execute full asynchronous document ingestion pipeline:
        1. Set status to 'processing'.
        2. Extract text (PDF/DOCX/TXT).
        3. Clean and chunk text while preserving page number.
        4. Generate embeddings via Gemini Embedding Service.
        5. Bulk save DocumentChunk records in PostgreSQL with pgvector.
        6. Set status to 'completed'.
        """
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found.")

        doc.status = "processing"
        doc.error_message = None
        db.commit()

        try:
            # 1. Parse text preserving pages
            pages_content = document_parser.extract_text(file_path=doc.storage_path, file_type=doc.file_type)
            if not pages_content:
                raise ValueError("No extractable text found in document.")

            # Calculate total pages if available
            valid_pages = [p["page_number"] for p in pages_content if p.get("page_number") is not None]
            doc.total_pages = max(valid_pages) if valid_pages else 1

            # 2. Chunk text with semantic boundaries
            chunks_data = chunking_service.chunk_document(
                pages_content=pages_content,
                document_id=doc.id
            )
            if not chunks_data:
                raise ValueError("No valid text chunks could be produced from document.")

            # 3. Generate batch embeddings
            chunk_texts = [c["content"] for c in chunks_data]
            embeddings = embedding_service.embed_chunks(chunk_texts, batch_size=20)

            # 4. Clean up any existing chunks if retrying a failed document
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()

            # 5. Save DocumentChunks
            db_chunks = []
            for i, c in enumerate(chunks_data):
                emb = embeddings[i] if i < len(embeddings) else embedding_service._pseudo_embedding(c["content"])
                chunk_obj = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=c["chunk_index"],
                    content=c["content"],
                    page_number=c.get("page_number"),
                    chunk_metadata=c.get("metadata", {}),
                    embedding=emb
                )
                db_chunks.append(chunk_obj)

            db.bulk_save_objects(db_chunks)

            # 6. Complete
            doc.status = "completed"
            doc.total_chunks = len(db_chunks)
            db.commit()
            db.refresh(doc)
            logger.info(f"Document {document_id} processed successfully: {doc.total_chunks} chunks.")
            return doc

        except Exception as e:
            logger.error(f"Failed processing document {document_id}: {e}", exc_info=True)
            db.rollback()
            doc.status = "failed"
            doc.error_message = str(e)
            db.commit()
            db.refresh(doc)
            return doc

document_processing_service = DocumentProcessingService()

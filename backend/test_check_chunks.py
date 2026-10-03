import uuid
from app.database import SessionLocal
from app.models.chunk import DocumentChunk

db = SessionLocal()
leave_doc_id = uuid.UUID("42ac4238-1685-4a0f-8015-f5f492764398")
chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == leave_doc_id).all()
for c in chunks:
    if "exception" in c.content.lower() or "modify" in c.content.lower():
        print(f"--- Page {c.page_number} Chunk {c.chunk_index} ---")
        print(c.content)

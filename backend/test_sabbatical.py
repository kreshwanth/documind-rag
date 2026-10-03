import uuid
from app.database import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.services.embedding_service import embedding_service
from app.services.vector_search_service import vector_search_service

db = SessionLocal()
user_id = uuid.UUID("f1a2138d-cf4a-4152-b51b-8a966911dd11")
leave_doc_id = uuid.UUID("42ac4238-1685-4a0f-8015-f5f492764398")
user = db.query(User).filter(User.id == user_id).first()

q = "An employee wants to take a long break to pursue further education that is relevant to their current job. What provision in the company’s leave policy could apply to them, and what approval would be required?"
q_vec = embedding_service.embed_query(q)

print("=== CANDIDATES FOR INDIRECT QUESTION ===")
chunks = vector_search_service.search(
    db=db,
    user_id=user.id,
    query_embedding=q_vec,
    document_ids=[leave_doc_id],
    query_text=q,
    top_k=10
)
for c in chunks:
    print(f"P{c['page_number']} | Chunk #{c['chunk_index']} | Score: {c['similarity_score']} | Cos: {c['raw_cosine']}")
    print(c['content'][:150])
    print("-" * 50)

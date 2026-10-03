import uuid
from app.database import SessionLocal
from app.models.user import User
from app.services.rag_chat_pipeline import rag_chat_pipeline
from app.schemas.rag import ChatRequest

db = SessionLocal()
user_id = uuid.UUID("f1a2138d-cf4a-4152-b51b-8a966911dd11")
user = db.query(User).filter(User.id == user_id).first()
leave_doc_id = uuid.UUID("42ac4238-1685-4a0f-8015-f5f492764398")

q = "An employee wants to take a long break to pursue further education that is relevant to their current job. What provision in the company’s leave policy could apply to them, and what approval would be required?"
req = ChatRequest(question=q, document_ids=[leave_doc_id], top_k=4)
res = rag_chat_pipeline.execute(db=db, user=user, chat_req=req)

print("=" * 70)
print(f"QUESTION: {q}")
print("ANSWER:\n", res.answer)
print("\nSOURCES:")
for s in res.sources:
    print(f"  - {s.document_name} (Page {s.page_number}) [Sim: {s.similarity_score}]")

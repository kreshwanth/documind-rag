import uuid
from app.database import SessionLocal
from app.models.user import User
from app.schemas.rag import ChatRequest
from app.services.rag_chat_pipeline import rag_chat_pipeline

db = SessionLocal()
user_id = uuid.UUID("f1a2138d-cf4a-4152-b51b-8a966911dd11")
leave_doc_id = uuid.UUID("42ac4238-1685-4a0f-8015-f5f492764398")
user = db.query(User).filter(User.id == user_id).first()

q = "If management needs to make an exception to the leave policy, what approval is required?"
req = ChatRequest(
    question=q,
    document_ids=[leave_doc_id]
)
res = rag_chat_pipeline.execute(
    db=db,
    user=user,
    chat_req=req
)

print("=== ANSWER ===")
print(res.answer)
print("=== SOURCES ===")
for s in res.sources:
    print(s.document_name, "Page", s.page_number, f"{s.similarity_score}%")

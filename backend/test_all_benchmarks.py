import uuid
from app.database import SessionLocal
from app.models.user import User
from app.schemas.rag import ChatRequest
from app.services.rag_chat_pipeline import rag_chat_pipeline

db = SessionLocal()
user_id = uuid.UUID("f1a2138d-cf4a-4152-b51b-8a966911dd11")
leave_doc_id = uuid.UUID("42ac4238-1685-4a0f-8015-f5f492764398")
sugar_doc_id = uuid.UUID("56c4f640-f699-4517-a2d1-f000303d830f")
user = db.query(User).filter(User.id == user_id).first()

test_questions = [
    (
        "A. No remaining leave balance + approval process",
        "An employee has no remaining leave balance but still needs several days off. What option does the policy provide, and how does the approval process work?",
        [leave_doc_id]
    ),
    (
        "B. Extended period to improve qualifications",
        "An employee needs to be away from work for an extended period to improve qualifications related to their job. What option does the policy provide?",
        [leave_doc_id]
    ),
    (
        "C. Ill and needs more sick leave than permitted",
        "An employee becomes ill and needs more sick leave than normally permitted. What additional requirement applies?",
        [leave_doc_id]
    ),
    (
        "D. Joins several months after year started",
        "An employee joins several months after the year has started. How would their leave entitlement be determined?",
        [leave_doc_id]
    ),
    (
        "E. Exception to the leave policy + approval required",
        "If management needs to make an exception to the leave policy, what approval is required?",
        [leave_doc_id]
    ),
]

for title, q, doc_ids in test_questions:
    print("=" * 70)
    print(f"TEST: {title}")
    print(f"QUESTION: {q}")
    req = ChatRequest(question=q, document_ids=doc_ids)
    res = rag_chat_pipeline.execute(db=db, user=user, chat_req=req)
    print("\nRETRIEVED SOURCES:")
    for s in res.sources:
        print(f"  - {s.document_name} | Page {s.page_number} | Match: {s.similarity_score}%")
    print("\nANSWER:")
    print(res.answer)
    print("=" * 70)

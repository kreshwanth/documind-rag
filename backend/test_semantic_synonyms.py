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

synonym_tests = [
    (
        "1. Used all leave / No leave remaining",
        "An employee has used all leave but needs extra time off. What option and approval apply?",
        [leave_doc_id]
    ),
    (
        "2. Further education / Improve qualifications",
        "An employee wants to take time off for further education to improve qualifications. What leave applies?",
        [leave_doc_id]
    ),
    (
        "3. Sick beyond normal limit",
        "An employee is sick beyond the normal limit. What requirement must they fulfill?",
        [leave_doc_id]
    ),
    (
        "4. Joined mid-year / after year started",
        "If someone joined mid-year after the year started, how is leave calculated?",
        [leave_doc_id]
    ),
    (
        "5. Cross-document isolation check",
        "What does the policy state about free sugars intake?",
        [leave_doc_id]  # Must return insufficient information when querying leave policy for sugar questions!
    )
]

for title, q, doc_ids in synonym_tests:
    print("=" * 70)
    print(f"TEST: {title}")
    print(f"QUERY: {q}")
    req = ChatRequest(question=q, document_ids=doc_ids)
    res = rag_chat_pipeline.execute(db=db, user=user, chat_req=req)
    print("\nRETRIEVED CHUNKS COUNT:", res.retrieved_chunks_count)
    print("SOURCES:")
    for s in res.sources:
        print(f"  - {s.document_name} | Page {s.page_number} | Score: {s.similarity_score}")
    print("\nANSWER:")
    print(res.answer)
    print("=" * 70)

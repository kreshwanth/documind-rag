import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from uuid import UUID
from app.database import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.services.rag_chat_pipeline import RAGChatPipeline
from app.schemas.rag import ChatRequest

def test_sabbatical_leave_indirect_retrieval_and_answer():
    """
    Test indirect semantic question for Sabbatical Leave:
    - User asks about long break for education/relevant qualifications.
    - RAG must retrieve Sabbatical Leave section chunks without user explicitly typing 'sabbatical'.
    - RAG must synthesize accurate grounded answer with duration and approval requirements.
    """
    session = SessionLocal()
    try:
        # 1. Fetch Leave Policy Document
        doc = session.query(Document).filter(Document.original_filename.ilike("%Leave%")).first()
        assert doc is not None, "Leave Policy document must exist in the database."
        
        user = session.query(User).filter(User.id == doc.user_id).first()
        assert user is not None, "Document owner user must exist in the database."
        
        question = (
            "An employee wants to take a long break to pursue further education that is relevant to their current job. "
            "What provision in the company’s leave policy could apply to them, and what approval would be required?"
        )
        
        req = ChatRequest(
            question=question,
            document_ids=[doc.id],
            top_k=5
        )
        
        # 2. Execute RAG Pipeline
        response = RAGChatPipeline.execute(db=session, user=user, chat_req=req)
        
        # 3. Assertions
        assert response is not None
        assert not response.is_fallback, "Should not return fallback message"
        
        # Verify top retrieved citations are from Sabbatical Leave sections (Page 2 & 3)
        assert len(response.sources) > 0, "Must return source citations"
        top_citation = response.sources[0]
        assert top_citation.page_number in [2, 3], f"Top citation should be from Page 2 or 3, got Page {top_citation.page_number}"
        
        ans_lower = response.answer.lower()
        assert "sabbatical" in ans_lower, "Answer must mention sabbatical leave"
        assert "qualifications" in ans_lower or "enhance" in ans_lower, "Answer must mention enhancing qualifications"
        assert "one year" in ans_lower or "1 year" in ans_lower, "Answer must mention the duration (up to one year)"
        assert "hod" in ans_lower, "Answer must mention HOD recommendations"
        assert "ceo" in ans_lower or "head of hr" in ans_lower, "Answer must mention Head of HR / CEO approval"
        
    finally:
        session.close()

if __name__ == "__main__":
    test_sabbatical_leave_indirect_retrieval_and_answer()
    print("Test passed successfully!")

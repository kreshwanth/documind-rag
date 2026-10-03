from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
from sqlalchemy.orm import Session
from app.models.conversation import Conversation, Message, MessageCitation
from app.models.user import User
from app.services.gemini_service import gemini_service
from app.services.vector_service import vector_service
from app.schemas.rag import CitationOut, RAGQueryResponse
from app.config import settings
import logging

logger = logging.getLogger("documind.rag")

INSUFFICIENT_INFO_FALLBACK = "I could not find sufficient information in the uploaded documents to answer this question."

SYSTEM_PROMPT = """You are DocuMind, an enterprise document intelligence assistant.
Your job is to answer the user's question strictly and solely based on the provided retrieved context.

Rules you MUST follow:
1. Use ONLY the facts directly mentioned in the context below. Do NOT use any external knowledge, assumptions, or hallucinations.
2. If the context does not contain enough facts to answer the question accurately, you MUST respond EXACTLY with:
"I could not find sufficient information in the uploaded documents to answer this question."
3. When formulating your answer, be clear, structured, and factual.
4. Maintain a professional, enterprise-grade tone.
"""

class RAGService:
    @staticmethod
    def query(
        db: Session,
        user: User,
        question: str,
        conversation_id: Optional[UUID] = None,
        document_ids: Optional[List[UUID]] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> RAGQueryResponse:
        """
        Execute full RAG pipeline:
        1. Ensure active conversation.
        2. Generate query embedding.
        3. Retrieve relevant chunks with pgvector cosine similarity and user isolation.
        4. Apply similarity cutoff & fallback logic.
        5. Build grounded prompt and generate answer via Gemini.
        6. Persist messages and citations in DB.
        """
        effective_top_k = top_k or settings.DEFAULT_TOP_K
        effective_threshold = similarity_threshold if similarity_threshold is not None else settings.DEFAULT_SIMILARITY_THRESHOLD

        # 1. Manage Conversation Session
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id
            ).first()
            if not conversation:
                conversation = Conversation(
                    id=conversation_id,
                    user_id=user.id,
                    title=question[:40] + ("..." if len(question) > 40 else "")
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
        else:
            conversation = Conversation(
                user_id=user.id,
                title=question[:40] + ("..." if len(question) > 40 else "")
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # 2. Embed user question
        query_embedding = gemini_service.get_query_embedding(question)

        # 3. Vector similarity search in PostgreSQL (pgvector)
        hits = vector_service.similarity_search(
            db=db,
            query_embedding=query_embedding,
            user_id=user.id,
            document_ids=document_ids,
            top_k=effective_top_k,
            similarity_threshold=effective_threshold
        )

        # 4. Check if any relevant chunks were retrieved
        if not hits:
            answer = INSUFFICIENT_INFO_FALLBACK
            is_fallback = True
            citations_out: List[CitationOut] = []
        else:
            # Build Grounded Context
            context_blocks = []
            citations_out = []
            for hit in hits:
                context_blocks.append(
                    f"--- Source: {hit['document_name']} (Page {hit['page_number']}) ---\n{hit['content']}"
                )
                citations_out.append(CitationOut(
                    document_id=hit["document_id"],
                    document_name=hit["document_name"],
                    page_number=hit["page_number"],
                    chunk_index=hit["chunk_index"],
                    similarity_score=hit["similarity_score"],
                    snippet=hit["content"][:200] + ("..." if len(hit["content"]) > 200 else "")
                ))

            context_str = "\n\n".join(context_blocks)
            user_prompt = f"""Context from uploaded documents:
{context_str}

User Question: {question}

Answer:"""

            # 5. Generate grounded response from Gemini
            raw_answer = gemini_service.generate_grounded_answer(
                prompt=user_prompt,
                system_instruction=SYSTEM_PROMPT
            )
            
            # Check if answer triggered the standard negative response
            if INSUFFICIENT_INFO_FALLBACK.lower() in raw_answer.lower():
                answer = INSUFFICIENT_INFO_FALLBACK
                is_fallback = True
            else:
                answer = raw_answer
                is_fallback = False

        # 6. Save User message & Assistant message + Citations in Database
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=question
        )
        db.add(user_msg)

        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer
        )
        db.add(assistant_msg)
        db.flush()

        # Save Citations if not fallback
        if not is_fallback:
            for cit in citations_out:
                citation_record = MessageCitation(
                    message_id=assistant_msg.id,
                    chunk_id=cit.document_id,  # references chunk or document
                    document_name=cit.document_name,
                    page_number=cit.page_number,
                    chunk_index=cit.chunk_index,
                    similarity_score=cit.similarity_score,
                    snippet=cit.snippet
                )
                db.add(citation_record)

        db.commit()
        db.refresh(assistant_msg)

        return RAGQueryResponse(
            answer=answer,
            citations=citations_out if not is_fallback else [],
            conversation_id=conversation.id,
            message_id=assistant_msg.id,
            retrieved_chunks_count=len(hits),
            is_fallback=is_fallback
        )

rag_service = RAGService()

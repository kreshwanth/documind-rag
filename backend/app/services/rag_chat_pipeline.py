from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.conversation import Conversation, Message, MessageCitation
from app.schemas.rag import ChatRequest, ChatResponse, SourceCitation
from app.services.embedding_service import embedding_service
from app.services.vector_search_service import vector_search_service
from app.services.context_builder import context_builder
from app.services.prompt_builder import prompt_builder, FALLBACK_RESPONSE_STRING
from app.services.llm_service import llm_service
from app.services.citation_formatter import citation_formatter
from app.config import settings
import logging

logger = logging.getLogger("documind.rag_chat")

class RAGChatPipeline:
    @staticmethod
    def execute(db: Session, user: User, chat_req: ChatRequest) -> ChatResponse:
        """
        Execute full RAG Q&A workflow:
        1. Resolve conversation thread.
        2. Generate query embedding vector.
        3. Search pgvector for relevant chunks belonging strictly to user.
        4. Apply top-K and similarity thresholding.
        5. If chunks found -> build grounded context, build prompt, call Gemini, format citations.
           If NO chunks found -> do not call LLM; return exact fallback response.
        6. Persist conversation and message history.
        """
        # 1. Conversation Session
        if chat_req.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == chat_req.conversation_id,
                Conversation.user_id == user.id
            ).first()
            if not conversation:
                conversation = Conversation(
                    id=chat_req.conversation_id,
                    user_id=user.id,
                    title=chat_req.question[:40] + ("..." if len(chat_req.question) > 40 else "")
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
        else:
            conversation = Conversation(
                user_id=user.id,
                title=chat_req.question[:40] + ("..." if len(chat_req.question) > 40 else "")
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # 2. Generate query embedding
        query_vector = embedding_service.embed_query(chat_req.question)

        # 3. Vector search via pgvector / Hybrid BM25
        retrieved_chunks = vector_search_service.search(
            db=db,
            user_id=user.id,
            query_embedding=query_vector,
            top_k=chat_req.top_k,
            similarity_threshold=chat_req.similarity_threshold,
            document_ids=chat_req.document_ids,
            query_text=chat_req.question
        )

        # 4. Check retrieval result
        if not retrieved_chunks:
            # When no relevant chunks are found, do not call the LLM
            answer = FALLBACK_RESPONSE_STRING
            sources = []
            is_fallback = True
        else:
            # 5. Build context & prompt
            context_block = context_builder.build_context(retrieved_chunks)
            rag_prompt = prompt_builder.build_rag_prompt(context_str=context_block, question=chat_req.question)

            # 6. Call LLM Service
            raw_answer = llm_service.generate_answer(prompt=rag_prompt)
            
            if FALLBACK_RESPONSE_STRING.lower() in raw_answer.lower():
                answer = FALLBACK_RESPONSE_STRING
                sources = []
                is_fallback = True
            else:
                answer = raw_answer
                sources = citation_formatter.format_citations(retrieved_chunks)
                is_fallback = False

        # 7. Persist messages & citations
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=chat_req.question
        )
        db.add(user_message)

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer
        )
        db.add(assistant_message)
        db.flush()

        if not is_fallback:
            for src in sources:
                citation_obj = MessageCitation(
                    message_id=assistant_message.id,
                    chunk_id=src.chunk_id,
                    document_id=src.document_id,
                    document_name=src.document_name,
                    page_number=src.page_number,
                    similarity_score=src.similarity_score,
                    excerpt=src.excerpt or ""
                )
                db.add(citation_obj)

        db.commit()
        db.refresh(assistant_message)

        return ChatResponse(
            answer=answer,
            sources=sources,
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            retrieved_chunks_count=len(retrieved_chunks),
            is_fallback=is_fallback
        )

rag_chat_pipeline = RAGChatPipeline()

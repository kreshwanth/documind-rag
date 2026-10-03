from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message, MessageCitation
from app.schemas.conversation import ConversationResponse, ConversationDetailResponse, ConversationCreate, MessageResponse
from app.schemas.rag import SourceCitation
from app.api.deps import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger("documind.conversations_api")

@router.get("", response_model=List[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all chat conversations for authenticated user."""
    convs = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()

    out = []
    for c in convs:
        count = db.query(Message).filter(Message.conversation_id == c.id).count()
        out.append(ConversationResponse(
            id=c.id,
            user_id=c.user_id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=count
        ))
    return out

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conv_in: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation session."""
    conv = Conversation(
        user_id=current_user.id,
        title=conv_in.title
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return ConversationResponse(
        id=conv.id,
        user_id=conv.user_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0
    )

@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full conversation message history and source citations."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    messages = db.query(Message).filter(
        Message.conversation_id == conv.id
    ).order_by(Message.created_at.asc()).all()

    messages_out = []
    for m in messages:
        citations = db.query(MessageCitation).filter(MessageCitation.message_id == m.id).all()
        cit_out = [
            SourceCitation(
                document_id=c.document_id,
                document_name=c.document_name,
                page_number=c.page_number,
                chunk_id=c.chunk_id,
                similarity_score=c.similarity_score,
                excerpt=c.excerpt
            )
            for c in citations
        ]
        messages_out.append(MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
            citations=cit_out
        ))

    return ConversationDetailResponse(
        id=conv.id,
        user_id=conv.user_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=len(messages_out),
        messages=messages_out
    )

@router.delete("/{conversation_id}", status_code=status.HTTP_200_OK)
def delete_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation thread."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    db.delete(conv)
    db.commit()
    return {"message": "Conversation deleted successfully."}

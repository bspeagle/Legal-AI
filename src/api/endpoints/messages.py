"""
API endpoints for message management in Legal AI Virtual Courtroom
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from datetime import datetime
import logging

from src.database.connection import get_session
from src.database.models import Message, Conversation, Participant

# Setup module logger
logger = logging.getLogger(__name__)

router = APIRouter()

# ---- Models for API requests and responses ----

class MessageCreate(BaseModel):
    """Request model for creating a new message"""
    conversation_id: int
    role: str
    content: str
    created_at: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = {}

class MessageResponse(BaseModel):
    """Response model for message information"""
    id: int
    conversation_id: int
    role: str
    content: str
    timestamp: str
    json_data: Optional[Dict[str, Any]] = {}

@router.post("/", response_model=MessageResponse)
async def create_message(
    message: MessageCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new message in a conversation
    """
    try:
        # Verify conversation exists
        result = await session.execute(select(Conversation).filter(Conversation.id == message.conversation_id))
        conversation = result.scalars().first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation with ID {message.conversation_id} not found")
        
        # Create message
        new_message = Message(
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            created_at=datetime.fromisoformat(message.created_at) if message.created_at else datetime.now(),
            json_data=message.json_data or {}
        )
        
        session.add(new_message)
        await session.commit()
        await session.refresh(new_message)
        
        # Format response
        return MessageResponse(
            id=new_message.id,
            conversation_id=new_message.conversation_id,
            role=new_message.role,
            content=new_message.content,
            timestamp=new_message.timestamp.isoformat(),
            json_data=new_message.json_data
        )
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create message: {str(e)}")

@router.get("/", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session)
):
    """
    List all messages, optionally filtered by conversation_id
    """
    try:
        query = select(Message)
        if conversation_id:
            query = query.filter(Message.conversation_id == conversation_id)
        
        result = await session.execute(query)
        messages = result.scalars().all()
        
        return [
            MessageResponse(
                id=message.id,
                conversation_id=message.conversation_id,
                role=message.role,
                content=message.content,
                timestamp=message.timestamp.isoformat(),
                json_data=message.json_data
            )
            for message in messages
        ]
    except Exception as e:
        logger.error(f"Error listing messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list messages: {str(e)}")

@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific message by ID
    """
    try:
        result = await session.execute(select(Message).filter(Message.id == message_id))
        message = result.scalars().first()
        
        if not message:
            raise HTTPException(status_code=404, detail=f"Message with ID {message_id} not found")
        
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at.isoformat(),
            json_data=message.json_data
        )
    except Exception as e:
        logger.error(f"Error retrieving message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve message: {str(e)}")

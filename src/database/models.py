"""
Database models for Legal AI Virtual Courtroom
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .connection import Base

class Case(Base):
    """Case model representing a legal case in the system"""
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    case_type = Column(String(100), nullable=False)  # family, criminal, civil, etc.
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    status = Column(String(50), default="active")  # active, closed, pending
    json_data = Column(JSON)  # Additional case-specific data (formerly metadata)

    # Relationships
    participants = relationship("Participant", back_populates="case")
    documents = relationship("Document", back_populates="case")
    conversations = relationship("Conversation", back_populates="case")


class Participant(Base):
    """Participant model representing a stakeholder in a case"""
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)  # client, opposing_party, judge, etc.
    agent_type = Column(String(100), nullable=False)  # AI model type
    system_prompt = Column(Text)
    json_data = Column(JSON)  # Additional participant-specific data (formerly metadata)

    # Relationships
    case = relationship("Case", back_populates="participants")
    messages = relationship("Message", back_populates="participant")


class Document(Base):
    """Document model for legal documents in a case"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    title = Column(String(255), nullable=False)
    document_type = Column(String(100))  # evidence, affidavit, ruling, etc.
    content = Column(Text)  # Extracted text content
    file_path = Column(String(255))  # Path to stored file
    uploaded_at = Column(DateTime, server_default=func.now())
    json_data = Column(JSON)  # Document metadata (formerly metadata)

    # Relationships
    case = relationship("Case", back_populates="documents")


class Conversation(Base):
    """Conversation model for courtroom interactions"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    title = Column(String(255), nullable=False)
    conversation_type = Column(String(100))  # examination, cross_examination, ruling
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime)
    status = Column(String(50), default="active")  # active, completed
    json_data = Column(JSON)  # Conversation context and settings (formerly metadata)

    # Relationships
    case = relationship("Case", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """Message model for individual messages in conversations"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    participant_id = Column(Integer, ForeignKey("participants.id"))
    content = Column(Text, nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    timestamp = Column(DateTime, server_default=func.now())
    json_data = Column(JSON)  # Additional message data (formerly metadata)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    participant = relationship("Participant", back_populates="messages")


class Scenario(Base):
    """Scenario model for simulations within conversations"""
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("conversations.id"))
    scenario = Column(Text, nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, server_default=func.now())
    json_data = Column(JSON)  # Additional scenario data

    # Relationships
    simulation = relationship("Conversation", foreign_keys=[simulation_id])

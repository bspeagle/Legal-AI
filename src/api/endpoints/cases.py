"""
API endpoints for case management in Legal AI Virtual Courtroom
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.connection import get_session
from src.database.models import Case, Participant, Document, Conversation

router = APIRouter()

# ---- Models for API requests and responses ----

class CaseCreate(BaseModel):
    """Request model for creating a new case"""
    title: str
    case_type: str
    description: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = {}
    
class CaseUpdate(BaseModel):
    """Request model for updating a case"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = None

class CaseResponse(BaseModel):
    """Response model for case information"""
    id: int
    title: str
    case_type: str
    description: Optional[str] = None
    status: str
    created_at: str
    updated_at: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = {}

class CaseDetailResponse(CaseResponse):
    """Response model for detailed case information"""
    participants: List[Dict[str, Any]] = []
    documents: List[Dict[str, Any]] = []
    conversations: List[Dict[str, Any]] = []

# ---- API Endpoints ----

@router.post("/", response_model=CaseResponse)
async def create_case(case: CaseCreate, session: AsyncSession = Depends(get_session)):
    """
    Create a new case
    """
    try:
        new_case = Case(
            title=case.title,
            case_type=case.case_type,
            description=case.description,
            json_data=case.json_data
        )
        
        session.add(new_case)
        await session.commit()
        await session.refresh(new_case)
        
        return CaseResponse(
            id=new_case.id,
            title=new_case.title,
            case_type=new_case.case_type,
            description=new_case.description,
            status=new_case.status,
            created_at=str(new_case.created_at),
            updated_at=str(new_case.updated_at) if new_case.updated_at else None,
            json_data=new_case.json_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create case: {str(e)}")

@router.get("/", response_model=List[CaseResponse])
async def list_cases(
    status: Optional[str] = Query(None),
    case_type: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    """
    List all cases with optional filtering
    """
    try:
        query = select(Case)
        
        # Apply filters if provided
        if status:
            query = query.filter(Case.status == status)
        if case_type:
            query = query.filter(Case.case_type == case_type)
            
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await session.execute(query)
        cases = result.scalars().all()
        
        return [
            CaseResponse(
                id=case.id,
                title=case.title,
                case_type=case.case_type,
                description=case.description,
                status=case.status,
                created_at=str(case.created_at),
                updated_at=str(case.updated_at) if case.updated_at else None,
                json_data=case.json_data
            )
            for case in cases
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list cases: {str(e)}")

@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case(case_id: int, session: AsyncSession = Depends(get_session)):
    """
    Get detailed information about a specific case
    """
    try:
        # Get case
        result = await session.execute(select(Case).filter(Case.id == case_id))
        case = result.scalars().first()
        
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
            
        # Get participants
        result = await session.execute(select(Participant).filter(Participant.case_id == case_id))
        participants = result.scalars().all()
        
        # Get documents
        result = await session.execute(select(Document).filter(Document.case_id == case_id))
        documents = result.scalars().all()
        
        # Get conversations
        result = await session.execute(select(Conversation).filter(Conversation.case_id == case_id))
        conversations = result.scalars().all()
        
        # Format response
        return CaseDetailResponse(
            id=case.id,
            title=case.title,
            case_type=case.case_type,
            description=case.description,
            status=case.status,
            created_at=str(case.created_at),
            updated_at=str(case.updated_at) if case.updated_at else None,
            json_data=case.json_data,
            participants=[{
                "id": p.id,
                "name": p.name,
                "role": p.role,
                "agent_type": p.agent_type
            } for p in participants],
            documents=[{
                "id": d.id,
                "title": d.title,
                "document_type": d.document_type,
                "uploaded_at": str(d.uploaded_at)
            } for d in documents],
            conversations=[{
                "id": c.id,
                "title": c.title,
                "conversation_type": c.conversation_type,
                "status": c.status,
                "started_at": str(c.started_at)
            } for c in conversations]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get case: {str(e)}")

@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(case_id: int, case: CaseUpdate, session: AsyncSession = Depends(get_session)):
    """
    Update an existing case
    """
    try:
        # Get case
        result = await session.execute(select(Case).filter(Case.id == case_id))
        db_case = result.scalars().first()
        
        if not db_case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
        
        # Update fields if provided
        if case.title is not None:
            db_case.title = case.title
        if case.description is not None:
            db_case.description = case.description
        if case.status is not None:
            db_case.status = case.status
        if case.json_data is not None:
            db_case.json_data = case.json_data
            
        await session.commit()
        await session.refresh(db_case)
        
        return CaseResponse(
            id=db_case.id,
            title=db_case.title,
            case_type=db_case.case_type,
            description=db_case.description,
            status=db_case.status,
            created_at=str(db_case.created_at),
            updated_at=str(db_case.updated_at) if db_case.updated_at else None,
            json_data=db_case.json_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update case: {str(e)}")

@router.delete("/{case_id}")
async def delete_case(case_id: int, session: AsyncSession = Depends(get_session)):
    """
    Delete a case and all related data
    """
    try:
        # Get case
        result = await session.execute(select(Case).filter(Case.id == case_id))
        db_case = result.scalars().first()
        
        if not db_case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
            
        # Delete case
        await session.delete(db_case)
        await session.commit()
        
        return {"message": f"Case {case_id} successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete case: {str(e)}")

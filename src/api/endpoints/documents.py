"""
API endpoints for document management in Legal AI Virtual Courtroom
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import uuid
from datetime import datetime
import PyPDF2
import io

from src.database.connection import get_session
from src.database.models import Document, Case

router = APIRouter()

# ---- Models for API requests and responses ----

class DocumentCreate(BaseModel):
    """Request model for creating a document reference"""
    case_id: int
    title: str
    document_type: str
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class DocumentResponse(BaseModel):
    """Response model for document information"""
    id: int
    case_id: int
    title: str
    document_type: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    uploaded_at: str
    metadata: Optional[Dict[str, Any]] = {}

class DocumentAnalysisRequest(BaseModel):
    """Request model for document analysis"""
    document_id: int
    analysis_type: str = "standard"  # standard, detailed, summary

class DocumentAnalysisResponse(BaseModel):
    """Response model for document analysis"""
    document_id: int
    title: str
    analysis_result: Dict[str, Any]
    key_points: List[str]
    metadata: Dict[str, Any]

# ---- API Endpoints ----

@router.post("/", response_model=DocumentResponse)
async def create_document(document: DocumentCreate, session: AsyncSession = Depends(get_session)):
    """
    Create a new document reference in the database
    """
    try:
        # Verify case exists
        result = await session.execute(select(Case).filter(Case.id == document.case_id))
        case = result.scalars().first()
        
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {document.case_id} not found")
            
        # Create document
        new_document = Document(
            case_id=document.case_id,
            title=document.title,
            document_type=document.document_type,
            content=document.content,
            metadata=document.metadata
        )
        
        session.add(new_document)
        await session.commit()
        await session.refresh(new_document)
        
        return DocumentResponse(
            id=new_document.id,
            case_id=new_document.case_id,
            title=new_document.title,
            document_type=new_document.document_type,
            content=new_document.content,
            file_path=new_document.file_path,
            uploaded_at=str(new_document.uploaded_at),
            metadata=new_document.metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    case_id: int = Form(...),
    title: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Upload a document file and create document record
    """
    try:
        # Verify case exists
        result = await session.execute(select(Case).filter(Case.id == case_id))
        case = result.scalars().first()
        
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
            
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join("data", "documents", str(case_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
            
        # Extract text if PDF
        content = None
        metadata = {}
        
        if file_extension.lower() == ".pdf":
            try:
                with io.BytesIO(contents) as pdf_file:
                    reader = PyPDF2.PdfReader(pdf_file)
                    content = ""
                    for page in reader.pages:
                        content += page.extract_text() + "\n"
                        
                    metadata = {
                        "page_count": len(reader.pages),
                        "file_size": len(contents),
                        "created_at": datetime.now().isoformat()
                    }
            except Exception as e:
                metadata["extraction_error"] = str(e)
        
        # Create document record
        new_document = Document(
            case_id=case_id,
            title=title,
            document_type=document_type,
            content=content,
            file_path=file_path,
            metadata=metadata
        )
        
        session.add(new_document)
        await session.commit()
        await session.refresh(new_document)
        
        return DocumentResponse(
            id=new_document.id,
            case_id=new_document.case_id,
            title=new_document.title,
            document_type=new_document.document_type,
            content=new_document.content,
            file_path=new_document.file_path,
            uploaded_at=str(new_document.uploaded_at),
            metadata=new_document.metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, session: AsyncSession = Depends(get_session)):
    """
    Get information about a specific document
    """
    try:
        result = await session.execute(select(Document).filter(Document.id == document_id))
        document = result.scalars().first()
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
            
        return DocumentResponse(
            id=document.id,
            case_id=document.case_id,
            title=document.title,
            document_type=document.document_type,
            content=document.content,
            file_path=document.file_path,
            uploaded_at=str(document.uploaded_at),
            metadata=document.metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(
    request: DocumentAnalysisRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Analyze a document using AI
    """
    try:
        # Get document
        result = await session.execute(select(Document).filter(Document.id == request.document_id))
        document = result.scalars().first()
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID {request.document_id} not found")
            
        if not document.content:
            raise HTTPException(status_code=400, detail="Document has no extractable content to analyze")
            
        # Analyze document content using OpenAI
        from openai import OpenAI
        import os
        
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Prepare prompt based on analysis type
        if request.analysis_type == "detailed":
            prompt = (
                f"Perform a detailed legal analysis of the following document titled '{document.title}'. "
                f"Extract all key legal points, obligations, rights, and implications. "
                f"Document type: {document.document_type}\n\n"
                f"{document.content[:8000]}"  # Limit content length
            )
        elif request.analysis_type == "summary":
            prompt = (
                f"Provide a concise summary of the following legal document titled '{document.title}'. "
                f"Focus on the main purpose and key provisions. "
                f"Document type: {document.document_type}\n\n"
                f"{document.content[:8000]}"  # Limit content length
            )
        else:  # standard
            prompt = (
                f"Analyze the following legal document titled '{document.title}'. "
                f"Identify the main legal points and potential implications. "
                f"Document type: {document.document_type}\n\n"
                f"{document.content[:8000]}"  # Limit content length
            )
        
        # Call OpenAI API for analysis
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a legal document analysis assistant specialized in extracting key information from legal documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        analysis_text = response.choices[0].message.content
        
        # Extract key points (simple implementation)
        key_points = [line.strip() for line in analysis_text.split("\n") 
                     if line.strip().startswith("- ") or line.strip().startswith("* ")]
        
        if not key_points:
            # If no bullet points, try to create summary points
            key_points = analysis_text.split(". ")[:5]
            key_points = [p + "." for p in key_points if len(p) > 20]
        
        # Create analysis result
        analysis_result = {
            "full_analysis": analysis_text,
            "document_type": document.document_type,
            "analysis_type": request.analysis_type,
            "analyzed_at": datetime.now().isoformat()
        }
        
        # Update document metadata with analysis info
        if "analyses" not in document.metadata:
            document.metadata["analyses"] = []
            
        document.metadata["analyses"].append({
            "type": request.analysis_type,
            "timestamp": datetime.now().isoformat()
        })
        
        await session.commit()
        
        return DocumentAnalysisResponse(
            document_id=document.id,
            title=document.title,
            analysis_result=analysis_result,
            key_points=key_points,
            metadata={
                "document_type": document.document_type,
                "analysis_type": request.analysis_type
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze document: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(document_id: int, session: AsyncSession = Depends(get_session)):
    """
    Delete a document
    """
    try:
        # Get document
        result = await session.execute(select(Document).filter(Document.id == document_id))
        document = result.scalars().first()
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
        
        # Delete file if exists
        if document.file_path and os.path.exists(document.file_path):
            os.remove(document.file_path)
            
        # Delete document record
        await session.delete(document)
        await session.commit()
        
        return {"message": f"Document {document_id} successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

"""
API endpoints for agent interactions in Legal AI Virtual Courtroom
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.agents.factory import AgentFactory
from src.database.connection import get_session
from src.database.models import Participant
from src.utils.logging_config import log_exception

# Setup module logger
logger = logging.getLogger(__name__)

router = APIRouter()

# ---- Models for API requests and responses ----

class AgentCreateRequest(BaseModel):
    """Request model for creating an agent"""
    agent_type: str
    name: str
    role_params: Dict[str, Any]
    
class AgentResponse(BaseModel):
    """Response model for agent information"""
    id: Optional[int] = None
    name: str
    agent_type: str
    role: str
    
class MessageRequest(BaseModel):
    """Request model for sending a message to an agent"""
    message: str
    
class MessageResponse(BaseModel):
    """Response model for agent message responses"""
    agent_name: str
    message: str
    reasoning: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = {}
    
class SimulationRequest(BaseModel):
    """Request model for simulating a courtroom exchange"""
    case_id: int
    scenario: str
    speaking_order: List[str]

class SimulationResponse(BaseModel):
    """Response model for simulation results"""
    exchanges: List[Dict[str, Any]]

# ---- API Endpoints ----

@router.post("/create", response_model=AgentResponse)
async def create_agent(request: AgentCreateRequest, session: AsyncSession = Depends(get_session)):
    """
    Create a new agent
    """
    try:
        # Create agent using factory
        agent = AgentFactory.create_agent(
            agent_type=request.agent_type,
            name=request.name,
            **request.role_params
        )
        
        # Save agent to database
        db_agent = Participant(
            name=agent.name,
            role=agent.role,
            agent_type=request.agent_type,
            system_prompt=agent.system_prompt,
            metadata={
                "model": agent.model,
                "temperature": agent.temperature,
                **request.role_params
            }
        )
        
        session.add(db_agent)
        await session.commit()
        await session.refresh(db_agent)
        
        return AgentResponse(
            id=db_agent.id,
            name=agent.name,
            agent_type=request.agent_type,
            role=agent.role
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

@router.post("/{agent_id}/message", response_model=MessageResponse)
async def send_message(
    agent_id: int, 
    request: MessageRequest, 
    session: AsyncSession = Depends(get_session)
):
    """
    Send a message to an agent and get a response
    """
    try:
        # Get agent from database
        result = await session.execute(
            f"SELECT * FROM participants WHERE id = {agent_id}"
        )
        db_agent = result.fetchone()
        
        if not db_agent:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
        
        # Create agent using factory
        agent = AgentFactory.create_agent(
            agent_type=db_agent.agent_type,
            name=db_agent.name,
            system_prompt=db_agent.system_prompt,
            **db_agent.json_data
        )
        
        # Process message
        response = await agent.process(request.message)
        
        return MessageResponse(
            agent_name=agent.name,
            message=response.message,
            reasoning=response.reasoning,
            confidence=response.confidence,
            metadata=response.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.post("/simulate", response_model=SimulationResponse)
async def simulate_courtroom_exchange(request: SimulationRequest, session: AsyncSession = Depends(get_session)):
    """
    Simulate an exchange between multiple agents in a courtroom setting
    """
    try:
        # Get case information
        result = await session.execute(
            f"SELECT * FROM cases WHERE id = {request.case_id}"
        )
        case = result.fetchone()
        
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {request.case_id} not found")
        
        # Get participants for this case
        result = await session.execute(
            f"SELECT * FROM participants WHERE case_id = {request.case_id}"
        )
        participants = result.fetchall()
        
        if not participants:
            raise HTTPException(status_code=404, detail="No participants found for this case")
        
        # Create agents
        agents = {}
        for p in participants:
            agents[p.role] = AgentFactory.create_agent(
                agent_type=p.agent_type,
                name=p.name,
                system_prompt=p.system_prompt,
                **p.json_data
            )
        
        # Simulate exchange
        exchanges = await AgentFactory.simulate_exchange(
            agents=agents,
            scenario=request.scenario,
            speaking_order=request.speaking_order
        )
        
        return SimulationResponse(exchanges=exchanges)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to simulate exchange: {str(e)}")

@router.post("/family-court", response_model=Dict[str, AgentResponse])
async def create_family_court_simulation(
    case_details: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """
    Create a complete family court simulation with all required agents
    """
    logger.info(f"Creating family court simulation with case details: {case_details}")
    
    try:
        # Validate required fields
        required_fields = ["client_name", "opposing_name"]
        for field in required_fields:
            if field not in case_details or not case_details[field]:
                logger.error(f"Missing required field in request: {field}")
                raise ValueError(f"Missing required field: {field}")
                
        # Log the key fields we're using
        logger.debug(f"Client name: {case_details.get('client_name')}")
        logger.debug(f"Opposing name: {case_details.get('opposing_name')}")
        logger.debug(f"Case title: {case_details.get('case_title', 'Family Court Case')}")
        logger.debug(f"All case details keys: {list(case_details.keys())}")
        
                
        # Create a new case in the database first
        from src.database.models import Case
        db_case = Case(
            title=case_details.get("case_title", "Family Court Case"),
            case_type="family",
            description=case_details.get("case_description", ""),
            status="active",
            json_data=case_details  # Using json_data instead of metadata
        )
        
        # Commit the case to get its ID
        session.add(db_case)
        await session.commit()
        await session.refresh(db_case)
        
        # Now that we have a case ID, create agents using factory
        # Ensure required name fields exist in case_details
        if not case_details.get("client_name"):
            case_details["client_name"] = "Client"
        if not case_details.get("opposing_name"):
            case_details["opposing_name"] = "Opposing Party"
            
        try:
            agents = AgentFactory.create_family_court_simulation(case_details)
        except Exception as e:
            # Detailed error for debugging
            error_msg = f"Failed to create agents: {str(e)}"
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Save agents to database and prepare response
        response = {}
        for role, agent in agents.items():
            # Map role to correct agent_type for database storage
            # This ensures we store the agent class type, not the role key
            role_to_agent_type = {
                "client": "client",
                "opposing_party": "opposing_party",
                "client_counsel": "legal_counsel",
                "opposing_counsel": "legal_counsel",
                "judge": "judicial"
            }
            
            # Get the correct agent_type from our mapping, fallback to role if not in mapping
            correct_agent_type = role_to_agent_type.get(role, role)
            logger.info(f"Creating DB participant: role={agent.role}, role_key={role}, agent_type={correct_agent_type}")
            
            db_agent = Participant(
                case_id=db_case.id,  # Now we have a valid case ID
                name=agent.name,
                role=agent.role,
                agent_type=correct_agent_type,  # Using mapped agent type
                system_prompt=agent.system_prompt,
                json_data={  # Using json_data instead of metadata
                    "model": agent.model,
                    "temperature": agent.temperature
                }
            )
            
            session.add(db_agent)
            await session.commit()
            await session.refresh(db_agent)
            
            response[role] = AgentResponse(
                id=db_agent.id,
                name=agent.name,
                agent_type=role,
                role=agent.role
            )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create simulation: {str(e)}")

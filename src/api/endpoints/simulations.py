"""
API endpoints for simulation management in Legal AI Virtual Courtroom
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime
import json
import logging

# Setup module logger
logger = logging.getLogger(__name__)

from src.database.connection import get_session
from src.database.models import Case, Conversation, Message, Participant
from src.agents.factory import AgentFactory

router = APIRouter()

# ---- Models for API requests and responses ----

class SimulationCreate(BaseModel):
    """Request model for creating a new simulation"""
    case_id: int
    title: str
    conversation_type: str  # examination, cross_examination, hearing, etc.
    json_data: Optional[Dict[str, Any]] = {}

class SimulationResponse(BaseModel):
    """Response model for simulation information"""
    id: int
    case_id: int
    title: str
    conversation_type: str
    started_at: str
    status: str
    json_data: Optional[Dict[str, Any]] = {}

class MessageCreate(BaseModel):
    """Request model for adding a message to a simulation"""
    participant_id: int
    content: str
    json_data: Optional[Dict[str, Any]] = {}

class MessageResponse(BaseModel):
    """Response model for message information"""
    id: int
    conversation_id: int
    participant_id: int
    participant_name: str
    participant_role: str
    content: str
    timestamp: str
    json_data: Optional[Dict[str, Any]] = {}

class ScenarioRun(BaseModel):
    """Request model for running a scenario in a simulation"""
    scenario: str
    speaking_order: List[str]
    context: Optional[Dict[str, Any]] = {}

class ScenarioResponse(BaseModel):
    """Response model for scenario results"""
    conversation_id: int
    messages: List[MessageResponse]
    json_data: Dict[str, Any]

class OutcomePrediction(BaseModel):
    """Request model for predicting case outcome"""
    case_id: int
    scenario_description: str
    factors: List[Dict[str, Any]]
    focus_areas: Optional[List[str]] = None

class PredictionResponse(BaseModel):
    """Response model for outcome prediction"""
    case_id: int
    likelihood: float
    rationale: str
    key_factors: List[Dict[str, Any]]
    recommendations: List[str]
    json_data: Dict[str, Any]

# ---- API Endpoints ----

@router.get("/", response_model=List[SimulationResponse])
async def get_simulations(case_id: int, session: AsyncSession = Depends(get_session)):
    """
    Get all simulations for a specific case
    """
    try:
        # Verify case exists
        result = await session.execute(select(Case).filter(Case.id == case_id))
        case = result.scalars().first()
        
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
        
        # Get all conversations/simulations for this case
        result = await session.execute(select(Conversation).filter(Conversation.case_id == case_id))
        conversations = result.scalars().all()
        
        # Convert to response models
        simulations = [
            SimulationResponse(
                id=conversation.id,
                case_id=conversation.case_id,
                title=conversation.title,
                conversation_type=conversation.conversation_type,
                started_at=str(conversation.started_at),
                status=conversation.status,
                json_data=conversation.json_data
            ) for conversation in conversations
        ]
        
        return simulations
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve simulations: {str(e)}")

@router.post("/", response_model=SimulationResponse)
async def create_simulation(simulation: SimulationCreate, session: AsyncSession = Depends(get_session)):
    """
    Create a new simulation conversation
    """
    try:
        # Verify case exists
        result = await session.execute(select(Case).filter(Case.id == simulation.case_id))
        case = result.scalars().first()
        
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {simulation.case_id} not found")
            
        # Create conversation
        new_conversation = Conversation(
            case_id=simulation.case_id,
            title=simulation.title,
            conversation_type=simulation.conversation_type,
            json_data=simulation.json_data
        )
        
        session.add(new_conversation)
        await session.commit()
        await session.refresh(new_conversation)
        
        return SimulationResponse(
            id=new_conversation.id,
            case_id=new_conversation.case_id,
            title=new_conversation.title,
            conversation_type=new_conversation.conversation_type,
            started_at=str(new_conversation.started_at),
            status=new_conversation.status,
            json_data=new_conversation.json_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create simulation: {str(e)}")

@router.get("/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(simulation_id: int, session: AsyncSession = Depends(get_session)):
    """
    Get information about a specific simulation
    """
    try:
        result = await session.execute(select(Conversation).filter(Conversation.id == simulation_id))
        conversation = result.scalars().first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Simulation with ID {simulation_id} not found")
            
        return SimulationResponse(
            id=conversation.id,
            case_id=conversation.case_id,
            title=conversation.title,
            conversation_type=conversation.conversation_type,
            started_at=str(conversation.started_at),
            status=conversation.status,
            json_data=conversation.json_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get simulation: {str(e)}")

@router.get("/{simulation_id}/messages", response_model=List[MessageResponse])
async def get_simulation_messages(
    simulation_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    session: AsyncSession = Depends(get_session)
):
    """
    Get all messages in a simulation
    """
    try:
        # Verify simulation exists
        result = await session.execute(select(Conversation).filter(Conversation.id == simulation_id))
        conversation = result.scalars().first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Simulation with ID {simulation_id} not found")
            
        # Get messages with join to get participant name
        query = text(
            """SELECT m.*, p.name as participant_name, p.role as participant_role 
            FROM messages m
            JOIN participants p ON m.participant_id = p.id
            WHERE m.conversation_id = :simulation_id
            ORDER BY m.timestamp
            LIMIT :limit OFFSET :skip
            """
        ).bindparams(
            simulation_id=simulation_id,
            limit=limit,
            skip=skip
        )
        result = await session.execute(query)
        messages = result.fetchall()
        
        return [
            MessageResponse(
                id=message.id,
                conversation_id=message.conversation_id,
                participant_id=message.participant_id,
                participant_name=message.participant_name,
                participant_role=message.participant_role,
                content=message.content,
                timestamp=str(message.timestamp),
                metadata=message.json_data
            )
            for message in messages
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

@router.post("/{simulation_id}/messages", response_model=MessageResponse)
async def add_message(
    simulation_id: int,
    message: MessageCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Add a message to a simulation
    """
    try:
        # Verify simulation exists
        result = await session.execute(select(Conversation).filter(Conversation.id == simulation_id))
        conversation = result.scalars().first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Simulation with ID {simulation_id} not found")
            
        # Verify participant exists
        result = await session.execute(select(Participant).filter(Participant.id == message.participant_id))
        participant = result.scalars().first()
        
        if not participant:
            raise HTTPException(status_code=404, detail=f"Participant with ID {message.participant_id} not found")
            
        # Create message
        new_message = Message(
            conversation_id=simulation_id,
            participant_id=message.participant_id,
            content=message.content,
            role="user" if participant.role == "client" else "assistant",
            json_data=message.json_data
        )
        
        session.add(new_message)
        await session.commit()
        await session.refresh(new_message)
        
        return MessageResponse(
            id=new_message.id,
            conversation_id=new_message.conversation_id,
            participant_id=new_message.participant_id,
            participant_name=participant.name,
            participant_role=participant.role,
            content=new_message.content,
            timestamp=str(new_message.timestamp),
            json_data=new_message.json_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")

@router.post("/{simulation_id}/scenario", response_model=ScenarioResponse)
async def run_scenario(
    simulation_id: int,
    scenario: ScenarioRun,
    session: AsyncSession = Depends(get_session)
):
    """
    Run a scenario in a simulation with multiple agent exchanges
    """
    try:
        # Verify simulation exists
        result = await session.execute(select(Conversation).filter(Conversation.id == simulation_id))
        conversation = result.scalars().first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Simulation with ID {simulation_id} not found")
            
        # Get case ID from simulation
        case_id = conversation.case_id
            
        # Get participants for this case
        query = text(
            "SELECT * FROM participants WHERE case_id = :case_id"
        ).bindparams(case_id=case_id)
        result = await session.execute(query)
        participants = result.fetchall()
        
        if not participants:
            raise HTTPException(status_code=404, detail="No participants found for this case")
        
        # Create agents
        agents = {}
        participants_map = {}
        
        # Map role names to standard agent types for consistent handling
        role_to_agent_type_map = {
            "client_counsel": "legal_counsel",
            "opposing_counsel": "legal_counsel",
            "judge": "judicial"
            # Add other mappings as needed
        }
        
        for p in participants:
            agent_type = p.role
            
            if p.agent_type:
                agent_type = p.agent_type
                
            # Apply role to agent type mapping if exists
            if p.role in role_to_agent_type_map:
                logger.info(f"Mapping participant role '{p.role}' to agent type '{role_to_agent_type_map[p.role]}'")
                agent_type = role_to_agent_type_map[p.role]
            
            # Parse json_data if it's a string
            extra_params = {}
            if p.json_data:
                if isinstance(p.json_data, str):
                    try:
                        extra_params = json.loads(p.json_data)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse json_data for participant {p.name}: {p.json_data}")
                else:
                    extra_params = p.json_data or {}
            
            # Add required default parameters based on agent_type
            if agent_type == "opposing_party":
                # Ensure opposing_party has required parameters
                if 'background' not in extra_params:
                    extra_params['background'] = {"history": "Default background"}
                if 'relationship_to_client' not in extra_params:
                    extra_params['relationship_to_client'] = "ex-spouse"
            
            agents[p.role] = AgentFactory.create_agent(
                agent_type=agent_type,
                name=p.name,
                system_prompt=p.system_prompt,
                **extra_params
            )
            
            participants_map[p.role] = p
        
        # Prepare speaking order with mapped agent roles
        # Ensure speaking_order refers to agent keys that exist in our agents dictionary
        mapped_speaking_order = []
        for speaker in scenario.speaking_order:
            # If the speaking order uses a standard agent type that matches a role in our mapping,
            # we need to use the role as the key instead
            mapped_speaker = speaker
            # Log the speaking order mapping for debugging
            logger.info(f"Processing speaker: {speaker}")
            logger.info(f"Available agent roles: {list(agents.keys())}")
            
            if speaker not in agents:
                logger.warning(f"Speaker '{speaker}' not found in agents dictionary, attempting to map")
                # Check if this is a reverse mapping issue (e.g., "legal_counsel" in speaking_order needs to map to "client_counsel" role)
                for role, agent_type in role_to_agent_type_map.items():
                    if agent_type == speaker and role in agents:
                        mapped_speaker = role
                        logger.info(f"Mapped speaker '{speaker}' to role '{mapped_speaker}'")
                        break
            
            mapped_speaking_order.append(mapped_speaker)
            logger.info(f"Final mapped speaker: {mapped_speaker}")
        
        logger.info(f"Original speaking order: {scenario.speaking_order}")
        logger.info(f"Mapped speaking order: {mapped_speaking_order}")
        
        # Simulate exchange with properly mapped speaking order
        exchanges = await AgentFactory.simulate_exchange(
            agents=agents,
            scenario=scenario.scenario,
            speaking_order=mapped_speaking_order
        )
        
        # Save messages to database
        messages = []
        
        for exchange in exchanges:
            role = exchange["role"]
            speaker_key = exchange["speaker"]
            content = exchange["message"]
            participant = participants_map.get(speaker_key)
            
            if not participant:
                continue
                
            # Create message
            new_message = Message(
                conversation_id=simulation_id,
                participant_id=participant.id,
                content=content,
                role="user" if role == "client" else "assistant",
                json_data={
                    "speaker_key": speaker_key,
                    "scenario_context": scenario.context
                }
            )
            
            session.add(new_message)
            await session.commit()
            await session.refresh(new_message)
            
            messages.append(MessageResponse(
                id=new_message.id,
                conversation_id=new_message.conversation_id,
                participant_id=new_message.participant_id,
                participant_name=participant.name,
                participant_role=participant.role,
                content=new_message.content,
                timestamp=str(new_message.timestamp),
                json_data=new_message.json_data
            ))
        
        # Update conversation metadata
        conversation.json_data = {
            **(conversation.json_data or {}),
            "last_scenario": {
                "scenario": scenario.scenario,
                "speaking_order": scenario.speaking_order,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await session.commit()
        
        return ScenarioResponse(
            conversation_id=simulation_id,
            messages=messages,
            json_data={
                "scenario": scenario.scenario,
                "speaking_order": scenario.speaking_order,
                "participants": [p.name for p in participants]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run scenario: {str(e)}")

@router.post("/{simulation_id}/predict-outcome", response_model=PredictionResponse)
async def predict_outcome(
    simulation_id: int,
    prediction: OutcomePrediction,
    session: AsyncSession = Depends(get_session)
):
    """
    Predict the outcome of a case based on simulation data
    """
    try:
        # Verify simulation exists
        result = await session.execute(select(Conversation).filter(Conversation.id == simulation_id))
        conversation = result.scalars().first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Simulation with ID {simulation_id} not found")
            
        # Get case
        result = await session.execute(select(Case).filter(Case.id == prediction.case_id))
        case = result.scalars().first()
        
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {prediction.case_id} not found")
            
        # Get messages from simulation
        query = text(
            """
            SELECT m.*, p.name as participant_name, p.role as participant_role 
            FROM messages m
            JOIN participants p ON m.participant_id = p.id
            WHERE m.conversation_id = :simulation_id
            ORDER BY m.timestamp
            """
        ).bindparams(simulation_id=simulation_id)
        
        result = await session.execute(query)
        messages = result.fetchall()
        
        # Format messages for analysis
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "speaker": msg.participant_name,
                "role": msg.participant_role,
                "content": msg.content
            })
            
        # Get judicial agent to make prediction
        judge_query = text(
            "SELECT * FROM participants WHERE case_id = :case_id AND role = 'judge'"
        ).bindparams(case_id=case.id)
        
        judge_result = await session.execute(judge_query)
        judge = judge_result.fetchone()
        
        if not judge:
            # Create a temporary judicial agent
            judicial_agent = AgentFactory.create_agent(
                agent_type="judicial",
                name="Judge",
                jurisdiction="Family Court" if case.case_type == "family" else "Court"
            )
        else:
            # Use existing judicial agent
            # Ensure json_data is a dictionary before unpacking
            judge_data = judge.json_data
            if isinstance(judge_data, str):
                try:
                    # Attempt to parse string as JSON
                    import json
                    judge_data = json.loads(judge_data)
                except:
                    judge_data = {}
            elif judge_data is None:
                judge_data = {}
            elif not isinstance(judge_data, dict):
                judge_data = {}
                
            judicial_agent = AgentFactory.create_agent(
                agent_type="judicial",
                name=judge.name,
                system_prompt=judge.system_prompt,
                **judge_data
            )
        
        # Prepare prediction request
        factors_text = "\n".join([
            f"- {factor['name']}: {factor['description']}" 
            for factor in prediction.factors
        ])
        
        focus_text = ""
        if prediction.focus_areas:
            focus_text = "Focus Areas:\n" + "\n".join([
                f"- {area}" for area in prediction.focus_areas
            ])
        
        prediction_prompt = f"""
        Based on the following case information and simulation exchanges, predict the likely outcome of this case.
        
        CASE TYPE: {case.case_type}
        CASE DESCRIPTION: {case.description}
        
        SCENARIO: {prediction.scenario_description}
        
        KEY FACTORS:
        {factors_text}
        
        {focus_text}
        
        PREVIOUS EXCHANGES:
        {formatted_messages[:10]}  # Limit to first 10 exchanges
        
        Please provide:
        1. The likely outcome with a likelihood percentage
        2. Your legal rationale for this prediction
        3. The key factors that influenced your decision
        4. Recommendations for the client
        """
        
        # Generate prediction
        response = await judicial_agent.process(prediction_prompt)
        
        # Parse prediction response (simplified implementation)
        prediction_text = response.message
        likelihood = 0.5  # Default
        rationale = prediction_text
        key_factors = []
        recommendations = []
        
        # Extract likelihood
        import re
        likelihood_matches = re.search(r'(\d+)%', prediction_text)
        if likelihood_matches:
            likelihood = float(likelihood_matches.group(1)) / 100.0
            
        # Extract recommendations (simplified)
        recommendations_section = re.split(r'recommendations|suggestions', prediction_text, flags=re.IGNORECASE)
        if len(recommendations_section) > 1:
            recommendations_text = recommendations_section[1]
            recommendations = [
                line.strip().strip('-').strip() 
                for line in recommendations_text.split('\n') 
                if line.strip() and not line.strip().startswith('#')
            ][:5]  # Limit to 5 recommendations
            
        # Extract key factors (simplified)
        key_factors_text = ""
        for factor in prediction.factors:
            if factor["name"].lower() in prediction_text.lower():
                key_factors.append({
                    "name": factor["name"],
                    "impact": "positive" if "favorable" in prediction_text.lower() else "negative",
                    "weight": "high" if factor["name"].lower() in prediction_text.lower() else "medium"
                })
        
        # Save prediction to conversation metadata
        conversation.json_data = {
            **(conversation.json_data or {}),
            "outcome_prediction": {
                "likelihood": likelihood,
                "timestamp": datetime.now().isoformat(),
                "key_factors": [f["name"] for f in key_factors]
            }
        }
        
        await session.commit()
        
        return PredictionResponse(
            case_id=case.id,
            likelihood=likelihood,
            rationale=rationale,
            key_factors=key_factors,
            recommendations=recommendations[:5] if recommendations else ["No specific recommendations provided"],
            json_data={
                "case_type": case.case_type,
                "prediction_time": datetime.now().isoformat(),
                "model_used": judicial_agent.model
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to predict outcome: {str(e)}")

@router.put("/{simulation_id}", response_model=SimulationResponse)
async def update_simulation(
    simulation_id: int,
    status: Optional[str] = None,
    title: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Update a simulation's status or title
    """
    try:
        # Get simulation
        result = await session.execute(select(Conversation).filter(Conversation.id == simulation_id))
        conversation = result.scalars().first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Simulation with ID {simulation_id} not found")
            
        # Update fields if provided
        if status:
            conversation.status = status
            if status == "completed":
                conversation.ended_at = datetime.now()
                
        if title:
            conversation.title = title
            
        await session.commit()
        await session.refresh(conversation)
        
        return SimulationResponse(
            id=conversation.id,
            case_id=conversation.case_id,
            title=conversation.title,
            conversation_type=conversation.conversation_type,
            started_at=str(conversation.started_at),
            status=conversation.status,
            json_data=conversation.json_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update simulation: {str(e)}")

@router.delete("/{simulation_id}")
async def delete_simulation(simulation_id: int, session: AsyncSession = Depends(get_session)):
    """
    Delete a simulation and all its messages
    """
    try:
        # Get simulation
        result = await session.execute(select(Conversation).filter(Conversation.id == simulation_id))
        conversation = result.scalars().first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Simulation with ID {simulation_id} not found")
            
        # Delete simulation
        await session.delete(conversation)
        await session.commit()
        
        return {"message": f"Simulation {simulation_id} successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete simulation: {str(e)}")

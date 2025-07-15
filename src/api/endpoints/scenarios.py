"""
API endpoints for scenario management in Legal AI Virtual Courtroom
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from datetime import datetime
import logging

from src.database.connection import get_session
from src.database.models import Case, Conversation, Scenario

# Setup module logger
logger = logging.getLogger(__name__)

router = APIRouter()

# ---- Models for API requests and responses ----

class ScenarioCreate(BaseModel):
    """Request model for creating a new scenario"""
    simulation_id: int
    scenario: str
    status: Optional[str] = "pending"
    json_data: Optional[Dict[str, Any]] = {}

class ScenarioResponse(BaseModel):
    """Response model for scenario information"""
    id: int
    simulation_id: int
    scenario: str
    status: str
    created_at: str
    json_data: Optional[Dict[str, Any]] = {}

@router.post("/", response_model=ScenarioResponse)
async def create_scenario(
    scenario: ScenarioCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new scenario for a simulation
    """
    try:
        # Verify simulation exists
        result = await session.execute(select(Conversation).filter(Conversation.id == scenario.simulation_id))
        conversation = result.scalars().first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Simulation with ID {scenario.simulation_id} not found")
        
        # Create scenario
        new_scenario = Scenario(
            simulation_id=scenario.simulation_id,
            scenario=scenario.scenario,
            status=scenario.status,
            created_at=datetime.now(),
            json_data=scenario.json_data or {}
        )
        
        session.add(new_scenario)
        await session.commit()
        await session.refresh(new_scenario)
        
        # Format response
        return ScenarioResponse(
            id=new_scenario.id,
            simulation_id=new_scenario.simulation_id,
            scenario=new_scenario.scenario,
            status=new_scenario.status,
            created_at=new_scenario.created_at.isoformat(),
            json_data=new_scenario.json_data
        )
    except Exception as e:
        logger.error(f"Error creating scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create scenario: {str(e)}")

@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific scenario by ID
    """
    try:
        result = await session.execute(select(Scenario).filter(Scenario.id == scenario_id))
        scenario = result.scalars().first()
        
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Scenario with ID {scenario_id} not found")
        
        return ScenarioResponse(
            id=scenario.id,
            simulation_id=scenario.simulation_id,
            scenario=scenario.scenario,
            status=scenario.status,
            created_at=scenario.created_at.isoformat(),
            json_data=scenario.json_data
        )
    except Exception as e:
        logger.error(f"Error retrieving scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve scenario: {str(e)}")

@router.get("/by-simulation/{simulation_id}", response_model=List[ScenarioResponse])
async def list_scenarios(
    simulation_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    List all scenarios for a simulation
    """
    try:
        result = await session.execute(select(Scenario).filter(Scenario.simulation_id == simulation_id))
        scenarios = result.scalars().all()
        
        return [
            ScenarioResponse(
                id=scenario.id,
                simulation_id=scenario.simulation_id,
                scenario=scenario.scenario,
                status=scenario.status,
                created_at=scenario.created_at.isoformat(),
                json_data=scenario.json_data
            )
            for scenario in scenarios
        ]
    except Exception as e:
        logger.error(f"Error listing scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list scenarios: {str(e)}")

"""
API router definitions for Legal AI Virtual Courtroom
"""
from fastapi import APIRouter
from .endpoints import cases, documents, simulations, agents, messages, scenarios

# Main API router
api_router = APIRouter(prefix="/api")

# Include routers from endpoint modules
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(simulations.router, prefix="/simulations", tags=["simulations"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])

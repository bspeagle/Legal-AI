"""
Agent module initialization for Legal AI Virtual Courtroom
"""
from .base import BaseAgent, AgentResponse, Message
from .client import ClientAgent
from .opposing_party import OpposingPartyAgent
from .legal_counsel import LegalCounselAgent
from .judicial import JudicialAgent
from .factory import AgentFactory

__all__ = [
    'BaseAgent',
    'AgentResponse',
    'Message',
    'ClientAgent',
    'OpposingPartyAgent',
    'LegalCounselAgent',
    'JudicialAgent',
    'AgentFactory'
]

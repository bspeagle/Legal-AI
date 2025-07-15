"""
Mock agents for testing without OpenAI API calls
"""
from typing import Dict, Any, List, Optional
from src.agents.base import BaseAgent, AgentResponse, Message

class MockAgent(BaseAgent):
    """
    Mock agent for testing that doesn't call the OpenAI API
    """
    
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.role = kwargs.get('role', 'mock_agent')
        self.system_prompt = kwargs.get('system_prompt', "You are a test agent")
        self.model = kwargs.get('model', 'gpt-4')
        self.temperature = kwargs.get('temperature', 0.7)
        
    async def process(self, input_text: str) -> AgentResponse:
        """Mock response for testing"""
        return AgentResponse(
            message=f"Mock response from {self.name}",
            reasoning="This is a mock response for testing",
            confidence=1.0,
            metadata={}
        )

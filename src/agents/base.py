"""
Base agent class for Legal AI Virtual Courtroom
"""
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import openai
from openai import AsyncOpenAI  # Import the async client
from pydantic import BaseModel
import logging

# Setup module logger
logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Message model for agent conversations"""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None  # Used for multi-agent conversations


class AgentResponse(BaseModel):
    """Standard response format from agents"""
    message: str
    reasoning: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = {}


class BaseAgent(ABC):
    """Base class for all legal AI agents"""
    
    def __init__(
        self, 
        name: str, 
        role: str, 
        system_prompt: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 1024
    ):
        """
        Initialize the base agent
        
        Args:
            name: Agent name
            role: Legal role (client, opposing_party, judge, etc.)
            system_prompt: System instructions for the agent
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in completion
        """
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.conversation_history: List[Message] = []
        
        # Add system prompt as first message
        self.conversation_history.append(
            Message(role="system", content=system_prompt)
        )
        
        # Initialize OpenAI async client
        self.client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        logger.info(f"Initialized AsyncOpenAI client for agent: {self.name}")
    
    def add_message(self, role: str, content: str, name: Optional[str] = None) -> None:
        """
        Add a message to the conversation history
        
        Args:
            role: Message role (user, assistant, system)
            content: Message content
            name: Optional name for multi-agent conversations
        """
        self.conversation_history.append(
            Message(role=role, content=content, name=name)
        )
    
    def clear_history(self) -> None:
        """Clear conversation history except for system prompt"""
        system_prompt = self.conversation_history[0]
        self.conversation_history = [system_prompt]
    
    @abstractmethod
    async def process(self, message: str) -> AgentResponse:
        """
        Process a message and generate a response
        
        Args:
            message: Input message to process
            
        Returns:
            AgentResponse: The agent's response
        """
        pass
    
    async def _generate_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate completion from OpenAI API
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            str: Generated completion text
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content

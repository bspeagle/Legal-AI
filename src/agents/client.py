"""
Client Agent implementation for Legal AI Virtual Courtroom
"""
import logging
from typing import Dict, Any, List, Optional
from .base import BaseAgent, AgentResponse, Message

# Setup module logger
logger = logging.getLogger(__name__)


class ClientAgent(BaseAgent):
    """
    Client Agent representing a party in legal proceedings
    
    This agent is responsible for:
    - Representing the user's perspective
    - Providing testimony and answers to questions
    - Responding to court inquiries
    - Expressing personal preferences and goals
    """
    
    def __init__(
        self,
        name: str = None,
        background: Dict[str, Any] = None,
        demeanor: str = "respectful",
        emotional_state: str = "calm",
        system_prompt: Optional[str] = None,
        model: str = "gpt-4",
        **kwargs
    ):
        logger.debug(f"Initializing ClientAgent with name={name}, background={background}")
        
        # Validate required parameters
        if name is None:
            logger.error("ClientAgent initialized with name=None, this will cause errors")
            # Provide fallback to prevent attribute error
            name = "Unnamed Client"
            logger.warning(f"Using fallback name: {name}")
            
        # Generate system prompt if not provided
        if system_prompt is None:
            # Create a default system prompt
            system_prompt = f"You are {name}, a client in a legal case. "
        
        # Initialize parent class (BaseAgent)
        logger.debug(f"Initializing BaseAgent parent class with name={name}, role='client'")
        super().__init__(
            name=name,
            role="client",
            system_prompt=system_prompt,
            model=model,
            **kwargs
        )
        
        """
        Initialize the Client Agent
        
        Args:
            name: Client name
            background: Dictionary of background information
            demeanor: General demeanor in court
            emotional_state: Current emotional state
            system_prompt: Custom system prompt (if None, default is used)
            model: OpenAI model to use
            **kwargs: Additional arguments passed to BaseAgent
        """
        self.background = background
        self.demeanor = demeanor
        self.emotional_state = emotional_state
        
        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()
        
        super().__init__(
            name=name,
            role="client",
            system_prompt=system_prompt,
            model=model,
            **kwargs
        )
    
    def _get_default_system_prompt(self) -> str:
        """Generate the default system prompt for the client agent"""
        # Format background information
        background_str = "\n".join([f"- {k}: {v}" for k, v in self.background.items()])
        
        return f"""
        You are {self.name}, a party involved in legal proceedings.
        
        BACKGROUND INFORMATION:
        {background_str}
        
        PERSONALITY AND DEMEANOR:
        You are generally {self.demeanor} in your interactions with the court and other parties.
        Your current emotional state is {self.emotional_state}.
        
        As a client in these proceedings, you should:
        
        1. Answer questions truthfully based on your background and perspective
        2. Express your desired outcomes and concerns
        3. Defer to your legal counsel on matters of law and strategy
        4. Maintain appropriate courtroom behavior
        5. Provide your personal experience and perspective
        
        When speaking:
        - Use first-person perspective ("I believe...", "In my experience...")
        - Express emotions appropriate to your emotional state
        - Reflect your personal priorities and values
        - Maintain your established character traits
        
        Your responses should feel authentic and consistent with your background story.
        """
    
    async def process(self, message: str) -> AgentResponse:
        """
        Process a message and generate a client response
        
        Args:
            message: Input message to process
            
        Returns:
            AgentResponse: The client response
        """
        # Add the user message to conversation history
        self.add_message("user", message)
        
        # Prepare messages for API call
        messages = [msg.dict() for msg in self.conversation_history]
        
        # Generate completion
        response_text = await self._generate_completion(messages)
        
        # Add response to conversation history
        self.add_message("assistant", response_text)
        
        # Create response object
        return AgentResponse(
            message=response_text,
            metadata={
                "demeanor": self.demeanor,
                "emotional_state": self.emotional_state
            }
        )
    
    async def provide_testimony(self, question: str) -> AgentResponse:
        """
        Provide testimony in response to a specific question
        
        Args:
            question: The question being asked
            
        Returns:
            AgentResponse: The testimony response
        """
        # Construct a prompt for testimony
        testimony_prompt = f"""
        You are now under oath in court proceedings.
        
        QUESTION: {question}
        
        Please provide your honest testimony in response to this question.
        Remember to stay in character as {self.name} with your established background and perspective.
        """
        
        # Process the testimony request
        return await self.process(testimony_prompt)
    
    def update_emotional_state(self, new_state: str) -> None:
        """
        Update the client's emotional state
        
        Args:
            new_state: New emotional state
        """
        self.emotional_state = new_state
        
        # Add a system message noting the emotional change
        self.add_message(
            "system", 
            f"Note: {self.name}'s emotional state has changed to {new_state}."
        )

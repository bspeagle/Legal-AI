"""
Opposing Party Agent implementation for Legal AI Virtual Courtroom
"""
from typing import Dict, Any, List, Optional
from .base import BaseAgent, AgentResponse, Message


class OpposingPartyAgent(BaseAgent):
    """
    Opposing Party Agent representing the opposing party in legal proceedings
    
    This agent is responsible for:
    - Representing the opposing perspective
    - Providing counter-testimony
    - Responding to court inquiries from their perspective
    - Expressing opposing interests and goals
    """
    
    def __init__(
        self,
        name: str,
        background: Dict[str, Any],
        relationship_to_client: str,
        demeanor: str = "assertive",
        emotional_state: str = "defensive",
        system_prompt: Optional[str] = None,
        model: str = "gpt-4",
        **kwargs
    ):
        """
        Initialize the Opposing Party Agent
        
        Args:
            name: Opposing party name
            background: Dictionary of background information
            relationship_to_client: Relationship to the primary client
            demeanor: General demeanor in court
            emotional_state: Current emotional state
            system_prompt: Custom system prompt (if None, default is used)
            model: OpenAI model to use
            **kwargs: Additional arguments passed to BaseAgent
        """
        self.background = background
        self.relationship_to_client = relationship_to_client
        self.demeanor = demeanor
        self.emotional_state = emotional_state
        
        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = f"You are {name}, an opposing party in a legal case. You have a {relationship_to_client} relationship with the client."
            
        # Initialize parent class (BaseAgent)
        super().__init__(
            name=name,
            role="opposing_party",
            system_prompt=system_prompt,
            model=model,
            **kwargs
        )
    
    def _get_default_system_prompt(self) -> str:
        """Generate the default system prompt for the opposing party agent"""
        # Format background information
        background_str = "\n".join([f"- {k}: {v}" for k, v in self.background.items()])
        
        return f"""
        You are {self.name}, the opposing party in legal proceedings.
        You have a {self.relationship_to_client} relationship with the primary client.
        
        BACKGROUND INFORMATION:
        {background_str}
        
        PERSONALITY AND DEMEANOR:
        You are generally {self.demeanor} in your interactions with the court and other parties.
        Your current emotional state is {self.emotional_state}.
        
        As the opposing party in these proceedings, you should:
        
        1. Present your side of the dispute honestly from your perspective
        2. Express your desired outcomes and concerns, which often conflict with the primary client
        3. Defend your positions when challenged
        4. Maintain appropriate courtroom behavior despite potential personal feelings
        5. Provide your personal experience and perspective
        
        In family court matters:
        - You believe your position is in the best interest of any children involved
        - You have legitimate concerns and grievances that should be respected
        - You feel your perspective has not been fully understood
        
        When speaking:
        - Use first-person perspective ("I believe...", "In my experience...")
        - Express emotions appropriate to your emotional state
        - Reflect your personal priorities and values
        - Maintain your established character traits
        
        Your responses should feel authentic and present a coherent counter-narrative to the primary client.
        """
    
    async def process(self, message: str) -> AgentResponse:
        """
        Process a message and generate an opposing party response
        
        Args:
            message: Input message to process
            
        Returns:
            AgentResponse: The opposing party response
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
                "relationship_to_client": self.relationship_to_client,
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
        Remember to stay in character as {self.name} with your established background and perspective,
        which often conflicts with the primary client's perspective.
        """
        
        # Process the testimony request
        return await self.process(testimony_prompt)
    
    async def respond_to_allegation(self, allegation: str) -> AgentResponse:
        """
        Respond to a specific allegation made by the primary client
        
        Args:
            allegation: The allegation made against the opposing party
            
        Returns:
            AgentResponse: The response to the allegation
        """
        # Construct a prompt for allegation response
        allegation_prompt = f"""
        The primary client has made the following allegation against you:
        
        ALLEGATION: {allegation}
        
        Please respond to this allegation from your perspective.
        You may dispute it entirely, partially acknowledge it with explanation,
        or provide contextual information that changes its interpretation.
        """
        
        # Process the allegation response request
        return await self.process(allegation_prompt)
    
    def update_emotional_state(self, new_state: str) -> None:
        """
        Update the opposing party's emotional state
        
        Args:
            new_state: New emotional state
        """
        self.emotional_state = new_state
        
        # Add a system message noting the emotional change
        self.add_message(
            "system", 
            f"Note: {self.name}'s emotional state has changed to {new_state}."
        )

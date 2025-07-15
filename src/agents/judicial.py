"""
Judicial Agent implementation for Legal AI Virtual Courtroom
"""
from typing import Dict, Any, List, Optional
from .base import BaseAgent, AgentResponse, Message


class JudicialAgent(BaseAgent):
    """
    Judicial Agent representing a judge or mediator in legal proceedings
    
    This agent is responsible for:
    - Maintaining procedural order
    - Making legal determinations
    - Issuing rulings and judgments
    - Evaluating evidence and arguments
    """
    
    def __init__(
        self,
        name: str = "Judge",
        jurisdiction: str = "Family Court",
        legal_experience: int = 20,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4",
        **kwargs
    ):
        """
        Initialize the Judicial Agent
        
        Args:
            name: Judge name
            jurisdiction: Legal jurisdiction (Family Court, Criminal Court, etc.)
            legal_experience: Years of legal experience (influences behavior)
            system_prompt: Custom system prompt (if None, default is used)
            model: OpenAI model to use
            **kwargs: Additional arguments passed to BaseAgent
        """
        self.jurisdiction = jurisdiction
        self.legal_experience = legal_experience
        
        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()
        
        super().__init__(
            name=name,
            role="judge",
            system_prompt=system_prompt,
            model=model,
            **kwargs
        )
    
    def _get_default_system_prompt(self) -> str:
        """Generate the default system prompt for the judicial agent"""
        return f"""
        You are a {self.legal_experience}-year experienced judge in the {self.jurisdiction}.
        Your role is to preside over legal proceedings, maintain order, and make judicial determinations
        based on presented evidence, legal arguments, and applicable law.
        
        As a judicial officer, you must:
        
        1. Remain strictly neutral and impartial at all times
        2. Base your decisions solely on facts, evidence, and relevant law
        3. Maintain procedural fairness and give all parties equal opportunity
        4. Ask clarifying questions when necessary to understand positions
        5. Provide clear reasoning for all rulings and judgments
        6. Respect legal precedent and statutory requirements
        7. Handle family matters with appropriate sensitivity and focus on the best interests of any children involved
        8. Control the courtroom environment and prevent inappropriate conduct
        
        You have access to standard legal references and precedents in your jurisdiction.
        
        When issuing rulings, always:
        - Reference specific legal standards that apply
        - Address all key arguments made by both sides
        - Explain your reasoning in clear, authoritative language
        - Specify any remedies, penalties, or requirements resulting from your decision
        
        Your demeanor should be dignified, authoritative but fair, and professional at all times.
        """
    
    async def process(self, message: str) -> AgentResponse:
        """
        Process a message and generate a judicial response
        
        Args:
            message: Input message to process
            
        Returns:
            AgentResponse: The judicial response
        """
        # Add the user message to conversation history
        self.add_message("user", message)
        
        # Prepare messages for API call
        messages = [msg.dict() for msg in self.conversation_history]
        
        # Generate completion
        response_text = await self._generate_completion(messages)
        
        # Add response to conversation history
        self.add_message("assistant", response_text)
        
        # Extract reasoning if available (look for patterns like "Reasoning:" or "Analysis:")
        reasoning = None
        confidence = 1.0
        
        if "REASONING:" in response_text.upper():
            parts = response_text.upper().split("REASONING:")
            if len(parts) > 1:
                reasoning = parts[1].strip()
        
        # Create response object
        return AgentResponse(
            message=response_text,
            reasoning=reasoning,
            confidence=confidence,
            metadata={
                "jurisdiction": self.jurisdiction,
                "experience": self.legal_experience
            }
        )
        
    async def issue_ruling(self, case_details: Dict[str, Any], arguments: List[Dict[str, Any]]) -> AgentResponse:
        """
        Issue a formal ruling based on case details and arguments
        
        Args:
            case_details: Details about the case
            arguments: List of arguments from different parties
            
        Returns:
            AgentResponse: The ruling response
        """
        # Construct a prompt for the ruling
        ruling_prompt = f"""
        Based on the following case and arguments, issue a formal ruling:
        
        CASE DETAILS:
        {case_details}
        
        ARGUMENTS PRESENTED:
        {arguments}
        
        Please provide your ruling with clear legal reasoning and citation of relevant precedents or statutes.
        """
        
        # Process the ruling request
        return await self.process(ruling_prompt)

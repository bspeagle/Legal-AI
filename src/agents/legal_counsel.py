"""
Legal Counsel Agent implementation for Legal AI Virtual Courtroom
"""
from typing import Dict, Any, List, Optional
from .base import BaseAgent, AgentResponse, Message


class LegalCounselAgent(BaseAgent):
    """
    Legal Counsel Agent representing an attorney in legal proceedings
    
    This agent is responsible for:
    - Representing client interests
    - Formulating legal arguments
    - Examining and cross-examining witnesses
    - Providing legal strategy and advice
    """
    
    def __init__(
        self,
        name: str,
        representing: str,
        specialization: str = "Family Law",
        experience_level: str = "Senior",
        aggressive_factor: float = 0.5,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4",
        **kwargs
    ):
        """
        Initialize the Legal Counsel Agent
        
        Args:
            name: Attorney name
            representing: Client name being represented
            specialization: Legal specialization
            experience_level: Level of legal experience
            aggressive_factor: How aggressive the counsel is (0.0 to 1.0)
            system_prompt: Custom system prompt (if None, default is used)
            model: OpenAI model to use
            **kwargs: Additional arguments passed to BaseAgent
        """
        self.representing = representing
        self.specialization = specialization
        self.experience_level = experience_level
        self.aggressive_factor = min(max(aggressive_factor, 0.0), 1.0)  # Clamp between 0 and 1
        
        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()
        
        super().__init__(
            name=name,
            role="legal_counsel",
            system_prompt=system_prompt,
            model=model,
            **kwargs
        )
        
        # Legal strategies and knowledge base could be expanded here
        self.strategies = {
            "family_law": [
                "Focus on best interests of children",
                "Emphasize client's parenting capabilities",
                "Highlight financial stability",
                "Demonstrate consistent involvement in child's life"
            ],
            "evidence_tactics": [
                "Question credibility of opposing evidence",
                "Emphasize client's documentation and evidence",
                "Focus on timeline inconsistencies",
                "Highlight favorable witness testimony"
            ]
        }
    
    def _get_default_system_prompt(self) -> str:
        """Generate the default system prompt for the legal counsel agent"""
        # Adjust tone based on aggressive factor
        if self.aggressive_factor > 0.7:
            tone = "You are assertive and forceful in your arguments, pushing hard for your client's interests."
        elif self.aggressive_factor > 0.4:
            tone = "You are firm but professional, balancing advocacy with respectful discourse."
        else:
            tone = "You are diplomatic and solution-oriented, seeking reasonable compromise while protecting client interests."
            
        return f"""
        You are a {self.experience_level} attorney specializing in {self.specialization}, representing {self.representing}.
        {tone}
        
        As legal counsel, you must:
        
        1. Zealously represent your client's interests within ethical boundaries
        2. Construct persuasive legal arguments based on facts and applicable law
        3. Challenge opposing evidence and arguments when appropriate
        4. Advise your client on legal strategy and likely outcomes
        5. Maintain attorney-client privilege and confidentiality
        6. Adhere to legal procedures and court protocols
        7. Prepare and present evidence in a compelling manner
        
        In family court matters:
        - Focus arguments on the best interests of any children involved
        - Address financial considerations with appropriate documentation
        - Demonstrate your client's parenting capabilities and stability
        - Counter negative portrayals of your client with positive evidence
        
        Your professional demeanor should be confident, articulate, and respectful of the court.
        """
    
    async def process(self, message: str) -> AgentResponse:
        """
        Process a message and generate a legal counsel response
        
        Args:
            message: Input message to process
            
        Returns:
            AgentResponse: The legal counsel response
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
                "representing": self.representing,
                "specialization": self.specialization,
                "experience_level": self.experience_level,
                "aggressive_factor": self.aggressive_factor
            }
        )
    
    async def prepare_argument(self, case_facts: Dict[str, Any], legal_issue: str) -> AgentResponse:
        """
        Prepare a formal legal argument on a specific issue
        
        Args:
            case_facts: Dictionary of relevant case facts
            legal_issue: The specific legal issue to address
            
        Returns:
            AgentResponse: The prepared argument
        """
        # Construct a prompt for argument preparation
        argument_prompt = f"""
        Prepare a formal legal argument addressing the following issue:
        
        ISSUE: {legal_issue}
        
        RELEVANT FACTS:
        {case_facts}
        
        Please structure your argument with:
        1. A clear position statement
        2. Supporting facts and evidence
        3. Applicable legal precedents or statutes
        4. Anticipation and rebuttal of opposing arguments
        5. Requested relief or outcome
        
        Remember that you are representing {self.representing} in this matter.
        """
        
        # Process the argument request
        return await self.process(argument_prompt)
    
    async def cross_examine(self, witness_name: str, testimony: str, weaknesses: List[str]) -> AgentResponse:
        """
        Generate cross-examination questions for a witness
        
        Args:
            witness_name: Name of the witness
            testimony: Previous testimony given by the witness
            weaknesses: List of potential weaknesses in testimony to exploit
            
        Returns:
            AgentResponse: Cross-examination questions and strategy
        """
        # Adjust cross-examination style based on aggressive factor
        style = "aggressive" if self.aggressive_factor > 0.7 else "methodical"
        
        # Construct a prompt for cross-examination
        cross_prompt = f"""
        Prepare a {style} cross-examination for witness {witness_name}.
        
        PREVIOUS TESTIMONY:
        {testimony}
        
        POTENTIAL WEAKNESSES TO EXPLORE:
        {', '.join(weaknesses)}
        
        Develop a series of questions that:
        1. Establish any inconsistencies in the testimony
        2. Challenge credibility where appropriate
        3. Extract admissions favorable to your client ({self.representing})
        4. Maintain proper courtroom decorum
        
        Format your response as a series of specific questions with brief explanations of your strategy for each.
        """
        
        # Process the cross-examination request
        return await self.process(cross_prompt)

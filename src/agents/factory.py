"""
Agent Factory for creating and managing agents in Legal AI Virtual Courtroom
"""
from typing import Dict, Any, List, Optional, Type
from .base import BaseAgent
from .client import ClientAgent
from .opposing_party import OpposingPartyAgent
from .legal_counsel import LegalCounselAgent
from .judicial import JudicialAgent
import logging

# Setup module logger
logger = logging.getLogger(__name__)

class AgentFactory:
    """
    Factory class for creating and managing agents
    
    This class provides methods to create various types of agents
    and manages their interactions in the virtual courtroom.
    """
    
    # Registry of available agent types
    _agent_types = {
        "client": ClientAgent,
        "opposing_party": OpposingPartyAgent,
        "legal_counsel": LegalCounselAgent,
        "judicial": JudicialAgent
    }
    
    @classmethod
    def create_agent(cls, agent_type: str, **kwargs) -> BaseAgent:
        """Create an agent of the specified type
        
        Args:
            agent_type: Type of agent to create
            **kwargs: Additional arguments for the agent
            
        Returns:
            BaseAgent: An initialized agent of the specified type
        """
        logger.debug(f"Creating agent of type: {agent_type} with parameters: {kwargs}")
        
        # Ensure name is present for all agents to avoid attribute errors
        if 'name' not in kwargs or kwargs['name'] is None:
            logger.error(f"Missing required 'name' parameter for agent type: {agent_type}")
            # Set a default name based on agent type to prevent attribute errors
            kwargs['name'] = f"Default {agent_type.capitalize()}"
            logger.warning(f"Using default name: {kwargs['name']} for {agent_type}")
        
        try:
            # Map non-standard role names to standard agent types
            agent_type_map = {
                "client": "client",
                "opposing_party": "opposing_party",
                "legal_counsel": "legal_counsel",
                "client_counsel": "legal_counsel",
                "opposing_counsel": "legal_counsel",
                "judicial": "judicial",
                "judge": "judicial"
            }
            
            # Map agent_type if it's one of our non-standard role names
            standard_agent_type = agent_type_map.get(agent_type, agent_type)
            logger.info(f"Agent type '{agent_type}' mapped to standard type '{standard_agent_type}'")
            
            # Add required default parameters based on agent_type
            if standard_agent_type == "legal_counsel" and 'representing' not in kwargs:
                # Default representing to match the agent name
                kwargs['representing'] = kwargs.get('name', 'Client').split("'s Attorney")[0]
                logger.info(f"Setting default 'representing' for legal_counsel: {kwargs['representing']}")
            
            if standard_agent_type == "opposing_party" and 'relationship_to_client' not in kwargs:
                kwargs['relationship_to_client'] = "ex-spouse"
                logger.info(f"Setting default 'relationship_to_client' for opposing_party")
                
            if 'background' not in kwargs and (standard_agent_type == "client" or standard_agent_type == "opposing_party"):
                kwargs['background'] = {"history": "Default background"}
                logger.info(f"Setting default 'background' for {standard_agent_type}")
            
            # Create the appropriate agent type
            if standard_agent_type == "client":
                agent = ClientAgent(**kwargs)
            elif standard_agent_type == "opposing_party":
                agent = OpposingPartyAgent(**kwargs)
            elif standard_agent_type == "legal_counsel":
                agent = LegalCounselAgent(**kwargs)
            elif standard_agent_type == "judicial":
                agent = JudicialAgent(**kwargs)
            else:
                logger.error(f"Unknown agent type: {agent_type}")
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            # Verify name was properly set
            if not hasattr(agent, 'name') or agent.name is None:
                logger.error(f"Agent {agent_type} created but 'name' attribute is missing")
            else:
                logger.debug(f"Successfully created {agent_type} agent with name: {agent.name}")
            
            return agent
        except Exception as e:
            logger.error(f"Error creating {agent_type} agent: {str(e)}")
            raise
        
    @classmethod
    def create_family_court_simulation(cls, case_details: Dict[str, Any]) -> Dict[str, BaseAgent]:
        """
        Create a complete set of agents for a family court simulation
        
        Args:
            case_details: Dictionary with case-specific details
            
        Returns:
            Dict[str, BaseAgent]: Dictionary of created agents
        """
        # Extract relevant case details
        client_name = case_details.get("client_name", "Client")
        opposing_name = case_details.get("opposing_name", "Ex-Spouse")
        relationship = case_details.get("relationship", "ex-spouse")
        client_background = case_details.get("client_background", {})
        opposing_background = case_details.get("opposing_background", {})
        
        # Create the agents
        client = cls.create_agent(
            "client",
            name=client_name,
            background=client_background,
            demeanor="respectful"
        )
        
        opposing_party = cls.create_agent(
            "opposing_party",
            name=opposing_name,
            background=opposing_background,
            relationship_to_client=relationship
        )
        
        client_counsel = cls.create_agent(
            "legal_counsel",
            name=f"{client_name}'s Attorney",
            representing=client_name,
            specialization="Family Law"
        )
        
        opposing_counsel = cls.create_agent(
            "legal_counsel",
            name=f"{opposing_name}'s Attorney",
            representing=opposing_name,
            specialization="Family Law"
        )
        
        judge = cls.create_agent(
            "judicial",
            name="Judge",
            jurisdiction="Family Court"
        )
        
        # Return dictionary of agents
        return {
            "client": client,
            "opposing_party": opposing_party,
            "client_counsel": client_counsel,
            "opposing_counsel": opposing_counsel,
            "judge": judge
        }
    
    @staticmethod
    async def simulate_exchange(
        agents: Dict[str, BaseAgent], 
        scenario: str, 
        speaking_order: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Simulate an exchange between multiple agents
        
        Args:
            agents: Dictionary of agents
            scenario: Scenario description to begin the exchange
            speaking_order: List of agent keys in the order they should speak
            
        Returns:
            List[Dict[str, Any]]: List of responses from each agent
        """
        responses = []
        current_context = scenario
        
        for speaker_key in speaking_order:
            if speaker_key not in agents:
                continue
                
            agent = agents[speaker_key]
            response = await agent.process(current_context)
            
            result = {
                "speaker": speaker_key,
                "name": agent.name,
                "role": agent.role,
                "message": response.message
            }
            
            responses.append(result)
            current_context = f"{current_context}\n\n{agent.name}: {response.message}"
            
        return responses

"""
Base Agent Class

Abstract base class for all code review agents.
"""

from abc import ABC, abstractmethod
from typing import Dict
import autogen


class BaseAgent(ABC):
    """
    Abstract base class for all code review agents
    
    All specialized agents should inherit from this class
    and implement the required methods.
    """
    
    @abstractmethod
    def create_agent(self) -> autogen.AssistantAgent:
        """
        Create and return the AutoGen agent instance
        
        Returns:
            AutoGen AssistantAgent or UserProxyAgent
        """
        pass
    
    @abstractmethod
    def register_functions(self) -> Dict:
        """
        Register tool functions with the agent
        
        Returns:
            Dictionary mapping function names to callable functions
        """
        pass
    
    @abstractmethod
    def analyze(self, code: str) -> Dict:
        """
        Perform high-level analysis on the provided code
        
        Args:
            code: Python source code to analyze
        
        Returns:
            Analysis results dictionary
        """
        pass
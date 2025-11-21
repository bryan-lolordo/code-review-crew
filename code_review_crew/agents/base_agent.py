"""
Base Agent Class

Abstract base class for all code review agents.
Provides common interface and structure.
"""

from abc import ABC, abstractmethod
import autogen
from typing import Dict


class BaseAgent(ABC):
    """
    Abstract base class for all code review agents
    
    All specialized agents should inherit from this class
    and implement the required methods.
    """
    
    @abstractmethod
    def create_agent(self):
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
            Example: {'run_pylint': self.tools['linting'].run_pylint}
        """
        pass
    
    @abstractmethod
    def analyze(self, code: str) -> Dict:
        """
        Perform analysis on the provided code
        
        Args:
            code: Python source code to analyze
        
        Returns:
            Dictionary containing analysis results
        """
        pass
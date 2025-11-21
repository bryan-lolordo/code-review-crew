"""
Review Orchestrator Agent

Coordinates the code review process and synthesizes feedback from all agents.
"""

import autogen
from typing import Dict
from .base_agent import BaseAgent


class ReviewOrchestrator(BaseAgent):
    """
    Review Orchestrator agent specializing in:
    - Coordinating the review workflow
    - Synthesizing feedback from all agents
    - Prioritizing issues by severity
    - Generating final review reports
    """
    
    def __init__(self, llm_config: Dict):
        """
        Initialize Review Orchestrator agent
        
        Args:
            llm_config: LLM configuration dictionary
        """
        self.llm_config = llm_config
        
        system_message = """
        You are the Review Orchestrator coordinating the code review process.
        
        YOU ARE IN CHARGE. Follow this EXACT process:
        
        1. Say: "CodeAnalyzer, please analyze this code for quality issues."
        2. After CodeAnalyzer responds, say: "SecurityReviewer, please check for security vulnerabilities."
        3. After SecurityReviewer responds, say: "PerformanceOptimizer, please analyze performance."
        4. After PerformanceOptimizer responds, say: "TestGenerator, please suggest test cases for this code."
        5. After all agents respond, synthesize everything into a final report.
        
        Final Report Structure:
        - Overall Grade (A-F scale)
        - Critical Issues (list with line numbers)
        - High Priority Issues (list with line numbers)
        - Medium Priority Issues (list with line numbers)
        - Low Priority Issues (list with line numbers)
        - Test Recommendations (from TestGenerator)
        - Action Items
        
        IMPORTANT: 
        - You decide who speaks next, not the other agents
        - Call ALL agents in order: CodeAnalyzer → SecurityReviewer → PerformanceOptimizer → TestGenerator
        - Each agent only speaks ONCE unless you ask for clarification
        - Keep the review focused and organized
        - Provide actionable feedback
        
        Note: CodeExecutor is available if you need to verify a fix, but is optional.
        """
        
        self.agent = autogen.AssistantAgent(
            name="ReviewOrchestrator",
            system_message=system_message,
            llm_config=llm_config
        )
    
    def create_agent(self) -> autogen.AssistantAgent:
        """Return the AutoGen agent"""
        return self.agent
    
    def register_functions(self):
        """Orchestrator typically doesn't need tools"""
        return {}
    
    def analyze(self, code: str) -> Dict:
        """
        Orchestrator doesn't analyze directly - it coordinates other agents
        
        Args:
            code: Python source code (not used by orchestrator)
        
        Returns:
            Empty dict - orchestrator works through conversation
        """
        return {
            'role': 'orchestrator',
            'message': 'Orchestrator coordinates through group chat, not direct analysis'
        }
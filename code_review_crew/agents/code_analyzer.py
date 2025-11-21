"""
Code Analyzer Agent

Specialized agent for analyzing code quality, style, and potential bugs.
Uses Pylint and other linting tools to provide comprehensive code analysis.
"""

import autogen
import re
from typing import Dict, List, Optional
from .base_agent import BaseAgent


class CodeAnalyzer(BaseAgent):
    """
    Code Analyzer agent specializing in:
    - Code smells and anti-patterns
    - PEP 8 style compliance
    - Code readability and maintainability
    - DRY violations
    - SOLID principles
    - Error handling
    """
    
    def __init__(self, llm_config: Dict, tools: Dict):
        """
        Initialize Code Analyzer agent
        
        Args:
            llm_config: LLM configuration dictionary
            tools: Dictionary of tool instances (linting_tool, etc.)
        """
        self.tools = tools
        self.llm_config = llm_config
        
        system_message = """
        You are a Code Analyzer specializing in Python code quality.
        
        Your responsibilities:
        1. Identify code smells and anti-patterns
        2. Check PEP 8 style compliance
        3. Evaluate code readability and maintainability
        4. Detect DRY (Don't Repeat Yourself) violations
        5. Assess SOLID principles adherence
        6. Review error handling practices
        
        Available tools (use if needed):
        - run_pylint: Run Pylint static analysis
        - check_pep8: Check PEP 8 compliance
        - detect_code_smells: Identify common code smells
        
        When reporting issues, use this format for EACH issue:
        - Issue type: (style/bug/smell)
        - Line number: (specific line or range)
        - Description: (what's wrong)
        - Suggested fix: (how to fix it)
        - Severity: (Critical/High/Medium/Low)
        
        IMPORTANT:
        - Provide your complete analysis
        - Do NOT tell the orchestrator what to do next
        - Do NOT call other agents
        - Focus only on code quality issues
        """
        
        self.agent = autogen.AssistantAgent(
            name="CodeAnalyzer",
            system_message=system_message,
            llm_config=llm_config
        )
    
    def create_agent(self) -> autogen.AssistantAgent:
        """Return the AutoGen agent"""
        return self.agent
    
    def register_functions(self):
        """Register tool functions with the agent"""
        function_map = {
            "run_pylint": self.tools['linting'].run_pylint,
            "check_pep8": self.tools['linting'].check_pep8,
            "detect_code_smells": self.detect_code_smells,
        }
        return function_map
    
    def detect_code_smells(self, code: str) -> Dict:
        """
        Detect common code smells in the provided code
        
        Args:
            code: Python source code to analyze
        
        Returns:
            Dictionary containing detected code smells
        """
        smells = {
            'long_method': self._check_long_methods(code),
            'magic_numbers': self._check_magic_numbers(code),
        }
        
        return {
            'total_smells': sum(len(v) for v in smells.values()),
            'smells': smells
        }
    
    def _check_long_methods(self, code: str) -> List[Dict]:
        """Check for methods/functions that are too long (>50 lines)"""
        issues = []
        lines = code.split('\n')
        current_function = None
        function_start = 0
        
        for i, line in enumerate(lines, 1):
            # Simple check for function definitions
            if line.strip().startswith('def '):
                if current_function:
                    # Check previous function length
                    length = i - function_start
                    if length > 50:
                        issues.append({
                            'function': current_function,
                            'line': function_start,
                            'length': length,
                            'description': f'Function is {length} lines long (max recommended: 50)'
                        })
                current_function = line.strip().split('(')[0].replace('def ', '')
                function_start = i
        
        return issues
    
    def _check_magic_numbers(self, code: str) -> List[Dict]:
        """Check for magic numbers (hardcoded numeric values that should be constants)"""
        issues = []
        lines = code.split('\n')
        
        # Look for standalone numbers (excluding 0, 1, -1 which are common)
        number_pattern = r'\b([2-9]\d*|[1-9]\d+)\b'
        
        for i, line in enumerate(lines, 1):
            # Skip comments and strings
            if '#' in line:
                line = line.split('#')[0]
            if line.strip().startswith(('"""', "'''", '"', "'")):
                continue
            
            matches = re.finditer(number_pattern, line)
            for match in matches:
                issues.append({
                    'line': i,
                    'value': match.group(),
                    'description': f'Magic number {match.group()} should be a named constant'
                })
        
        return issues[:5]  # Limit to first 5 to avoid noise
    
    def analyze(self, code: str) -> Dict:
        """
        High-level analysis function
        
        Args:
            code: Python source code to analyze
        
        Returns:
            Comprehensive analysis results
        """
        results = {
            'pylint_results': self.tools['linting'].run_pylint(code),
            'pep8_results': self.tools['linting'].check_pep8(code),
            'code_smells': self.detect_code_smells(code)
        }
        
        return results
"""
Test Generator Agent

Specialized agent for generating unit tests and test cases.
"""

import autogen
import re
from typing import Dict, List
from .base_agent import BaseAgent


class TestGenerator(BaseAgent):
    """
    Test Generator agent specializing in:
    - Unit test generation
    - Edge case identification
    - Test coverage analysis
    - Pytest-style test creation
    """
    
    def __init__(self, llm_config: Dict, tools: Dict = None):
        """
        Initialize Test Generator agent
        
        Args:
            llm_config: LLM configuration dictionary
            tools: Dictionary of tool instances (optional)
        """
        self.tools = tools or {}
        self.llm_config = llm_config
        
        system_message = """
        You are a Test Generator specializing in creating comprehensive unit tests.
        
        Your responsibilities:
        1. Analyze the code to identify functions that need testing
        2. Suggest test cases for each function
        3. Identify edge cases and error conditions
        4. Prioritize tests by importance (CRITICAL, HIGH, MEDIUM, LOW)
        
        For EACH function, suggest:
        - Happy path test (normal valid inputs)
        - Edge case tests (empty, null, boundary conditions)
        - Error handling tests (invalid inputs, exceptions)
        - Security tests (SQL injection, XSS if applicable)
        
        Format your response like this:
        
        Function: function_name
        Test 1: [Priority] Description
        Test 2: [Priority] Description
        ...
        
        Example:
        Function: get_user(username)
        Test 1: [HIGH] Test with valid username returns user data
        Test 2: [CRITICAL] Test with SQL injection attempt is blocked
        Test 3: [MEDIUM] Test with empty string returns None
        Test 4: [MEDIUM] Test with None returns None
        
        Be specific and actionable. Focus on the most important tests first.
        
        IMPORTANT:
        - Provide complete test suggestions
        - Do NOT tell the orchestrator what to do next
        - Focus only on test recommendations
        """
        
        self.agent = autogen.AssistantAgent(
            name="TestGenerator",
            system_message=system_message,
            llm_config=llm_config
        )
    
    def create_agent(self) -> autogen.AssistantAgent:
        """Return the AutoGen agent"""
        return self.agent
    
    def register_functions(self):
        """Register tool functions with the agent"""
        function_map = {
            "identify_test_cases": self.identify_test_cases,
            "generate_test_skeleton": self.generate_test_skeleton,
        }
        return function_map
    
    def identify_test_cases(self, code: str) -> List[Dict]:
        """
        Identify what test cases should be created for the code
        
        Args:
            code: Python source code to analyze
        
        Returns:
            List of test case descriptions
        """
        test_cases = []
        
        # Extract functions from code
        functions = self._extract_functions(code)
        
        for func in functions:
            # Basic test cases for each function
            test_cases.append({
                'function': func['name'],
                'line': func['line'],
                'test_type': 'happy_path',
                'description': f'Test {func["name"]} with valid inputs',
                'priority': 'HIGH'
            })
            
            # Check for edge cases based on function signature
            if 'username' in func['params'] or 'email' in func['params']:
                test_cases.append({
                    'function': func['name'],
                    'test_type': 'validation',
                    'description': f'Test {func["name"]} with invalid/empty input',
                    'priority': 'HIGH'
                })
            
            if any(keyword in func['body'].lower() for keyword in ['query', 'database', 'db']):
                test_cases.append({
                    'function': func['name'],
                    'test_type': 'sql_injection',
                    'description': f'Test {func["name"]} against SQL injection',
                    'priority': 'CRITICAL'
                })
            
            if 'list' in func['params'] or 'items' in func['params']:
                test_cases.extend([
                    {
                        'function': func['name'],
                        'test_type': 'edge_case',
                        'description': f'Test {func["name"]} with empty list',
                        'priority': 'MEDIUM'
                    },
                    {
                        'function': func['name'],
                        'test_type': 'edge_case',
                        'description': f'Test {func["name"]} with single item',
                        'priority': 'MEDIUM'
                    }
                ])
            
            # Error handling tests
            if 'try' in func['body'] or 'except' in func['body']:
                test_cases.append({
                    'function': func['name'],
                    'test_type': 'error_handling',
                    'description': f'Test {func["name"]} error handling',
                    'priority': 'HIGH'
                })
        
        return test_cases
    
    def generate_test_skeleton(self, function_name: str, test_cases: List[Dict]) -> str:
        """
        Generate a test skeleton for a function
        
        Args:
            function_name: Name of the function to test
            test_cases: List of test case descriptions
        
        Returns:
            Pytest test code skeleton
        """
        test_code = f"""import pytest
from your_module import {function_name}


class Test{function_name.title().replace('_', '')}:
    \"\"\"Test suite for {function_name} function\"\"\"
    
"""
        
        # Generate test methods
        for i, test_case in enumerate(test_cases, 1):
            test_name = f"test_{function_name}_{test_case.get('test_type', 'case')}"
            test_code += f"""    def {test_name}(self):
        \"\"\"Test: {test_case.get('description', 'Test case')}\"\"\"
        # Arrange
        # TODO: Set up test data
        
        # Act
        # TODO: Call the function
        result = {function_name}(...)
        
        # Assert
        # TODO: Add assertions
        assert result is not None
    
"""
        
        return test_code
    
    def _extract_functions(self, code: str) -> List[Dict]:
        """
        Extract function definitions from code
        
        Args:
            code: Python source code
        
        Returns:
            List of function information
        """
        functions = []
        lines = code.split('\n')
        current_function = None
        function_body = []
        
        for i, line in enumerate(lines, 1):
            # Detect function definition
            if line.strip().startswith('def '):
                # Save previous function if exists
                if current_function:
                    current_function['body'] = '\n'.join(function_body)
                    functions.append(current_function)
                    function_body = []
                
                # Parse new function
                match = re.match(r'\s*def\s+(\w+)\s*\((.*?)\)', line)
                if match:
                    func_name = match.group(1)
                    params = [p.strip().split(':')[0].strip() for p in match.group(2).split(',') if p.strip()]
                    
                    current_function = {
                        'name': func_name,
                        'line': i,
                        'params': params,
                        'body': ''
                    }
            elif current_function:
                # Accumulate function body
                if line and not line[0].isspace() and not line.strip().startswith('def '):
                    # End of function
                    current_function['body'] = '\n'.join(function_body)
                    functions.append(current_function)
                    current_function = None
                    function_body = []
                else:
                    function_body.append(line)
        
        # Don't forget last function
        if current_function:
            current_function['body'] = '\n'.join(function_body)
            functions.append(current_function)
        
        return functions
    
    def analyze(self, code: str) -> Dict:
        """
        Comprehensive test generation analysis
        
        Args:
            code: Python source code to analyze
        
        Returns:
            Test generation analysis results
        """
        test_cases = self.identify_test_cases(code)
        
        # Group by function
        functions = {}
        for case in test_cases:
            func = case['function']
            if func not in functions:
                functions[func] = []
            functions[func].append(case)
        
        results = {
            'total_test_cases': len(test_cases),
            'functions_analyzed': len(functions),
            'test_cases_by_function': functions,
            'critical_tests': [tc for tc in test_cases if tc.get('priority') == 'CRITICAL'],
            'high_priority_tests': [tc for tc in test_cases if tc.get('priority') == 'HIGH']
        }
        
        return results
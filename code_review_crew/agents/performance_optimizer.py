"""
Performance Optimizer Agent

Specialized agent for analyzing performance and optimization opportunities.
"""

import autogen
import re
from typing import Dict, List
from .base_agent import BaseAgent


class PerformanceOptimizer(BaseAgent):
    """
    Performance Optimizer agent specializing in:
    - Algorithmic complexity analysis
    - Performance bottlenecks
    - Memory optimization
    - Caching opportunities
    """
    
    def __init__(self, llm_config: Dict, tools: Dict):
        """
        Initialize Performance Optimizer agent
        
        Args:
            llm_config: LLM configuration dictionary
            tools: Dictionary of tool instances
        """
        self.tools = tools
        self.llm_config = llm_config
        
        system_message = """
        You are a Performance Optimizer specializing in code performance analysis.
        
        Your responsibilities:
        1. Analyze algorithmic complexity (Big O)
        2. Identify performance bottlenecks
        3. Suggest optimization strategies
        4. Review memory usage
        5. Identify caching opportunities
        6. Detect inefficient patterns
        
        Use available tools:
        - analyze_complexity: Calculate cyclomatic complexity
        - find_bottlenecks: Identify performance issues
        - detect_nested_loops: Find O(n²) or worse complexity
        
        Provide complexity analysis (O(n), O(n²), etc.).
        Balance performance with readability.
        
        When reporting issues:
        - Current complexity
        - Suggested optimization
        - Expected improvement
        - Code example
        """
        
        self.agent = autogen.AssistantAgent(
            name="PerformanceOptimizer",
            system_message=system_message,
            llm_config=llm_config
        )
    
    def create_agent(self) -> autogen.AssistantAgent:
        """Return the AutoGen agent"""
        return self.agent
    
    def register_functions(self):
        """Register tool functions with the agent"""
        function_map = {
            "analyze_complexity": self.tools['complexity'].calculate_complexity,
            "find_bottlenecks": self.tools['complexity'].find_bottlenecks,
            "detect_nested_loops": self.detect_nested_loops,
        }
        return function_map
    
    def detect_nested_loops(self, code: str) -> List[Dict]:
        """
        Detect nested loops which often indicate O(n²) or worse complexity
        
        Args:
            code: Python source code to analyze
        
        Returns:
            List of nested loop issues
        """
        issues = []
        lines = code.split('\n')
        
        loop_stack = []  # Track nested loop depth
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            # Detect loop start
            if stripped.startswith('for ') or stripped.startswith('while '):
                loop_stack.append({'line': i, 'indent': indent, 'type': stripped.split()[0]})
                
                # Check if nested (2+ loops deep)
                if len(loop_stack) >= 2:
                    issues.append({
                        'line': i,
                        'depth': len(loop_stack),
                        'severity': 'HIGH' if len(loop_stack) == 2 else 'CRITICAL',
                        'description': f'Nested loop (depth {len(loop_stack)}) - Likely O(n^{len(loop_stack)}) complexity',
                        'suggestion': 'Consider using hash maps, sets, or other data structures for O(n) complexity'
                    })
            
            # Pop loops when indent decreases
            if loop_stack and indent <= loop_stack[-1]['indent'] and not stripped.startswith(('for ', 'while ')):
                while loop_stack and indent <= loop_stack[-1]['indent']:
                    loop_stack.pop()
        
        return issues
    
    def detect_string_concatenation(self, code: str) -> List[Dict]:
        """
        Detect inefficient string concatenation in loops
        
        Args:
            code: Python source code to analyze
        
        Returns:
            List of string concatenation issues
        """
        issues = []
        lines = code.split('\n')
        
        in_loop = False
        loop_indent = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            # Track if we're in a loop
            if stripped.startswith('for ') or stripped.startswith('while '):
                in_loop = True
                loop_indent = indent
            elif in_loop and indent <= loop_indent:
                in_loop = False
            
            # Check for string concatenation in loop
            if in_loop and ('+=' in stripped or '= ' in stripped and '+' in stripped):
                if any(var in stripped for var in ['str', 'text', 'result', 'output']):
                    issues.append({
                        'line': i,
                        'severity': 'MEDIUM',
                        'description': 'String concatenation in loop - Inefficient for large iterations',
                        'suggestion': 'Use list.append() and join(), or StringIO for better performance'
                    })
        
        return issues
    
    def detect_repeated_calculations(self, code: str) -> List[Dict]:
        """
        Detect calculations that could be cached
        
        Args:
            code: Python source code to analyze
        
        Returns:
            List of caching opportunities
        """
        issues = []
        lines = code.split('\n')
        
        # Look for function calls in loops
        in_loop = False
        loop_line = 0
        function_calls = {}
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped.startswith('for ') or stripped.startswith('while '):
                in_loop = True
                loop_line = i
                function_calls = {}
            elif in_loop and not line.startswith(' '):
                in_loop = False
            
            # Look for function calls
            if in_loop:
                # Simple pattern for function calls
                matches = re.findall(r'(\w+)\(', stripped)
                for func in matches:
                    if func not in ['range', 'len', 'print', 'str', 'int', 'float']:
                        if func in function_calls:
                            function_calls[func] += 1
                        else:
                            function_calls[func] = 1
        
        # Report functions called multiple times
        for func, count in function_calls.items():
            if count > 1:
                issues.append({
                    'line': loop_line,
                    'severity': 'MEDIUM',
                    'description': f'Function {func}() called {count} times in loop',
                    'suggestion': 'Consider caching the result if the function is expensive'
                })
        
        return issues[:3]  # Limit to top 3
    
    def analyze(self, code: str) -> Dict:
        """
        Comprehensive performance analysis
        
        Args:
            code: Python source code to analyze
        
        Returns:
            Performance analysis results
        """
        results = {
            'nested_loops': self.detect_nested_loops(code),
            'string_concat': self.detect_string_concatenation(code),
            'caching_opportunities': self.detect_repeated_calculations(code),
            'complexity_metrics': self.tools['complexity'].calculate_complexity(code),
            'total_issues': 0
        }
        
        results['total_issues'] = (
            len(results['nested_loops']) +
            len(results['string_concat']) +
            len(results['caching_opportunities'])
        )
        
        return results
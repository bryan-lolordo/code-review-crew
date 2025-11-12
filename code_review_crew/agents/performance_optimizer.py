"""
Performance Optimizer Agent

Specialized agent for analyzing code performance and suggesting optimizations.
Uses complexity analysis tools to identify bottlenecks.
"""

import autogen
from typing import Dict, List, Optional
from .base_agent import BaseAgent


class PerformanceOptimizer(BaseAgent):
    """
    Performance Optimizer agent specializing in:
    - Algorithmic complexity (Big O analysis)
    - Memory usage optimization
    - Database query efficiency
    - Loop optimization
    - Caching opportunities
    - Profiling insights
    """
    
    def __init__(self, llm_config: Dict, tools: Dict):
        """
        Initialize Performance Optimizer agent
        
        Args:
            llm_config: LLM configuration dictionary
            tools: Dictionary of tool instances (complexity_analyzer, etc.)
        """
        self.tools = tools
        self.llm_config = llm_config
        
        system_message = """
        You are a Performance Optimizer specializing in code efficiency.
        
        Your responsibilities:
        1. Analyze algorithmic complexity (time and space)
        2. Identify performance bottlenecks
        3. Suggest optimization strategies
        4. Review database query efficiency
        5. Identify caching opportunities
        6. Detect memory leaks
        7. Optimize loops and iterations
        
        Use the available tools:
        - analyze_complexity: Calculate cyclomatic and time complexity
        - find_bottlenecks: Identify performance bottlenecks
        - profile_code: Get profiling insights
        
        For each performance issue:
        - Explain the current complexity (e.g., O(n²))
        - Describe why it's a bottleneck
        - Suggest optimized approach with complexity (e.g., O(n))
        - Provide code example of optimization
        - Balance performance with readability
        
        Prioritize issues by impact:
        - Critical: O(n³) or worse, memory leaks
        - High: O(n²) in hot paths
        - Medium: Inefficient but acceptable
        - Low: Micro-optimizations
        
        Always consider real-world impact, not just theoretical complexity.
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
            "detect_inefficiencies": self.detect_inefficiencies,
        }
        return function_map
    
    def detect_inefficiencies(self, code: str) -> Dict:
        """
        Detect common performance inefficiencies
        
        Args:
            code: Python source code to analyze
        
        Returns:
            Dictionary of detected inefficiencies
        """
        inefficiencies = {
            'nested_loops': self._check_nested_loops(code),
            'string_concat': self._check_string_concatenation(code),
            'repeated_work': self._check_repeated_work(code),
            'inefficient_data_structures': self._check_data_structures(code),
            'no_caching': self._check_caching_opportunities(code)
        }
        
        return {
            'total_issues': sum(len(v) for v in inefficiencies.values()),
            'inefficiencies': inefficiencies
        }
    
    def _check_nested_loops(self, code: str) -> List[Dict]:
        """Check for nested loops that might be O(n²) or worse"""
        issues = []
        lines = code.split('\n')
        
        loop_depth = 0
        loop_stack = []
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Detect loop start
            if stripped.startswith('for ') or stripped.startswith('while '):
                loop_depth += 1
                loop_stack.append(line_num)
                
                if loop_depth >= 2:
                    issues.append({
                        'line': line_num,
                        'depth': loop_depth,
                        'severity': 'High' if loop_depth == 2 else 'Critical',
                        'description': f'Nested loop (depth {loop_depth}) - potential O(n^{loop_depth}) complexity',
                        'suggestion': 'Consider using hash maps, sets, or preprocessing to reduce complexity'
                    })
            
            # Detect loop end (simplified - doesn't handle all cases)
            if loop_depth > 0 and not line.startswith(' ' * (loop_depth * 4)):
                if loop_stack:
                    loop_stack.pop()
                    loop_depth -= 1
        
        return issues
    
    def _check_string_concatenation(self, code: str) -> List[Dict]:
        """Check for inefficient string concatenation in loops"""
        issues = []
        lines = code.split('\n')
        
        in_loop = False
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped.startswith('for ') or stripped.startswith('while '):
                in_loop = True
            
            if in_loop and '+=' in line and ('str' in line or '"' in line or "'" in line):
                issues.append({
                    'line': line_num,
                    'severity': 'Medium',
                    'description': 'String concatenation in loop - O(n²) with string copying',
                    'suggestion': 'Use list.append() and "".join() instead',
                    'example': "result = []; result.append(item); ''.join(result)"
                })
        
        return issues
    
    def _check_repeated_work(self, code: str) -> List[Dict]:
        """Check for repeated calculations or database calls"""
        issues = []
        lines = code.split('\n')
        
        # Check for repeated function calls in loops
        in_loop = False
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped.startswith('for ') or stripped.startswith('while '):
                in_loop = True
            
            if in_loop and any(x in line for x in ['get_', 'fetch_', 'query_', 'load_']):
                issues.append({
                    'line': line_num,
                    'severity': 'High',
                    'description': 'Potential repeated database/network calls in loop',
                    'suggestion': 'Batch requests or cache results outside the loop'
                })
        
        return issues
    
    def _check_data_structures(self, code: str) -> List[Dict]:
        """Check for inefficient data structure usage"""
        issues = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check for 'in list' checks
            if ' in ' in line and 'if ' in line and '[' in line:
                issues.append({
                    'line': line_num,
                    'severity': 'Medium',
                    'description': 'Using "in" operator with list - O(n) lookup',
                    'suggestion': 'Consider using set for O(1) membership testing'
                })
        
        return issues
    
    def _check_caching_opportunities(self, code: str) -> List[Dict]:
        """Identify opportunities for caching/memoization"""
        issues = []
        
        # Check for recursive functions without memoization
        if 'def ' in code and 'return ' in code:
            lines = code.split('\n')
            for line_num, line in enumerate(lines, 1):
                if 'def ' in line:
                    func_name = line.split('def ')[1].split('(')[0]
                    # Check if function calls itself
                    if func_name in code[code.index(line):]:
                        issues.append({
                            'line': line_num,
                            'function': func_name,
                            'severity': 'Medium',
                            'description': 'Recursive function without memoization',
                            'suggestion': 'Add @functools.lru_cache decorator'
                        })
                        break
        
        return issues
    
    def suggest_optimizations(self, code: str, bottlenecks: List[Dict]) -> List[Dict]:
        """
        Generate specific optimization suggestions
        
        Args:
            code: Original code
            bottlenecks: List of identified bottlenecks
        
        Returns:
            List of optimization suggestions with code examples
        """
        suggestions = []
        
        for bottleneck in bottlenecks:
            if 'nested_loops' in bottleneck.get('type', ''):
                suggestions.append({
                    'issue': bottleneck,
                    'optimization': 'Use hash map for O(1) lookups',
                    'example': """
# Instead of:
for item1 in list1:
    for item2 in list2:
        if item1 == item2:
            # process
            
# Use:
set2 = set(list2)
for item1 in list1:
    if item1 in set2:  # O(1) lookup
        # process
"""
                })
        
        return suggestions
    
    def analyze(self, code: str) -> Dict:
        """
        High-level performance analysis function
        
        Args:
            code: Python source code to analyze
        
        Returns:
            Comprehensive performance analysis results
        """
        results = {
            'complexity_analysis': self.tools['complexity'].calculate_complexity(code),
            'bottlenecks': self.tools['complexity'].find_bottlenecks(code),
            'inefficiencies': self.detect_inefficiencies(code)
        }
        
        # Add optimization suggestions
        if results['bottlenecks']:
            results['suggestions'] = self.suggest_optimizations(
                code, 
                results['bottlenecks']
            )
        
        return results
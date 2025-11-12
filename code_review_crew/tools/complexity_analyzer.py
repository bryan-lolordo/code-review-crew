"""
Complexity Analyzer Tool

Wrapper for Radon complexity analysis.
Calculates cyclomatic complexity, maintainability index, and other metrics.
"""

import subprocess
import json
import tempfile
import os
from typing import Dict, List


class ComplexityAnalyzer:
    """Wrapper for Radon complexity analysis tool"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def calculate_complexity(self, code: str) -> Dict:
        """
        Calculate cyclomatic complexity using Radon
        
        Args:
            code: Python source code to analyze
        
        Returns:
            {
                'functions': [
                    {
                        'name': str,
                        'complexity': int,
                        'rank': str (A-F),
                        'line': int,
                        'col': int
                    }
                ],
                'average_complexity': float,
                'maintainability_index': float,
                'total_functions': int
            }
        """
        # Write code to temporary file
        temp_file = os.path.join(self.temp_dir, 'temp_code.py')
        with open(temp_file, 'w') as f:
            f.write(code)
        
        try:
            # Run radon cc (cyclomatic complexity)
            cc_result = subprocess.run(
                ['radon', 'cc', temp_file, '-j'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Run radon mi (maintainability index)
            mi_result = subprocess.run(
                ['radon', 'mi', temp_file, '-j'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse cyclomatic complexity
            complexity_data = {}
            if cc_result.stdout:
                try:
                    complexity_data = json.loads(cc_result.stdout)
                except json.JSONDecodeError:
                    pass
            
            # Parse maintainability index
            mi_data = {}
            if mi_result.stdout:
                try:
                    mi_data = json.loads(mi_result.stdout)
                except json.JSONDecodeError:
                    pass
            
            # Format results
            functions = self._format_complexity_results(complexity_data)
            
            # Calculate average complexity
            avg_complexity = self._calculate_average_complexity(functions)
            
            # Get maintainability index
            mi_score = self._extract_mi_score(mi_data)
            
            return {
                'functions': functions,
                'average_complexity': avg_complexity,
                'maintainability_index': mi_score,
                'total_functions': len(functions),
                'complexity_summary': self._generate_complexity_summary(functions, avg_complexity)
            }
        
        except subprocess.TimeoutExpired:
            return self._empty_complexity_result('Complexity analysis timed out')
        except FileNotFoundError:
            return self._empty_complexity_result('Radon not installed')
        except Exception as e:
            return self._empty_complexity_result(f'Complexity analysis error: {str(e)}')
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def _format_complexity_results(self, data: Dict) -> List[Dict]:
        """Format Radon complexity results"""
        functions = []
        
        for file_path, items in data.items():
            for item in items:
                if item['type'] in ['function', 'method']:
                    functions.append({
                        'name': item['name'],
                        'complexity': item['complexity'],
                        'rank': item['rank'],
                        'line': item['lineno'],
                        'col': item['col_offset'],
                        'severity': self._complexity_to_severity(item['complexity'])
                    })
        
        return functions
    
    def _complexity_to_severity(self, complexity: int) -> str:
        """Map complexity to severity level"""
        if complexity > 20:
            return 'critical'
        elif complexity > 10:
            return 'high'
        elif complexity > 5:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_average_complexity(self, functions: List[Dict]) -> float:
        """Calculate average complexity across all functions"""
        if not functions:
            return 0.0
        
        total = sum(f['complexity'] for f in functions)
        return round(total / len(functions), 2)
    
    def _extract_mi_score(self, data: Dict) -> float:
        """Extract maintainability index score"""
        try:
            for file_path, info in data.items():
                return info.get('mi', 0.0)
        except:
            return 0.0
    
    def _generate_complexity_summary(self, functions: List[Dict], avg: float) -> str:
        """Generate human-readable complexity summary"""
        if not functions:
            return "No functions to analyze."
        
        high_complexity = [f for f in functions if f['complexity'] > 10]
        
        summary = f"Average complexity: {avg}. "
        
        if high_complexity:
            summary += f"{len(high_complexity)} functions have high complexity (>10). "
        else:
            summary += "All functions have acceptable complexity. "
        
        if avg > 10:
            summary += "Consider refactoring for better maintainability."
        
        return summary
    
    def _empty_complexity_result(self, error: str) -> Dict:
        """Return empty result with error"""
        return {
            'functions': [],
            'average_complexity': 0.0,
            'maintainability_index': 0.0,
            'total_functions': 0,
            'complexity_summary': error,
            'error': error
        }
    
    def find_bottlenecks(self, code: str) -> List[Dict]:
        """
        Identify performance bottlenecks in code
        
        Args:
            code: Python source code
        
        Returns:
            List of identified bottlenecks
        """
        bottlenecks = []
        
        # Get complexity analysis
        complexity = self.calculate_complexity(code)
        
        # Find high-complexity functions
        for func in complexity['functions']:
            if func['complexity'] > 10:
                bottlenecks.append({
                    'type': 'high_complexity',
                    'location': f"Function '{func['name']}' at line {func['line']}",
                    'complexity': func['complexity'],
                    'severity': func['severity'],
                    'suggestion': 'Consider refactoring into smaller functions',
                    'impact': 'Harder to maintain and test'
                })
        
        # Find nested loops
        nested_loops = self._find_nested_loops(code)
        bottlenecks.extend(nested_loops)
        
        # Find repeated calculations
        repeated = self._find_repeated_calculations(code)
        bottlenecks.extend(repeated)
        
        return bottlenecks
    
    def _find_nested_loops(self, code: str) -> List[Dict]:
        """Find nested loops that could be performance bottlenecks"""
        bottlenecks = []
        lines = code.split('\n')
        
        loop_depth = 0
        loop_stack = []
        
        for line_num, line in enumerate(lines, 1):
            indent = len(line) - len(line.lstrip())
            stripped = line.strip()
            
            if stripped.startswith('for ') or stripped.startswith('while '):
                loop_depth += 1
                loop_stack.append({'line': line_num, 'indent': indent})
                
                if loop_depth >= 2:
                    complexity_class = 'n^' + str(loop_depth)
                    bottlenecks.append({
                        'type': 'nested_loops',
                        'location': f'Line {line_num}',
                        'depth': loop_depth,
                        'severity': 'high' if loop_depth == 2 else 'critical',
                        'complexity': f'O({complexity_class})',
                        'suggestion': 'Use hash maps, sets, or preprocessing to reduce nesting',
                        'impact': f'Performance degrades rapidly with input size ({complexity_class})'
                    })
            
            # Detect loop end by indentation
            if loop_stack and indent <= loop_stack[-1]['indent'] and not stripped:
                if loop_stack:
                    loop_stack.pop()
                    loop_depth = len(loop_stack)
        
        return bottlenecks
    
    def _find_repeated_calculations(self, code: str) -> List[Dict]:
        """Find repeated calculations that could be cached"""
        bottlenecks = []
        lines = code.split('\n')
        
        in_loop = False
        loop_start = 0
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped.startswith('for ') or stripped.startswith('while '):
                in_loop = True
                loop_start = line_num
            
            if in_loop:
                # Check for function calls that could be cached
                if any(pattern in line for pattern in ['get_', 'fetch_', 'calculate_', 'compute_']):
                    # Simple heuristic: if the same call appears multiple times
                    remaining_lines = lines[line_num:]
                    if sum(1 for l in remaining_lines if stripped in l) > 1:
                        bottlenecks.append({
                            'type': 'repeated_calculation',
                            'location': f'Line {line_num} (inside loop starting at line {loop_start})',
                            'severity': 'medium',
                            'suggestion': 'Cache result before loop or use memoization',
                            'impact': 'Unnecessary repeated work'
                        })
        
        return bottlenecks
    
    def calculate_halstead_metrics(self, code: str) -> Dict:
        """
        Calculate Halstead complexity metrics
        
        Args:
            code: Python source code
        
        Returns:
            Dictionary of Halstead metrics
        """
        temp_file = os.path.join(self.temp_dir, 'temp_code.py')
        with open(temp_file, 'w') as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                ['radon', 'hal', temp_file, '-j'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    # Extract Halstead metrics
                    for file_path, metrics in data.items():
                        return {
                            'volume': metrics.get('volume', 0),
                            'difficulty': metrics.get('difficulty', 0),
                            'effort': metrics.get('effort', 0),
                            'time': metrics.get('time', 0),
                            'bugs': metrics.get('bugs', 0)
                        }
                except json.JSONDecodeError:
                    pass
        except:
            pass
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        return {
            'volume': 0,
            'difficulty': 0,
            'effort': 0,
            'time': 0,
            'bugs': 0,
            'error': 'Could not calculate Halstead metrics'
        }
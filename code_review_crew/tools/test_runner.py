"""
Test Runner Tool

Wrapper for pytest to run tests and collect coverage information.
"""

import subprocess
import tempfile
import os
import json
from typing import Dict, List


class TestRunner:
    """
    Test runner tool using pytest
    
    Features:
    - Run pytest tests
    - Collect test results
    - Generate coverage reports
    - Parse test output
    """
    
    def __init__(self):
        """Initialize the test runner"""
        self.pytest_available = self._check_pytest_available()
    
    def _check_pytest_available(self) -> bool:
        """Check if pytest is installed"""
        try:
            result = subprocess.run(
                ["pytest", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def run_tests(self, test_code: str, source_code: str = None) -> Dict:
        """
        Run pytest tests
        
        Args:
            test_code: Pytest test code
            source_code: Source code being tested (optional)
        
        Returns:
            Test execution results
        """
        if not self.pytest_available:
            return {
                'available': False,
                'message': 'pytest not installed. Install with: pip install pytest',
                'tests_run': 0,
                'passed': 0,
                'failed': 0
            }
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write source code if provided
            if source_code:
                source_file = os.path.join(temp_dir, 'source.py')
                with open(source_file, 'w') as f:
                    f.write(source_code)
            
            # Write test code
            test_file = os.path.join(temp_dir, 'test_code.py')
            with open(test_file, 'w') as f:
                f.write(test_code)
            
            try:
                # Run pytest with verbose output and JSON report
                result = subprocess.run(
                    ['pytest', test_file, '-v', '--tb=short'],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=temp_dir
                )
                
                # Parse output
                output = result.stdout + result.stderr
                results = self._parse_pytest_output(output, result.returncode)
                
                return {
                    'available': True,
                    'status': 'success' if result.returncode == 0 else 'failures',
                    'tests_run': results['tests_run'],
                    'passed': results['passed'],
                    'failed': results['failed'],
                    'skipped': results['skipped'],
                    'output': output,
                    'details': results['details']
                }
            
            except subprocess.TimeoutExpired:
                return {
                    'available': True,
                    'status': 'timeout',
                    'message': 'Test execution timed out (>30s)',
                    'tests_run': 0,
                    'passed': 0,
                    'failed': 0
                }
            
            except Exception as e:
                return {
                    'available': True,
                    'status': 'error',
                    'message': str(e),
                    'tests_run': 0,
                    'passed': 0,
                    'failed': 0
                }
    
    def _parse_pytest_output(self, output: str, exit_code: int) -> Dict:
        """
        Parse pytest output to extract test results
        
        Args:
            output: Pytest output text
            exit_code: Pytest exit code
        
        Returns:
            Parsed test results
        """
        results = {
            'tests_run': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        # Count test results from output
        for line in output.split('\n'):
            if ' PASSED' in line:
                results['passed'] += 1
                results['tests_run'] += 1
                test_name = line.split('::')[-1].split(' ')[0]
                results['details'].append({
                    'name': test_name,
                    'status': 'PASSED'
                })
            elif ' FAILED' in line:
                results['failed'] += 1
                results['tests_run'] += 1
                test_name = line.split('::')[-1].split(' ')[0]
                results['details'].append({
                    'name': test_name,
                    'status': 'FAILED'
                })
            elif ' SKIPPED' in line:
                results['skipped'] += 1
                test_name = line.split('::')[-1].split(' ')[0]
                results['details'].append({
                    'name': test_name,
                    'status': 'SKIPPED'
                })
        
        return results
    
    def run_with_coverage(self, test_code: str, source_code: str) -> Dict:
        """
        Run tests with coverage analysis
        
        Args:
            test_code: Pytest test code
            source_code: Source code to measure coverage
        
        Returns:
            Test results with coverage information
        """
        if not self.pytest_available:
            return {
                'available': False,
                'message': 'pytest not installed'
            }
        
        # Check if pytest-cov is available
        try:
            subprocess.run(['pytest', '--cov', '--version'], 
                         capture_output=True, timeout=5)
            cov_available = True
        except:
            cov_available = False
        
        if not cov_available:
            return {
                'available': True,
                'coverage_available': False,
                'message': 'pytest-cov not installed. Install with: pip install pytest-cov',
                'test_results': self.run_tests(test_code, source_code)
            }
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write source code
            source_file = os.path.join(temp_dir, 'source.py')
            with open(source_file, 'w') as f:
                f.write(source_code)
            
            # Write test code
            test_file = os.path.join(temp_dir, 'test_code.py')
            with open(test_file, 'w') as f:
                f.write(test_code)
            
            try:
                # Run pytest with coverage
                result = subprocess.run(
                    ['pytest', test_file, '--cov=source', '--cov-report=term'],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=temp_dir
                )
                
                output = result.stdout + result.stderr
                
                # Parse coverage from output
                coverage_pct = self._parse_coverage(output)
                
                return {
                    'available': True,
                    'coverage_available': True,
                    'test_results': self._parse_pytest_output(output, result.returncode),
                    'coverage_percentage': coverage_pct,
                    'output': output
                }
            
            except Exception as e:
                return {
                    'available': True,
                    'coverage_available': True,
                    'error': str(e)
                }
    
    def _parse_coverage(self, output: str) -> float:
        """
        Parse coverage percentage from pytest-cov output
        
        Args:
            output: Pytest output with coverage
        
        Returns:
            Coverage percentage
        """
        import re
        
        # Look for coverage percentage in output
        match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
        if match:
            return float(match.group(1))
        
        return 0.0
    
    def validate_test_code(self, test_code: str) -> Dict:
        """
        Validate that test code is syntactically correct
        
        Args:
            test_code: Python test code to validate
        
        Returns:
            Validation results
        """
        try:
            # Try to compile the code
            compile(test_code, '<test>', 'exec')
            
            # Check for pytest conventions
            has_test_functions = 'def test_' in test_code
            has_imports = 'import' in test_code
            has_assertions = 'assert' in test_code
            
            issues = []
            if not has_test_functions:
                issues.append('No test functions found (should start with test_)')
            if not has_assertions:
                issues.append('No assertions found (tests should have assertions)')
            
            return {
                'valid': True,
                'syntax_ok': True,
                'has_test_functions': has_test_functions,
                'has_imports': has_imports,
                'has_assertions': has_assertions,
                'issues': issues
            }
        
        except SyntaxError as e:
            return {
                'valid': False,
                'syntax_ok': False,
                'error': str(e),
                'line': e.lineno,
                'message': e.msg
            }
        
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def generate_test_report(self, test_results: Dict) -> str:
        """
        Generate a formatted test report
        
        Args:
            test_results: Results from run_tests()
        
        Returns:
            Formatted report string
        """
        if not test_results.get('available'):
            return "pytest not available"
        
        report = []
        report.append("=" * 60)
        report.append("TEST EXECUTION REPORT")
        report.append("=" * 60)
        report.append(f"Status: {test_results.get('status', 'unknown')}")
        report.append(f"Tests Run: {test_results.get('tests_run', 0)}")
        report.append(f"Passed: {test_results.get('passed', 0)} ✓")
        report.append(f"Failed: {test_results.get('failed', 0)} ✗")
        report.append(f"Skipped: {test_results.get('skipped', 0)} ⊘")
        
        if test_results.get('details'):
            report.append("\nTest Details:")
            report.append("-" * 60)
            for detail in test_results['details']:
                status_symbol = {
                    'PASSED': '✓',
                    'FAILED': '✗',
                    'SKIPPED': '⊘'
                }.get(detail['status'], '?')
                report.append(f"  {status_symbol} {detail['name']}")
        
        report.append("=" * 60)
        
        return "\n".join(report)
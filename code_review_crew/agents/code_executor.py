"""
Code Executor Agent

Specialized agent for safely executing code and running tests in Docker sandbox.
"""

import autogen
import subprocess
import tempfile
import os
from typing import Dict, List
from .base_agent import BaseAgent


class CodeExecutor(BaseAgent):
    """
    Code Executor agent specializing in:
    - Safe code execution in Docker sandbox
    - Running generated tests
    - Validating fixes
    - Capturing execution results
    """
    
    def __init__(self, llm_config: Dict, tools: Dict = None):
        """
        Initialize Code Executor agent
        
        Args:
            llm_config: LLM configuration dictionary
            tools: Dictionary of tool instances (optional)
        """
        self.tools = tools or {}
        self.llm_config = llm_config
        self.docker_available = self._check_docker()
        
        system_message = """
        You are a Code Executor specializing in safely running code and tests.
        
        Your responsibilities:
        1. Execute code in isolated Docker sandbox
        2. Run generated tests using pytest
        3. Validate proposed fixes
        4. Report execution results and errors
        5. Check code actually works as intended
        6. Provide runtime feedback
        
        Execution Guidelines:
        - Always run code in isolated environment
        - Set resource limits (CPU, memory, time)
        - Capture stdout, stderr, and exit codes
        - Report failures clearly
        - Never execute obviously malicious code
        - Timeout after 30 seconds max
        
        When reporting results:
        - Success/failure status
        - Output produced
        - Errors encountered
        - Execution time
        - Resource usage
        """
        
        # For code execution, use UserProxyAgent instead of AssistantAgent
        self.agent = autogen.UserProxyAgent(
            name="CodeExecutor",
            system_message=system_message,
            code_execution_config=False,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0
        )
    
    def create_agent(self) -> autogen.UserProxyAgent:
        """Return the AutoGen agent"""
        return self.agent
    
    def register_functions(self):
        """Register tool functions with the agent"""
        function_map = {
            "execute_code": self.execute_code,
            "run_tests": self.run_tests,
            "validate_fix": self.validate_fix,
        }
        return function_map
    
    def _check_docker(self) -> bool:
        """
        Check if Docker is available
        
        Returns:
            True if Docker is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def execute_code(self, code: str, timeout: int = 10) -> Dict:
        """
        Execute Python code safely
        
        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds
        
        Returns:
            Execution results
        """
        if not self.docker_available:
            return {
                'status': 'skipped',
                'message': 'Docker not available - code execution disabled for safety',
                'stdout': '',
                'stderr': '',
                'exit_code': -1
            }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute in Docker container
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "-v", f"{temp_file}:/code.py",
                    "--memory", "256m",
                    "--cpus", "0.5",
                    "--network", "none",
                    "python:3.9-slim",
                    "python", "/code.py"
                ],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_code': result.returncode
            }
        
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'message': f'Execution exceeded {timeout} seconds',
                'stdout': '',
                'stderr': 'Timeout',
                'exit_code': -1
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'stdout': '',
                'stderr': str(e),
                'exit_code': -1
            }
        
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def run_tests(self, test_code: str, source_code: str = "") -> Dict:
        """
        Run pytest tests
        
        Args:
            test_code: Pytest test code
            source_code: Source code being tested (optional)
        
        Returns:
            Test execution results
        """
        if not self.docker_available:
            return {
                'status': 'skipped',
                'message': 'Docker not available - test execution disabled',
                'tests_run': 0,
                'passed': 0,
                'failed': 0
            }
        
        # Create temporary directory with test and source files
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
                # Run pytest in Docker
                result = subprocess.run(
                    [
                        "docker", "run", "--rm",
                        "-v", f"{temp_dir}:/tests",
                        "--memory", "256m",
                        "--cpus", "0.5",
                        "--network", "none",
                        "python:3.9-slim",
                        "sh", "-c",
                        "pip install pytest -q && pytest /tests -v"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Parse pytest output
                output = result.stdout + result.stderr
                passed = output.count(' PASSED')
                failed = output.count(' FAILED')
                
                return {
                    'status': 'success' if result.returncode == 0 else 'failures',
                    'tests_run': passed + failed,
                    'passed': passed,
                    'failed': failed,
                    'output': output
                }
            
            except subprocess.TimeoutExpired:
                return {
                    'status': 'timeout',
                    'message': 'Test execution timed out',
                    'tests_run': 0,
                    'passed': 0,
                    'failed': 0
                }
            
            except Exception as e:
                return {
                    'status': 'error',
                    'message': str(e),
                    'tests_run': 0,
                    'passed': 0,
                    'failed': 0
                }
    
    def validate_fix(self, original_code: str, fixed_code: str, test_code: str = None) -> Dict:
        """
        Validate that a fix doesn't break functionality
        
        Args:
            original_code: Original code
            fixed_code: Fixed code
            test_code: Optional test code to validate behavior
        
        Returns:
            Validation results
        """
        results = {
            'original_execution': self.execute_code(original_code),
            'fixed_execution': self.execute_code(fixed_code),
        }
        
        if test_code:
            results['tests'] = self.run_tests(test_code, fixed_code)
        
        # Compare results
        original_success = results['original_execution']['status'] == 'success'
        fixed_success = results['fixed_execution']['status'] == 'success'
        
        if fixed_success and not original_success:
            results['verdict'] = 'improvement'
            results['message'] = 'Fix improves code - now executes successfully'
        elif fixed_success and original_success:
            results['verdict'] = 'maintained'
            results['message'] = 'Fix maintains functionality'
        elif not fixed_success and original_success:
            results['verdict'] = 'regression'
            results['message'] = 'WARNING: Fix breaks working code'
        else:
            results['verdict'] = 'both_broken'
            results['message'] = 'Both versions have issues'
        
        return results
    
    def analyze(self, code: str) -> Dict:
        """
        Analyze code executability
        
        Args:
            code: Python source code to analyze
        
        Returns:
            Analysis of code execution potential
        """
        # Try to execute the code
        execution_result = self.execute_code(code, timeout=5)
        
        results = {
            'docker_available': self.docker_available,
            'execution_result': execution_result,
            'can_execute': execution_result['status'] in ['success', 'error'],
            'recommendation': ''
        }
        
        if not self.docker_available:
            results['recommendation'] = 'Install Docker for safe code execution'
        elif execution_result['status'] == 'success':
            results['recommendation'] = 'Code executes successfully'
        elif execution_result['status'] == 'error':
            results['recommendation'] = f"Code has runtime errors: {execution_result['stderr']}"
        elif execution_result['status'] == 'timeout':
            results['recommendation'] = 'Code takes too long to execute - potential infinite loop'
        
        return results
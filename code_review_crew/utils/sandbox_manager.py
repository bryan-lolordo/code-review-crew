"""
Sandbox Manager Utility

Manages Docker containers for safe code execution.
Provides isolated environments with resource limits and timeouts.
"""

import subprocess
import tempfile
import os
import time
import json
from typing import Dict, Optional, List
import uuid


class SandboxManager:
    """Manages Docker sandbox containers for code execution"""
    
    def __init__(self, docker_image: str = "python:3.11-slim"):
        """
        Initialize Sandbox Manager
        
        Args:
            docker_image: Docker image to use for sandbox
        """
        self.docker_image = docker_image
        self.temp_dir = tempfile.gettempdir()
        self.active_containers = []
        
        # Check if Docker is available
        self.docker_available = self._check_docker()
    
    def _check_docker(self) -> bool:
        """Check if Docker is installed and running"""
        try:
            result = subprocess.run(
                ['docker', 'version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def execute_code(
        self,
        code: str,
        timeout: int = 30,
        memory_limit: str = "512m",
        enable_network: bool = False
    ) -> Dict:
        """
        Execute Python code in Docker sandbox
        
        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds
            memory_limit: Memory limit (e.g., "512m", "1g")
            enable_network: Whether to allow network access
        
        Returns:
            {
                'status': 'success'|'error'|'timeout',
                'output': str,
                'error': str,
                'execution_time': float,
                'memory_used': int
            }
        """
        if not self.docker_available:
            return {
                'status': 'error',
                'output': '',
                'error': 'Docker is not available',
                'execution_time': 0,
                'memory_used': 0
            }
        
        # Create temporary file for code
        code_file = os.path.join(self.temp_dir, f'sandbox_{uuid.uuid4().hex}.py')
        
        try:
            # Write code to file
            with open(code_file, 'w') as f:
                f.write(code)
            
            # Build Docker run command
            docker_cmd = [
                'docker', 'run',
                '--rm',  # Remove container after execution
                '--memory', memory_limit,
                '--cpus', '1.0',  # Limit to 1 CPU
                '--pids-limit', '100',  # Limit number of processes
            ]
            
            # Disable network if requested
            if not enable_network:
                docker_cmd.extend(['--network', 'none'])
            
            # Mount code file
            docker_cmd.extend([
                '-v', f'{code_file}:/code.py:ro',  # Read-only mount
                self.docker_image,
                'python', '/code.py'
            ])
            
            # Execute with timeout
            start_time = time.time()
            
            try:
                result = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                execution_time = time.time() - start_time
                
                if result.returncode == 0:
                    return {
                        'status': 'success',
                        'output': result.stdout,
                        'error': result.stderr,
                        'execution_time': execution_time,
                        'memory_used': self._get_memory_usage(result.stderr)
                    }
                else:
                    return {
                        'status': 'error',
                        'output': result.stdout,
                        'error': result.stderr,
                        'execution_time': execution_time,
                        'memory_used': 0
                    }
            
            except subprocess.TimeoutExpired:
                return {
                    'status': 'timeout',
                    'output': '',
                    'error': f'Execution exceeded {timeout} seconds',
                    'execution_time': timeout,
                    'memory_used': 0
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'output': '',
                'error': str(e),
                'execution_time': 0,
                'memory_used': 0
            }
        
        finally:
            # Clean up temporary file
            if os.path.exists(code_file):
                os.remove(code_file)
    
    def execute_with_input(
        self,
        code: str,
        stdin_input: str,
        timeout: int = 30
    ) -> Dict:
        """
        Execute code with stdin input
        
        Args:
            code: Python code to execute
            stdin_input: Input to pass to stdin
            timeout: Maximum execution time
        
        Returns:
            Execution results
        """
        if not self.docker_available:
            return {
                'status': 'error',
                'output': '',
                'error': 'Docker is not available'
            }
        
        code_file = os.path.join(self.temp_dir, f'sandbox_{uuid.uuid4().hex}.py')
        
        try:
            with open(code_file, 'w') as f:
                f.write(code)
            
            docker_cmd = [
                'docker', 'run', '--rm',
                '--memory', '512m',
                '--network', 'none',
                '-i',  # Interactive mode for stdin
                '-v', f'{code_file}:/code.py:ro',
                self.docker_image,
                'python', '/code.py'
            ]
            
            start_time = time.time()
            
            result = subprocess.run(
                docker_cmd,
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'output': result.stdout,
                'error': result.stderr,
                'execution_time': execution_time
            }
        
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'output': '',
                'error': f'Execution exceeded {timeout} seconds',
                'execution_time': timeout
            }
        
        finally:
            if os.path.exists(code_file):
                os.remove(code_file)
    
    def create_persistent_container(
        self,
        name: Optional[str] = None,
        memory_limit: str = "512m"
    ) -> Dict:
        """
        Create a persistent container for multiple executions
        
        Args:
            name: Container name (auto-generated if None)
            memory_limit: Memory limit
        
        Returns:
            Container info
        """
        if not self.docker_available:
            return {
                'status': 'error',
                'error': 'Docker is not available'
            }
        
        if name is None:
            name = f'sandbox_{uuid.uuid4().hex[:8]}'
        
        try:
            # Create container
            result = subprocess.run(
                [
                    'docker', 'create',
                    '--name', name,
                    '--memory', memory_limit,
                    '--network', 'none',
                    '-i',
                    self.docker_image,
                    '/bin/sh'
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                container_id = result.stdout.strip()
                self.active_containers.append(container_id)
                
                return {
                    'status': 'success',
                    'container_id': container_id,
                    'container_name': name
                }
            else:
                return {
                    'status': 'error',
                    'error': result.stderr
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def cleanup_container(self, container_id: str) -> bool:
        """
        Remove a container
        
        Args:
            container_id: Container ID or name
        
        Returns:
            Success status
        """
        try:
            subprocess.run(
                ['docker', 'rm', '-f', container_id],
                capture_output=True,
                timeout=10
            )
            
            if container_id in self.active_containers:
                self.active_containers.remove(container_id)
            
            return True
        
        except Exception:
            return False
    
    def cleanup_all(self):
        """Clean up all active containers"""
        for container_id in self.active_containers[:]:
            self.cleanup_container(container_id)
    
    def get_container_stats(self, container_id: str) -> Dict:
        """
        Get container resource usage stats
        
        Args:
            container_id: Container ID
        
        Returns:
            Stats dictionary
        """
        try:
            result = subprocess.run(
                ['docker', 'stats', container_id, '--no-stream', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            
            return {}
        
        except Exception:
            return {}
    
    def _get_memory_usage(self, stderr: str) -> int:
        """Extract memory usage from stderr if available"""
        # This is a placeholder - actual implementation would parse Docker stats
        return 0
    
    def install_packages(self, packages: List[str]) -> Dict:
        """
        Create a container with additional Python packages
        
        Args:
            packages: List of pip packages to install
        
        Returns:
            Container info
        """
        if not self.docker_available:
            return {
                'status': 'error',
                'error': 'Docker is not available'
            }
        
        # Create temporary Dockerfile
        dockerfile_content = f"""
FROM {self.docker_image}
RUN pip install --no-cache-dir {' '.join(packages)}
"""
        
        dockerfile_path = os.path.join(self.temp_dir, f'Dockerfile.{uuid.uuid4().hex}')
        image_name = f'sandbox_custom_{uuid.uuid4().hex[:8]}'
        
        try:
            # Write Dockerfile
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            # Build image
            result = subprocess.run(
                ['docker', 'build', '-t', image_name, '-f', dockerfile_path, self.temp_dir],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes for build
            )
            
            if result.returncode == 0:
                return {
                    'status': 'success',
                    'image_name': image_name,
                    'packages': packages
                }
            else:
                return {
                    'status': 'error',
                    'error': result.stderr
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
        
        finally:
            if os.path.exists(dockerfile_path):
                os.remove(dockerfile_path)


class MockSandboxManager:
    """
    Mock sandbox manager for when Docker is not available.
    Uses subprocess with limited safety (NOT RECOMMENDED FOR PRODUCTION).
    """
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def execute_code(
        self,
        code: str,
        timeout: int = 30,
        memory_limit: str = "512m",
        enable_network: bool = False
    ) -> Dict:
        """Execute code using subprocess (UNSAFE - for testing only)"""
        
        code_file = os.path.join(self.temp_dir, f'mock_sandbox_{uuid.uuid4().hex}.py')
        
        try:
            with open(code_file, 'w') as f:
                f.write(code)
            
            start_time = time.time()
            
            result = subprocess.run(
                ['python', code_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'output': result.stdout,
                'error': result.stderr,
                'execution_time': execution_time,
                'memory_used': 0,
                'warning': 'Using mock sandbox without Docker isolation'
            }
        
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'output': '',
                'error': f'Execution exceeded {timeout} seconds',
                'execution_time': timeout,
                'memory_used': 0
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'output': '',
                'error': str(e),
                'execution_time': 0,
                'memory_used': 0
            }
        
        finally:
            if os.path.exists(code_file):
                os.remove(code_file)


# Convenience function

def get_sandbox_manager(use_docker: bool = True) -> object:
    """
    Get appropriate sandbox manager
    
    Args:
        use_docker: Try to use Docker if available
    
    Returns:
        SandboxManager or MockSandboxManager
    """
    if use_docker:
        manager = SandboxManager()
        if manager.docker_available:
            return manager
    
    print("Warning: Docker not available, using mock sandbox (unsafe)")
    return MockSandboxManager()
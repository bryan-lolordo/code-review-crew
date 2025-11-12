"""
Security Reviewer Agent

Specialized agent for identifying security vulnerabilities and risks.
Uses Bandit and security best practices to scan code.
"""

import autogen
from typing import Dict, List, Optional
from .base_agent import BaseAgent


class SecurityReviewer(BaseAgent):
    """
    Security Reviewer agent specializing in:
    - SQL injection vulnerabilities
    - XSS (Cross-Site Scripting)
    - Authentication/authorization flaws
    - Input validation issues
    - Sensitive data exposure
    - OWASP Top 10 vulnerabilities
    """
    
    def __init__(self, llm_config: Dict, tools: Dict):
        """
        Initialize Security Reviewer agent
        
        Args:
            llm_config: LLM configuration dictionary
            tools: Dictionary of tool instances (security_scanner, etc.)
        """
        self.tools = tools
        self.llm_config = llm_config
        
        system_message = """
        You are a Security Reviewer specializing in application security.
        
        Your responsibilities:
        1. Identify SQL injection vulnerabilities
        2. Detect XSS (Cross-Site Scripting) risks
        3. Review authentication and authorization mechanisms
        4. Check input validation and sanitization
        5. Identify sensitive data exposure
        6. Scan for OWASP Top 10 vulnerabilities
        7. Review cryptography usage
        8. Check for hardcoded credentials
        
        Use the available tools:
        - scan_security: Run Bandit security scanner
        - check_owasp: Check for OWASP Top 10 vulnerabilities
        - detect_injection: Detect injection vulnerabilities
        
        For each security issue found:
        - Explain the vulnerability clearly
        - Describe the potential exploit
        - Assess the security impact (Critical/High/Medium/Low)
        - Provide secure code alternatives
        - Reference relevant security standards (OWASP, CWE)
        
        Always prioritize security issues as Critical or High severity.
        Provide concrete examples of how the vulnerability could be exploited.
        """
        
        self.agent = autogen.AssistantAgent(
            name="SecurityReviewer",
            system_message=system_message,
            llm_config=llm_config
        )
    
    def create_agent(self) -> autogen.AssistantAgent:
        """Return the AutoGen agent"""
        return self.agent
    
    def register_functions(self):
        """Register tool functions with the agent"""
        function_map = {
            "scan_security": self.tools['security'].run_bandit,
            "check_owasp": self.tools['security'].check_owasp_top10,
            "detect_injection": self.detect_injection_vulns,
        }
        return function_map
    
    def detect_injection_vulns(self, code: str) -> Dict:
        """
        Detect various injection vulnerabilities
        
        Args:
            code: Python source code to analyze
        
        Returns:
            Dictionary of detected injection vulnerabilities
        """
        injections = {
            'sql_injection': self._check_sql_injection(code),
            'command_injection': self._check_command_injection(code),
            'code_injection': self._check_code_injection(code),
            'xpath_injection': self._check_xpath_injection(code)
        }
        
        return {
            'total_injections': sum(len(v) for v in injections.values()),
            'injections': injections
        }
    
    def _check_sql_injection(self, code: str) -> List[Dict]:
        """Check for SQL injection vulnerabilities"""
        vulnerabilities = []
        
        # Common SQL injection patterns
        patterns = [
            'f"SELECT',
            'f\'SELECT',
            '" + ',
            '\' + ',
            'execute(query',
            '.format('
        ]
        
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                if pattern in line and 'SELECT' in line.upper():
                    vulnerabilities.append({
                        'line': line_num,
                        'pattern': pattern,
                        'code': line.strip(),
                        'severity': 'Critical',
                        'description': 'Possible SQL injection vulnerability'
                    })
        
        return vulnerabilities
    
    def _check_command_injection(self, code: str) -> List[Dict]:
        """Check for command injection vulnerabilities"""
        vulnerabilities = []
        
        dangerous_functions = [
            'os.system(',
            'subprocess.call(',
            'subprocess.run(',
            'eval(',
            'exec('
        ]
        
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            for func in dangerous_functions:
                if func in line:
                    vulnerabilities.append({
                        'line': line_num,
                        'function': func,
                        'code': line.strip(),
                        'severity': 'High',
                        'description': 'Potential command/code injection'
                    })
        
        return vulnerabilities
    
    def _check_code_injection(self, code: str) -> List[Dict]:
        """Check for code injection via eval/exec"""
        # Implemented in _check_command_injection
        return []
    
    def _check_xpath_injection(self, code: str) -> List[Dict]:
        """Check for XPath injection vulnerabilities"""
        # TODO: Implement XPath injection detection
        return []
    
    def check_crypto_usage(self, code: str) -> Dict:
        """
        Check for weak or insecure cryptography usage
        
        Args:
            code: Python source code to analyze
        
        Returns:
            Dictionary of cryptography issues
        """
        issues = {
            'weak_hash': self._check_weak_hashing(code),
            'weak_random': self._check_weak_random(code),
            'hardcoded_secrets': self._check_hardcoded_secrets(code)
        }
        
        return issues
    
    def _check_weak_hashing(self, code: str) -> List[Dict]:
        """Check for weak hashing algorithms"""
        weak_algorithms = ['md5', 'sha1']
        issues = []
        
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            for algo in weak_algorithms:
                if algo in line.lower():
                    issues.append({
                        'line': line_num,
                        'algorithm': algo,
                        'severity': 'High',
                        'description': f'{algo.upper()} is cryptographically broken'
                    })
        
        return issues
    
    def _check_weak_random(self, code: str) -> List[Dict]:
        """Check for weak random number generation"""
        if 'import random' in code and ('token' in code.lower() or 'password' in code.lower()):
            return [{
                'severity': 'High',
                'description': 'Using random module for security-sensitive operations',
                'recommendation': 'Use secrets module instead'
            }]
        return []
    
    def _check_hardcoded_secrets(self, code: str) -> List[Dict]:
        """Check for hardcoded passwords, API keys, etc."""
        # TODO: Implement hardcoded secrets detection
        return []
    
    def analyze(self, code: str) -> Dict:
        """
        High-level security analysis function
        
        Args:
            code: Python source code to analyze
        
        Returns:
            Comprehensive security analysis results
        """
        results = {
            'bandit_results': self.tools['security'].run_bandit(code),
            'owasp_check': self.tools['security'].check_owasp_top10(code),
            'injection_vulns': self.detect_injection_vulns(code),
            'crypto_issues': self.check_crypto_usage(code)
        }
        
        return results
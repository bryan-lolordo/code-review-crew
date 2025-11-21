"""
Security Reviewer Agent

Specialized agent for identifying security vulnerabilities and best practices.
"""

import autogen
import re
from typing import Dict, List
from .base_agent import BaseAgent


class SecurityReviewer(BaseAgent):
    """
    Security Reviewer agent specializing in:
    - SQL injection vulnerabilities
    - XSS (Cross-Site Scripting)
    - Authentication/authorization flaws
    - Input validation
    - Cryptography issues
    - OWASP Top 10
    """
    
    def __init__(self, llm_config: Dict, tools: Dict):
        """
        Initialize Security Reviewer agent
        
        Args:
            llm_config: LLM configuration dictionary
            tools: Dictionary of tool instances
        """
        self.tools = tools
        self.llm_config = llm_config
        
        system_message = """
        You are a Security Reviewer specializing in identifying security vulnerabilities.
        
        Your responsibilities:
        1. Identify SQL injection vulnerabilities
        2. Detect XSS (Cross-Site Scripting) risks
        3. Check authentication and authorization
        4. Review input validation
        5. Identify weak cryptography
        6. Check for hardcoded secrets
        7. Review OWASP Top 10 vulnerabilities
        
        Use available tools:
        - scan_security: Run Bandit security scanner
        - detect_sql_injection: Check for SQL injection patterns
        - detect_secrets: Find hardcoded secrets
        
        Mark ALL security issues as CRITICAL.
        Explain the exploit and provide secure alternatives.
        
        When reporting issues:
        - Severity: CRITICAL
        - Line number
        - Vulnerability type
        - Exploit example
        - Secure fix
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
            "detect_sql_injection": self.detect_sql_injection,
            "detect_secrets": self.detect_hardcoded_secrets,
            "detect_weak_crypto": self.detect_weak_crypto,
        }
        return function_map
    
    def detect_sql_injection(self, code: str) -> List[Dict]:
        """
        Detect potential SQL injection vulnerabilities
        
        Args:
            code: Python source code to analyze
        
        Returns:
            List of potential SQL injection issues
        """
        issues = []
        lines = code.split('\n')
        
        # Patterns that suggest SQL injection risk
        dangerous_patterns = [
            (r'f["\'].*SELECT.*\{.*\}.*["\']', 'f-string in SQL query'),
            (r'["\'].*SELECT.*["\'].*\+.*', 'String concatenation in SQL'),
            (r'["\'].*SELECT.*%.*["\'].*%', '% formatting in SQL'),
            (r'\.format\(.*\).*SELECT', '.format() in SQL query'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, description in dangerous_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'line': i,
                        'type': 'SQL Injection',
                        'severity': 'CRITICAL',
                        'description': f'{description} - Use parameterized queries',
                        'code': line.strip()
                    })
        
        return issues
    
    def detect_hardcoded_secrets(self, code: str) -> List[Dict]:
        """
        Detect hardcoded secrets like API keys, passwords
        
        Args:
            code: Python source code to analyze
        
        Returns:
            List of potential hardcoded secrets
        """
        issues = []
        lines = code.split('\n')
        
        # Patterns for common secrets
        secret_patterns = [
            (r'(api[_-]?key|apikey)\s*=\s*["\'][^"\']+["\']', 'API Key'),
            (r'(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', 'Password'),
            (r'(secret|token)\s*=\s*["\'][^"\']+["\']', 'Secret/Token'),
            (r'(sk-[a-zA-Z0-9]{32,})', 'API Key (OpenAI style)'),
        ]
        
        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('#'):
                continue
                
            for pattern, secret_type in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'line': i,
                        'type': 'Hardcoded Secret',
                        'severity': 'CRITICAL',
                        'description': f'{secret_type} hardcoded - Use environment variables',
                        'code': line.strip()
                    })
        
        return issues
    
    def detect_weak_crypto(self, code: str) -> List[Dict]:
        """
        Detect weak cryptographic functions
        
        Args:
            code: Python source code to analyze
        
        Returns:
            List of weak crypto usage
        """
        issues = []
        lines = code.split('\n')
        
        # Weak crypto patterns
        weak_patterns = [
            (r'hashlib\.md5', 'MD5 is cryptographically broken - Use SHA256 or bcrypt'),
            (r'hashlib\.sha1', 'SHA1 is weak - Use SHA256 or better'),
            (r'\.encode\(\)\.hex\(\)', 'Simple encoding is not encryption'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, description in weak_patterns:
                if re.search(pattern, line):
                    issues.append({
                        'line': i,
                        'type': 'Weak Cryptography',
                        'severity': 'HIGH',
                        'description': description,
                        'code': line.strip()
                    })
        
        return issues
    
    def analyze(self, code: str) -> Dict:
        """
        Comprehensive security analysis
        
        Args:
            code: Python source code to analyze
        
        Returns:
            Security analysis results
        """
        results = {
            'sql_injection': self.detect_sql_injection(code),
            'hardcoded_secrets': self.detect_hardcoded_secrets(code),
            'weak_crypto': self.detect_weak_crypto(code),
            'total_issues': 0
        }
        
        results['total_issues'] = (
            len(results['sql_injection']) +
            len(results['hardcoded_secrets']) +
            len(results['weak_crypto'])
        )
        
        return results
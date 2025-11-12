"""
Security Scanner Tool

Wrapper for Bandit security analysis tool.
Identifies security vulnerabilities and risks in Python code.
"""

import subprocess
import json
import tempfile
import os
from typing import Dict, List


class SecurityScanner:
    """Wrapper for Bandit security scanner"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def run_bandit(self, code: str) -> Dict:
        """
        Scan code for security vulnerabilities using Bandit
        
        Args:
            code: Python source code to scan
        
        Returns:
            {
                'high_severity': [...],
                'medium_severity': [...],
                'low_severity': [...],
                'total_issues': int,
                'confidence_scores': {...},
                'summary': str
            }
        """
        # Write code to temporary file
        temp_file = os.path.join(self.temp_dir, 'temp_code.py')
        with open(temp_file, 'w') as f:
            f.write(code)
        
        try:
            # Run Bandit with JSON output
            result = subprocess.run(
                ['bandit', '-f', 'json', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse JSON output
            report = {}
            if result.stdout:
                try:
                    report = json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass
            
            # Categorize issues by severity
            categorized = self._categorize_issues(report.get('results', []))
            
            # Generate summary
            summary = self._generate_security_summary(categorized)
            
            return {
                'high_severity': categorized['high'],
                'medium_severity': categorized['medium'],
                'low_severity': categorized['low'],
                'total_issues': len(report.get('results', [])),
                'summary': summary,
                'metrics': report.get('metrics', {})
            }
        
        except subprocess.TimeoutExpired:
            return {
                'high_severity': [],
                'medium_severity': [],
                'low_severity': [],
                'total_issues': 0,
                'summary': 'Security scan timed out',
                'error': 'Timeout'
            }
        except FileNotFoundError:
            return {
                'high_severity': [],
                'medium_severity': [],
                'low_severity': [],
                'total_issues': 0,
                'summary': 'Bandit not installed',
                'error': 'Bandit not found'
            }
        except Exception as e:
            return {
                'high_severity': [],
                'medium_severity': [],
                'low_severity': [],
                'total_issues': 0,
                'summary': f'Security scan error: {str(e)}',
                'error': str(e)
            }
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def _categorize_issues(self, issues: List[Dict]) -> Dict:
        """Categorize issues by severity"""
        categorized = {
            'high': [],
            'medium': [],
            'low': []
        }
        
        for issue in issues:
            severity = issue.get('issue_severity', 'MEDIUM').lower()
            
            formatted_issue = {
                'test_id': issue.get('test_id', ''),
                'test_name': issue.get('test_name', ''),
                'line_number': issue.get('line_number', 0),
                'line_range': issue.get('line_range', []),
                'code': issue.get('code', ''),
                'issue_text': issue.get('issue_text', ''),
                'issue_severity': severity.upper(),
                'issue_confidence': issue.get('issue_confidence', 'MEDIUM'),
                'more_info': issue.get('more_info', '')
            }
            
            if severity == 'high':
                categorized['high'].append(formatted_issue)
            elif severity == 'medium':
                categorized['medium'].append(formatted_issue)
            else:
                categorized['low'].append(formatted_issue)
        
        return categorized
    
    def _generate_security_summary(self, categorized: Dict) -> str:
        """Generate human-readable security summary"""
        high_count = len(categorized['high'])
        medium_count = len(categorized['medium'])
        low_count = len(categorized['low'])
        
        if high_count == 0 and medium_count == 0 and low_count == 0:
            return "No security issues detected."
        
        summary = "Security scan complete. "
        
        if high_count > 0:
            summary += f"Found {high_count} HIGH severity issues (immediate action required). "
        
        if medium_count > 0:
            summary += f"{medium_count} MEDIUM severity issues detected. "
        
        if low_count > 0:
            summary += f"{low_count} LOW severity issues found."
        
        return summary
    
    def check_owasp_top10(self, code: str) -> List[str]:
        """
        Check for OWASP Top 10 vulnerabilities
        
        Args:
            code: Python source code to check
        
        Returns:
            List of OWASP categories with vulnerabilities found
        """
        vulnerabilities = []
        
        # A01:2021 - Broken Access Control
        if self._check_broken_access_control(code):
            vulnerabilities.append('A01:2021 - Broken Access Control')
        
        # A02:2021 - Cryptographic Failures
        if self._check_crypto_failures(code):
            vulnerabilities.append('A02:2021 - Cryptographic Failures')
        
        # A03:2021 - Injection
        if self._check_injection(code):
            vulnerabilities.append('A03:2021 - Injection')
        
        # A04:2021 - Insecure Design
        # (More conceptual, harder to detect automatically)
        
        # A05:2021 - Security Misconfiguration
        if self._check_security_misconfiguration(code):
            vulnerabilities.append('A05:2021 - Security Misconfiguration')
        
        # A06:2021 - Vulnerable and Outdated Components
        # (Would require dependency checking)
        
        # A07:2021 - Identification and Authentication Failures
        if self._check_auth_failures(code):
            vulnerabilities.append('A07:2021 - Identification and Authentication Failures')
        
        # A08:2021 - Software and Data Integrity Failures
        if self._check_integrity_failures(code):
            vulnerabilities.append('A08:2021 - Software and Data Integrity Failures')
        
        # A09:2021 - Security Logging and Monitoring Failures
        # (Harder to detect automatically)
        
        # A10:2021 - Server-Side Request Forgery (SSRF)
        if self._check_ssrf(code):
            vulnerabilities.append('A10:2021 - Server-Side Request Forgery')
        
        return vulnerabilities
    
    def _check_broken_access_control(self, code: str) -> bool:
        """Check for broken access control issues"""
        # Simple checks for missing authorization
        indicators = [
            'admin' in code.lower() and 'check' not in code.lower(),
            '@login_required' not in code and 'admin' in code.lower()
        ]
        return any(indicators)
    
    def _check_crypto_failures(self, code: str) -> bool:
        """Check for cryptographic failures"""
        weak_crypto = ['md5', 'sha1', 'des', 'rc4']
        return any(algo in code.lower() for algo in weak_crypto)
    
    def _check_injection(self, code: str) -> bool:
        """Check for injection vulnerabilities"""
        # SQL injection
        sql_patterns = [
            'f"SELECT' in code,
            'f\'SELECT' in code,
            '" + ' in code and 'SELECT' in code.upper(),
            '\' + ' in code and 'SELECT' in code.upper()
        ]
        
        # Command injection
        cmd_patterns = [
            'os.system(' in code,
            'subprocess.call(' in code and 'shell=True' in code,
            'eval(' in code,
            'exec(' in code
        ]
        
        return any(sql_patterns + cmd_patterns)
    
    def _check_security_misconfiguration(self, code: str) -> bool:
        """Check for security misconfiguration"""
        indicators = [
            'DEBUG = True' in code or 'debug=True' in code,
            'SECRET_KEY = ' in code and '=' in code,  # Hardcoded secret
            'verify=False' in code  # Disabling SSL verification
        ]
        return any(indicators)
    
    def _check_auth_failures(self, code: str) -> bool:
        """Check for authentication failures"""
        weak_auth = [
            'password == ' in code and '"' in code,  # Hardcoded password
            'import random' in code and 'token' in code.lower(),  # Weak random
            'session_id' in code.lower() and 'secure' not in code.lower()
        ]
        return any(weak_auth)
    
    def _check_integrity_failures(self, code: str) -> bool:
        """Check for integrity failures"""
        indicators = [
            'pickle.load' in code,  # Insecure deserialization
            'yaml.load(' in code and 'Loader=' not in code
        ]
        return any(indicators)
    
    def _check_ssrf(self, code: str) -> bool:
        """Check for SSRF vulnerabilities"""
        indicators = [
            'requests.get(' in code and 'user' in code.lower(),
            'urllib.request.urlopen(' in code and 'input(' in code
        ]
        return any(indicators)
    
    def scan_for_secrets(self, code: str) -> List[Dict]:
        """
        Scan for hardcoded secrets (API keys, passwords, tokens)
        
        Args:
            code: Python source code
        
        Returns:
            List of potential secrets found
        """
        secrets = []
        lines = code.split('\n')
        
        # Patterns for common secrets
        secret_patterns = {
            'api_key': r'api[_-]?key',
            'password': r'password',
            'secret': r'secret',
            'token': r'token',
            'aws_access': r'aws[_-]?access',
            'private_key': r'private[_-]?key'
        }
        
        for line_num, line in enumerate(lines, 1):
            lower_line = line.lower()
            
            # Check for assignment with quotes
            if '=' in line and ('"' in line or "'" in line):
                for secret_type, pattern in secret_patterns.items():
                    if pattern in lower_line:
                        secrets.append({
                            'line': line_num,
                            'type': secret_type,
                            'severity': 'high',
                            'message': f'Possible hardcoded {secret_type} detected',
                            'code': line.strip()
                        })
        
        return secrets
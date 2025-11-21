"""
Security Scanner Tool

Wrapper for Bandit security scanner to identify security vulnerabilities in Python code.
"""

import subprocess
import json
import tempfile
import os
from typing import Dict, List


class SecurityScanner:
    """
    Security scanner tool using Bandit
    
    Detects:
    - SQL injection
    - Hardcoded passwords
    - Weak cryptography
    - Shell injection
    - Assert usage
    - Insecure functions
    """
    
    def __init__(self):
        """Initialize the security scanner"""
        self.bandit_available = self._check_bandit_available()
    
    def _check_bandit_available(self) -> bool:
        """Check if Bandit is installed"""
        try:
            result = subprocess.run(
                ["bandit", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def run_bandit(self, code: str) -> Dict:
        """
        Run Bandit security scanner on code
        
        Args:
            code: Python source code to scan
        
        Returns:
            Dictionary containing security scan results
        """
        if not self.bandit_available:
            return {
                'available': False,
                'message': 'Bandit not installed. Install with: pip install bandit',
                'issues': [],
                'severity_counts': {}
            }
        
        # Write code to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Run Bandit with JSON output
            result = subprocess.run(
                ['bandit', '-f', 'json', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse JSON output
            if result.stdout:
                output = json.loads(result.stdout)
                issues = self._parse_bandit_output(output)
                
                return {
                    'available': True,
                    'total_issues': len(issues),
                    'issues': issues,
                    'severity_counts': self._count_severity(issues),
                    'raw_output': output
                }
            else:
                return {
                    'available': True,
                    'total_issues': 0,
                    'issues': [],
                    'severity_counts': {},
                    'message': 'No issues found'
                }
        
        except subprocess.TimeoutExpired:
            return {
                'available': True,
                'error': 'Bandit scan timed out',
                'issues': [],
                'severity_counts': {}
            }
        
        except json.JSONDecodeError as e:
            return {
                'available': True,
                'error': f'Failed to parse Bandit output: {e}',
                'issues': [],
                'severity_counts': {}
            }
        
        except Exception as e:
            return {
                'available': True,
                'error': str(e),
                'issues': [],
                'severity_counts': {}
            }
        
        finally:
            # Cleanup temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def _parse_bandit_output(self, output: Dict) -> List[Dict]:
        """
        Parse Bandit JSON output into structured issues
        
        Args:
            output: Bandit JSON output
        
        Returns:
            List of security issues
        """
        issues = []
        
        for result in output.get('results', []):
            issues.append({
                'line': result.get('line_number'),
                'severity': result.get('issue_severity'),
                'confidence': result.get('issue_confidence'),
                'type': result.get('test_name'),
                'description': result.get('issue_text'),
                'code': result.get('code', '').strip(),
                'cwe': result.get('issue_cwe', {}).get('id') if result.get('issue_cwe') else None
            })
        
        return issues
    
    def _count_severity(self, issues: List[Dict]) -> Dict:
        """
        Count issues by severity level
        
        Args:
            issues: List of security issues
        
        Returns:
            Dictionary with severity counts
        """
        counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for issue in issues:
            severity = issue.get('severity', 'MEDIUM')
            if severity in counts:
                counts[severity] += 1
        
        return counts
    
    def check_owasp_top10(self, code: str) -> Dict:
        """
        Check for OWASP Top 10 vulnerabilities
        
        Args:
            code: Python source code to check
        
        Returns:
            Dictionary of OWASP Top 10 findings
        """
        # Run Bandit and map to OWASP categories
        bandit_results = self.run_bandit(code)
        
        owasp_categories = {
            'A01:2021 - Broken Access Control': [],
            'A02:2021 - Cryptographic Failures': [],
            'A03:2021 - Injection': [],
            'A04:2021 - Insecure Design': [],
            'A05:2021 - Security Misconfiguration': [],
            'A06:2021 - Vulnerable Components': [],
            'A07:2021 - Authentication Failures': [],
            'A08:2021 - Software and Data Integrity': [],
            'A09:2021 - Security Logging Failures': [],
            'A10:2021 - Server-Side Request Forgery': []
        }
        
        # Map Bandit findings to OWASP categories
        for issue in bandit_results.get('issues', []):
            issue_type = issue.get('type', '').lower()
            
            # Injection
            if any(keyword in issue_type for keyword in ['sql', 'injection', 'exec', 'eval']):
                owasp_categories['A03:2021 - Injection'].append(issue)
            
            # Cryptographic Failures
            elif any(keyword in issue_type for keyword in ['weak', 'crypto', 'hash', 'md5', 'sha1']):
                owasp_categories['A02:2021 - Cryptographic Failures'].append(issue)
            
            # Security Misconfiguration
            elif any(keyword in issue_type for keyword in ['assert', 'debug', 'hardcoded']):
                owasp_categories['A05:2021 - Security Misconfiguration'].append(issue)
            
            # Default to Insecure Design
            else:
                owasp_categories['A04:2021 - Insecure Design'].append(issue)
        
        # Remove empty categories
        owasp_results = {k: v for k, v in owasp_categories.items() if v}
        
        return {
            'total_categories_affected': len(owasp_results),
            'categories': owasp_results,
            'summary': self._generate_owasp_summary(owasp_results)
        }
    
    def _generate_owasp_summary(self, owasp_results: Dict) -> str:
        """
        Generate a summary of OWASP findings
        
        Args:
            owasp_results: OWASP categorized results
        
        Returns:
            Summary string
        """
        if not owasp_results:
            return "No OWASP Top 10 vulnerabilities detected"
        
        summary_lines = []
        for category, issues in owasp_results.items():
            summary_lines.append(f"{category}: {len(issues)} issue(s)")
        
        return "\n".join(summary_lines)
    
    def scan_for_secrets(self, code: str) -> List[Dict]:
        """
        Scan for hardcoded secrets (passwords, API keys, tokens)
        
        Args:
            code: Python source code to scan
        
        Returns:
            List of potential secrets found
        """
        import re
        
        secrets = []
        lines = code.split('\n')
        
        # Patterns for common secrets
        patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'Password'),
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', 'API Key'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Secret'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'Token'),
            (r'(aws|amazon)[_-]?secret', 'AWS Secret'),
            (r'private[_-]?key', 'Private Key'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, secret_type in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    secrets.append({
                        'line': i,
                        'type': secret_type,
                        'severity': 'HIGH',
                        'description': f'Hardcoded {secret_type} detected',
                        'code': line.strip()
                    })
        
        return secrets
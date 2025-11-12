"""
Linting Tool

Wrapper for Pylint and PEP 8 style checkers.
Provides structured analysis results for code quality.
"""

import subprocess
import json
import tempfile
import os
from typing import Dict, List


class LintingTool:
    """Wrapper for Python linting tools (Pylint, pycodestyle)"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def run_pylint(self, code: str) -> Dict:
        """
        Run Pylint on code and return structured results
        
        Args:
            code: Python source code to analyze
        
        Returns:
            {
                'score': float (0-10),
                'issues': [
                    {
                        'type': 'convention|refactor|warning|error',
                        'line': int,
                        'column': int,
                        'message': str,
                        'symbol': str,
                        'message_id': str
                    }
                ],
                'summary': str,
                'statistics': dict
            }
        """
        # Write code to temporary file
        temp_file = os.path.join(self.temp_dir, 'temp_code.py')
        with open(temp_file, 'w') as f:
            f.write(code)
        
        try:
            # Run pylint with JSON output
            result = subprocess.run(
                ['pylint', temp_file, '--output-format=json', '--score=yes'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse JSON output
            issues = []
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass
            
            # Calculate score from stderr (pylint prints score there)
            score = self._extract_score(result.stderr)
            
            # Format issues
            formatted_issues = self._format_pylint_issues(issues)
            
            # Generate summary
            summary = self._generate_summary(score, formatted_issues)
            
            # Get statistics
            statistics = self._calculate_statistics(formatted_issues)
            
            return {
                'score': score,
                'issues': formatted_issues,
                'summary': summary,
                'statistics': statistics,
                'raw_output': result.stderr
            }
        
        except subprocess.TimeoutExpired:
            return {
                'score': 0,
                'issues': [],
                'summary': 'Pylint timeout',
                'error': 'Analysis timed out'
            }
        except Exception as e:
            return {
                'score': 0,
                'issues': [],
                'summary': f'Pylint error: {str(e)}',
                'error': str(e)
            }
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def _extract_score(self, stderr: str) -> float:
        """Extract Pylint score from stderr output"""
        try:
            for line in stderr.split('\n'):
                if 'Your code has been rated at' in line:
                    score_str = line.split('rated at ')[1].split('/')[0]
                    return float(score_str)
        except:
            pass
        return 0.0
    
    def _format_pylint_issues(self, issues: List[Dict]) -> List[Dict]:
        """Format Pylint issues into consistent structure"""
        formatted = []
        
        for issue in issues:
            formatted.append({
                'type': issue.get('type', 'unknown'),
                'line': issue.get('line', 0),
                'column': issue.get('column', 0),
                'message': issue.get('message', ''),
                'symbol': issue.get('symbol', ''),
                'message_id': issue.get('message-id', ''),
                'severity': self._map_severity(issue.get('type', '')),
                'category': issue.get('symbol', '').split('-')[0] if '-' in issue.get('symbol', '') else 'other'
            })
        
        return formatted
    
    def _map_severity(self, issue_type: str) -> str:
        """Map Pylint issue type to severity"""
        mapping = {
            'error': 'high',
            'warning': 'medium',
            'refactor': 'medium',
            'convention': 'low'
        }
        return mapping.get(issue_type, 'low')
    
    def _generate_summary(self, score: float, issues: List[Dict]) -> str:
        """Generate human-readable summary"""
        if score >= 9.0:
            quality = "Excellent"
        elif score >= 8.0:
            quality = "Good"
        elif score >= 7.0:
            quality = "Acceptable"
        elif score >= 5.0:
            quality = "Needs Improvement"
        else:
            quality = "Poor"
        
        error_count = len([i for i in issues if i['type'] == 'error'])
        warning_count = len([i for i in issues if i['type'] == 'warning'])
        
        summary = f"Pylint Score: {score}/10 ({quality}). "
        summary += f"Found {error_count} errors, {warning_count} warnings, "
        summary += f"and {len(issues) - error_count - warning_count} other issues."
        
        return summary
    
    def _calculate_statistics(self, issues: List[Dict]) -> Dict:
        """Calculate statistics from issues"""
        stats = {
            'total_issues': len(issues),
            'by_type': {},
            'by_severity': {},
            'by_category': {}
        }
        
        for issue in issues:
            # Count by type
            issue_type = issue['type']
            stats['by_type'][issue_type] = stats['by_type'].get(issue_type, 0) + 1
            
            # Count by severity
            severity = issue['severity']
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            
            # Count by category
            category = issue['category']
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        return stats
    
    def check_pep8(self, code: str) -> List[Dict]:
        """
        Check PEP 8 compliance using pycodestyle
        
        Args:
            code: Python source code to check
        
        Returns:
            List of PEP 8 violations
        """
        # Write code to temporary file
        temp_file = os.path.join(self.temp_dir, 'temp_code.py')
        with open(temp_file, 'w') as f:
            f.write(code)
        
        try:
            # Run pycodestyle
            result = subprocess.run(
                ['pycodestyle', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse output
            violations = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    violation = self._parse_pep8_line(line)
                    if violation:
                        violations.append(violation)
            
            return violations
        
        except subprocess.TimeoutExpired:
            return []
        except FileNotFoundError:
            # pycodestyle not installed
            return [{
                'line': 0,
                'message': 'pycodestyle not installed',
                'error': True
            }]
        except Exception as e:
            return [{
                'line': 0,
                'message': f'PEP 8 check error: {str(e)}',
                'error': True
            }]
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def _parse_pep8_line(self, line: str) -> Dict:
        """Parse a pycodestyle output line"""
        try:
            # Format: filename:line:column: code message
            parts = line.split(':', 3)
            if len(parts) >= 4:
                return {
                    'line': int(parts[1]),
                    'column': int(parts[2]),
                    'code': parts[3].split()[0],
                    'message': ' '.join(parts[3].split()[1:]),
                    'severity': 'low'
                }
        except:
            pass
        return None
    
    def get_code_metrics(self, code: str) -> Dict:
        """
        Get basic code metrics
        
        Args:
            code: Python source code
        
        Returns:
            Dictionary of code metrics
        """
        lines = code.split('\n')
        
        metrics = {
            'total_lines': len(lines),
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'docstring_lines': 0
        }
        
        in_docstring = False
        for line in lines:
            stripped = line.strip()
            
            # Check for docstrings
            if '"""' in stripped or "'''" in stripped:
                in_docstring = not in_docstring
                metrics['docstring_lines'] += 1
            elif in_docstring:
                metrics['docstring_lines'] += 1
            # Check for comments
            elif stripped.startswith('#'):
                metrics['comment_lines'] += 1
            # Check for blank lines
            elif not stripped:
                metrics['blank_lines'] += 1
            # Otherwise it's a code line
            else:
                metrics['code_lines'] += 1
        
        return metrics
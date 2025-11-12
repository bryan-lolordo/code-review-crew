"""
Git Tool

Utilities for parsing Git diffs and working with version control.
Useful for reviewing code changes in pull requests.
"""

import subprocess
import re
from typing import Dict, List, Optional


class GitTool:
    """Wrapper for Git operations and diff parsing"""
    
    def __init__(self):
        self.diff_pattern = re.compile(r'^@@\s+-(\d+),?(\d*)\s+\+(\d+),?(\d*)\s+@@')
    
    def parse_diff(self, diff_text: str) -> Dict:
        """
        Parse a Git diff into structured format
        
        Args:
            diff_text: Git diff output
        
        Returns:
            {
                'files': [
                    {
                        'file_path': str,
                        'old_path': str,
                        'new_path': str,
                        'chunks': [
                            {
                                'old_start': int,
                                'old_lines': int,
                                'new_start': int,
                                'new_lines': int,
                                'changes': [...]
                            }
                        ]
                    }
                ],
                'stats': {...}
            }
        """
        files = []
        current_file = None
        current_chunk = None
        
        lines = diff_text.split('\n')
        
        for line in lines:
            # New file
            if line.startswith('diff --git'):
                if current_file:
                    files.append(current_file)
                
                # Extract file paths
                match = re.search(r'a/(.+?)\s+b/(.+)', line)
                if match:
                    current_file = {
                        'old_path': match.group(1),
                        'new_path': match.group(2),
                        'file_path': match.group(2),
                        'chunks': []
                    }
            
            # File mode/index/--- +++
            elif line.startswith('---') or line.startswith('+++'):
                continue
            
            # Chunk header
            elif line.startswith('@@'):
                if current_file:
                    match = self.diff_pattern.match(line)
                    if match:
                        old_start = int(match.group(1))
                        old_lines = int(match.group(2)) if match.group(2) else 1
                        new_start = int(match.group(3))
                        new_lines = int(match.group(4)) if match.group(4) else 1
                        
                        current_chunk = {
                            'old_start': old_start,
                            'old_lines': old_lines,
                            'new_start': new_start,
                            'new_lines': new_lines,
                            'header': line,
                            'changes': []
                        }
                        current_file['chunks'].append(current_chunk)
            
            # Added line
            elif line.startswith('+') and current_chunk:
                current_chunk['changes'].append({
                    'type': 'add',
                    'line': line[1:],
                    'line_number': current_chunk['new_start'] + len([c for c in current_chunk['changes'] if c['type'] in ['add', 'context']])
                })
            
            # Removed line
            elif line.startswith('-') and current_chunk:
                current_chunk['changes'].append({
                    'type': 'remove',
                    'line': line[1:],
                    'line_number': current_chunk['old_start'] + len([c for c in current_chunk['changes'] if c['type'] in ['remove', 'context']])
                })
            
            # Context line
            elif line.startswith(' ') and current_chunk:
                current_chunk['changes'].append({
                    'type': 'context',
                    'line': line[1:]
                })
        
        # Add last file
        if current_file:
            files.append(current_file)
        
        # Calculate stats
        stats = self._calculate_diff_stats(files)
        
        return {
            'files': files,
            'stats': stats
        }
    
    def _calculate_diff_stats(self, files: List[Dict]) -> Dict:
        """Calculate statistics from parsed diff"""
        stats = {
            'files_changed': len(files),
            'insertions': 0,
            'deletions': 0,
            'total_changes': 0
        }
        
        for file in files:
            for chunk in file['chunks']:
                for change in chunk['changes']:
                    if change['type'] == 'add':
                        stats['insertions'] += 1
                    elif change['type'] == 'remove':
                        stats['deletions'] += 1
        
        stats['total_changes'] = stats['insertions'] + stats['deletions']
        
        return stats
    
    def get_changed_lines(self, diff_text: str) -> Dict[str, List[int]]:
        """
        Extract line numbers of changed lines per file
        
        Args:
            diff_text: Git diff output
        
        Returns:
            Dictionary mapping file paths to lists of changed line numbers
        """
        parsed = self.parse_diff(diff_text)
        changed_lines = {}
        
        for file in parsed['files']:
            file_path = file['file_path']
            lines = []
            
            for chunk in file['chunks']:
                for change in chunk['changes']:
                    if change['type'] in ['add', 'remove']:
                        lines.append(change.get('line_number', 0))
            
            changed_lines[file_path] = sorted(list(set(lines)))
        
        return changed_lines
    
    def extract_added_code(self, diff_text: str) -> Dict[str, str]:
        """
        Extract only the added code from a diff
        
        Args:
            diff_text: Git diff output
        
        Returns:
            Dictionary mapping file paths to added code
        """
        parsed = self.parse_diff(diff_text)
        added_code = {}
        
        for file in parsed['files']:
            file_path = file['file_path']
            lines = []
            
            for chunk in file['chunks']:
                for change in chunk['changes']:
                    if change['type'] == 'add':
                        lines.append(change['line'])
            
            if lines:
                added_code[file_path] = '\n'.join(lines)
        
        return added_code
    
    def get_commit_diff(self, commit_hash: str, repo_path: str = '.') -> str:
        """
        Get the diff for a specific commit
        
        Args:
            commit_hash: Git commit hash
            repo_path: Path to Git repository
        
        Returns:
            Diff text
        """
        try:
            result = subprocess.run(
                ['git', 'show', commit_hash],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error: {result.stderr}"
        
        except subprocess.TimeoutExpired:
            return "Error: Git command timed out"
        except FileNotFoundError:
            return "Error: Git not found"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_branch_diff(self, base_branch: str, compare_branch: str, repo_path: str = '.') -> str:
        """
        Get diff between two branches
        
        Args:
            base_branch: Base branch name
            compare_branch: Branch to compare
            repo_path: Path to Git repository
        
        Returns:
            Diff text
        """
        try:
            result = subprocess.run(
                ['git', 'diff', base_branch, compare_branch],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error: {result.stderr}"
        
        except subprocess.TimeoutExpired:
            return "Error: Git command timed out"
        except FileNotFoundError:
            return "Error: Git not found"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def analyze_diff_complexity(self, diff_text: str) -> Dict:
        """
        Analyze the complexity of changes in a diff
        
        Args:
            diff_text: Git diff output
        
        Returns:
            Analysis of change complexity
        """
        parsed = self.parse_diff(diff_text)
        
        analysis = {
            'risk_level': 'low',
            'concerns': [],
            'metrics': {
                'files_changed': parsed['stats']['files_changed'],
                'lines_added': parsed['stats']['insertions'],
                'lines_deleted': parsed['stats']['deletions'],
                'net_change': parsed['stats']['insertions'] - parsed['stats']['deletions']
            }
        }
        
        # Assess risk level
        if parsed['stats']['files_changed'] > 20:
            analysis['risk_level'] = 'high'
            analysis['concerns'].append('Large number of files changed')
        elif parsed['stats']['files_changed'] > 10:
            analysis['risk_level'] = 'medium'
        
        if parsed['stats']['total_changes'] > 500:
            analysis['risk_level'] = 'high'
            analysis['concerns'].append('Very large change set')
        elif parsed['stats']['total_changes'] > 200:
            if analysis['risk_level'] == 'low':
                analysis['risk_level'] = 'medium'
        
        # Check for risky patterns
        for file in parsed['files']:
            # Modifying critical files
            if any(pattern in file['file_path'] for pattern in ['auth', 'security', 'payment', 'database']):
                analysis['concerns'].append(f'Modifying sensitive file: {file["file_path"]}')
                analysis['risk_level'] = 'high'
        
        return analysis
    
    def suggest_review_focus(self, diff_text: str) -> List[str]:
        """
        Suggest areas to focus on during code review
        
        Args:
            diff_text: Git diff output
        
        Returns:
            List of review focus suggestions
        """
        parsed = self.parse_diff(diff_text)
        suggestions = []
        
        # Check for security-sensitive changes
        security_patterns = ['auth', 'password', 'token', 'secret', 'key', 'sql', 'query']
        for file in parsed['files']:
            file_lower = file['file_path'].lower()
            if any(pattern in file_lower for pattern in security_patterns):
                suggestions.append(f'Security review needed for {file["file_path"]}')
        
        # Check for large changes
        if parsed['stats']['total_changes'] > 200:
            suggestions.append('Large change set - consider breaking into smaller PRs')
        
        # Check for deleted lines
        if parsed['stats']['deletions'] > parsed['stats']['insertions']:
            suggestions.append('Significant code deletion - verify removed code is truly unused')
        
        # Check for test files
        test_files = [f for f in parsed['files'] if 'test' in f['file_path'].lower()]
        non_test_files = [f for f in parsed['files'] if 'test' not in f['file_path'].lower()]
        
        if non_test_files and not test_files:
            suggestions.append('No test changes detected - consider adding tests')
        
        return suggestions
"""
Report Generator Utility

Generates formatted code review reports in various formats (Markdown, HTML, JSON).
"""

from typing import Dict, List, Optional
from datetime import datetime
import json


class ReportGenerator:
    """Generates formatted code review reports"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_markdown(self, review_data: Dict) -> str:
        """
        Generate Markdown format report
        
        Args:
            review_data: Review results dictionary
        
        Returns:
            Markdown formatted report
        """
        md = f"""# Code Review Report

**Generated:** {self.timestamp}  
**Overall Grade:** {review_data.get('grade', 'N/A')}  
**Total Issues:** {self._count_total_issues(review_data.get('issues', {}))}

---

## Executive Summary

{review_data.get('summary', 'No summary available')}

---

## Issues by Priority

"""
        
        # Critical Issues
        critical = review_data.get('issues', {}).get('critical', [])
        md += f"### 🔴 Critical Issues ({len(critical)})\n\n"
        
        if critical:
            for i, issue in enumerate(critical, 1):
                md += self._format_issue_markdown(i, issue)
        else:
            md += "*No critical issues found.*\n\n"
        
        # High Priority
        high = review_data.get('issues', {}).get('high', [])
        md += f"### 🟡 High Priority Issues ({len(high)})\n\n"
        
        if high:
            for i, issue in enumerate(high, 1):
                md += self._format_issue_markdown(i, issue)
        else:
            md += "*No high priority issues found.*\n\n"
        
        # Medium Priority
        medium = review_data.get('issues', {}).get('medium', [])
        md += f"### 🟠 Medium Priority Issues ({len(medium)})\n\n"
        
        if medium:
            for i, issue in enumerate(medium[:5], 1):  # Show top 5
                md += self._format_issue_markdown(i, issue)
            if len(medium) > 5:
                md += f"\n*...and {len(medium) - 5} more medium priority issues*\n\n"
        else:
            md += "*No medium priority issues found.*\n\n"
        
        # Low Priority
        low = review_data.get('issues', {}).get('low', [])
        md += f"### 💡 Suggestions ({len(low)})\n\n"
        
        if low:
            for issue in low[:3]:  # Show top 3
                md += f"- {issue.get('description', 'Issue')}\n"
            if len(low) > 3:
                md += f"\n*...and {len(low) - 3} more suggestions*\n\n"
        else:
            md += "*No suggestions.*\n\n"
        
        # Strengths
        md += "---\n\n## ✅ Strengths\n\n"
        strengths = review_data.get('strengths', [])
        if strengths:
            for strength in strengths:
                md += f"- {strength}\n"
        else:
            md += "*No specific strengths identified.*\n"
        
        # Next Steps
        md += "\n---\n\n## 📋 Recommended Next Steps\n\n"
        next_steps = review_data.get('next_steps', [])
        if next_steps:
            for i, step in enumerate(next_steps, 1):
                md += f"{i}. {step}\n"
        else:
            md += "*No specific next steps.*\n"
        
        # Agent Feedback
        if 'agent_feedback' in review_data:
            md += "\n---\n\n## 🤖 Agent Analysis\n\n"
            for agent, feedback in review_data.get('agent_feedback', {}).items():
                md += f"### {agent}\n\n"
                if isinstance(feedback, dict) and 'summary' in feedback:
                    md += f"{feedback['summary']}\n\n"
                else:
                    md += f"{feedback}\n\n"
        
        return md
    
    def generate_html(self, review_data: Dict) -> str:
        """
        Generate HTML format report
        
        Args:
            review_data: Review results dictionary
        
        Returns:
            HTML formatted report
        """
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Review Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .grade {{
            font-size: 3rem;
            font-weight: bold;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .issue-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .critical {{ border-left: 5px solid #d32f2f; }}
        .high {{ border-left: 5px solid #f57c00; }}
        .medium {{ border-left: 5px solid #fbc02d; }}
        .low {{ border-left: 5px solid #388e3c; }}
        .issue {{
            padding: 15px;
            margin: 10px 0;
            background: #f9f9f9;
            border-radius: 5px;
        }}
        .issue-title {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .code-block {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85rem;
            font-weight: bold;
        }}
        .badge-critical {{ background: #d32f2f; color: white; }}
        .badge-high {{ background: #f57c00; color: white; }}
        .badge-medium {{ background: #fbc02d; color: black; }}
        .badge-low {{ background: #388e3c; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Code Review Report</h1>
        <p><strong>Generated:</strong> {self.timestamp}</p>
        <div class="grade">Grade: {review_data.get('grade', 'N/A')}</div>
        <p><strong>Total Issues:</strong> {self._count_total_issues(review_data.get('issues', {}))}</p>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <p>{review_data.get('summary', 'No summary available')}</p>
    </div>
"""
        
        # Issues sections
        issues = review_data.get('issues', {})
        
        for severity, color in [('critical', 'critical'), ('high', 'high'), ('medium', 'medium'), ('low', 'low')]:
            severity_issues = issues.get(severity, [])
            emoji = {'critical': '🔴', 'high': '🟡', 'medium': '🟠', 'low': '💡'}[severity]
            
            html += f"""
    <div class="issue-section {color}">
        <h2>{emoji} {severity.title()} Issues ({len(severity_issues)})</h2>
"""
            
            if severity_issues:
                for issue in severity_issues[:10]:  # Limit to 10 per section
                    html += self._format_issue_html(issue, severity)
            else:
                html += f"<p>No {severity} priority issues found.</p>"
            
            html += "    </div>\n"
        
        # Strengths
        html += """
    <div class="issue-section">
        <h2>✅ Strengths</h2>
        <ul>
"""
        for strength in review_data.get('strengths', []):
            html += f"            <li>{strength}</li>\n"
        
        html += """        </ul>
    </div>
    
    <div class="issue-section">
        <h2>📋 Recommended Next Steps</h2>
        <ol>
"""
        for step in review_data.get('next_steps', []):
            html += f"            <li>{step}</li>\n"
        
        html += """        </ol>
    </div>
</body>
</html>"""
        
        return html
    
    def generate_json(self, review_data: Dict) -> str:
        """
        Generate JSON format report
        
        Args:
            review_data: Review results dictionary
        
        Returns:
            JSON formatted report
        """
        report = {
            'timestamp': self.timestamp,
            'grade': review_data.get('grade', 'N/A'),
            'summary': review_data.get('summary', ''),
            'issues': review_data.get('issues', {}),
            'strengths': review_data.get('strengths', []),
            'next_steps': review_data.get('next_steps', []),
            'agent_feedback': review_data.get('agent_feedback', {}),
            'metrics': {
                'total_issues': self._count_total_issues(review_data.get('issues', {})),
                'critical_count': len(review_data.get('issues', {}).get('critical', [])),
                'high_count': len(review_data.get('issues', {}).get('high', [])),
                'medium_count': len(review_data.get('issues', {}).get('medium', [])),
                'low_count': len(review_data.get('issues', {}).get('low', []))
            }
        }
        
        return json.dumps(report, indent=2)
    
    def generate_text(self, review_data: Dict) -> str:
        """
        Generate plain text format report
        
        Args:
            review_data: Review results dictionary
        
        Returns:
            Plain text formatted report
        """
        text = f"""
{'='*80}
CODE REVIEW REPORT
{'='*80}

Generated: {self.timestamp}
Overall Grade: {review_data.get('grade', 'N/A')}
Total Issues: {self._count_total_issues(review_data.get('issues', {}))}

{'='*80}
EXECUTIVE SUMMARY
{'='*80}

{review_data.get('summary', 'No summary available')}

{'='*80}
ISSUES BY PRIORITY
{'='*80}

"""
        
        # Add issues
        issues = review_data.get('issues', {})
        
        for severity in ['critical', 'high', 'medium', 'low']:
            severity_issues = issues.get(severity, [])
            text += f"\n{severity.upper()} PRIORITY ({len(severity_issues)} issues)\n"
            text += "-" * 80 + "\n"
            
            if severity_issues:
                for i, issue in enumerate(severity_issues, 1):
                    text += f"\n{i}. {issue.get('description', 'Issue')}\n"
                    if 'line' in issue:
                        text += f"   Line: {issue['line']}\n"
                    if 'suggestion' in issue:
                        text += f"   Fix: {issue['suggestion']}\n"
            else:
                text += f"No {severity} priority issues.\n"
        
        # Strengths
        text += f"\n{'='*80}\n"
        text += "STRENGTHS\n"
        text += "=" * 80 + "\n"
        for strength in review_data.get('strengths', []):
            text += f"✓ {strength}\n"
        
        # Next steps
        text += f"\n{'='*80}\n"
        text += "RECOMMENDED NEXT STEPS\n"
        text += "=" * 80 + "\n"
        for i, step in enumerate(review_data.get('next_steps', []), 1):
            text += f"{i}. {step}\n"
        
        return text
    
    # Helper methods
    
    def _format_issue_markdown(self, number: int, issue: Dict) -> str:
        """Format a single issue in Markdown"""
        md = f"**{number}. {issue.get('description', 'Issue')}**\n"
        
        if 'line' in issue:
            md += f"- **Line:** {issue['line']}\n"
        
        if 'source' in issue:
            md += f"- **Detected by:** {issue['source']}\n"
        
        if 'severity' in issue:
            md += f"- **Severity:** {issue['severity']}\n"
        
        if 'suggestion' in issue:
            md += f"- **Fix:** {issue['suggestion']}\n"
        
        if 'code' in issue:
            md += f"\n```python\n{issue['code']}\n```\n"
        
        md += "\n"
        return md
    
    def _format_issue_html(self, issue: Dict, severity: str) -> str:
        """Format a single issue in HTML"""
        html = f"""
        <div class="issue">
            <div class="issue-title">
                <span class="badge badge-{severity}">{severity.upper()}</span>
                {issue.get('description', 'Issue')}
            </div>
"""
        
        if 'line' in issue:
            html += f"            <p><strong>Line:</strong> {issue['line']}</p>\n"
        
        if 'suggestion' in issue:
            html += f"            <p><strong>Fix:</strong> {issue['suggestion']}</p>\n"
        
        if 'code' in issue:
            html += f"            <div class='code-block'>{issue['code']}</div>\n"
        
        html += "        </div>\n"
        return html
    
    def _count_total_issues(self, issues: Dict) -> int:
        """Count total issues across all severities"""
        return sum(len(issues.get(severity, [])) for severity in ['critical', 'high', 'medium', 'low'])


# Convenience functions

def generate_report(review_data: Dict, format: str = 'markdown') -> str:
    """
    Generate a report in the specified format
    
    Args:
        review_data: Review results dictionary
        format: Output format ('markdown', 'html', 'json', 'text')
    
    Returns:
        Formatted report string
    """
    generator = ReportGenerator()
    
    if format == 'markdown':
        return generator.generate_markdown(review_data)
    elif format == 'html':
        return generator.generate_html(review_data)
    elif format == 'json':
        return generator.generate_json(review_data)
    elif format == 'text':
        return generator.generate_text(review_data)
    else:
        raise ValueError(f"Unknown format: {format}. Use 'markdown', 'html', 'json', or 'text'")


def save_report(review_data: Dict, filename: str, format: str = 'markdown'):
    """
    Generate and save a report to file
    
    Args:
        review_data: Review results dictionary
        filename: Output filename
        format: Output format
    """
    report = generate_report(review_data, format)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Report saved to {filename}")
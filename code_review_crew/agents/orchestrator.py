"""
Review Orchestrator Agent

Manages the code review workflow and synthesizes feedback from all agents.
Acts as the project manager coordinating the multi-agent review process.
"""

import autogen
from typing import Dict, List, Optional
from .base_agent import BaseAgent


class ReviewOrchestrator(BaseAgent):
    """
    Review Orchestrator agent responsible for:
    - Coordinating the code review process
    - Managing agent communication
    - Resolving conflicts between agents
    - Prioritizing issues by severity
    - Synthesizing final comprehensive review
    - Providing actionable next steps
    """
    
    def __init__(self, llm_config: Dict):
        """
        Initialize Review Orchestrator agent
        
        Args:
            llm_config: LLM configuration dictionary
        """
        self.llm_config = llm_config
        
        system_message = """
        You are the Review Orchestrator managing a team of specialized code review agents.
        
        Your team consists of:
        - Code Analyzer: Reviews code quality, style, and structure
        - Security Reviewer: Identifies security vulnerabilities
        - Performance Optimizer: Analyzes performance and suggests optimizations
        - Test Generator: Creates comprehensive unit tests
        
        Your responsibilities:
        1. Coordinate the review workflow
        2. Listen to all agent feedback
        3. Identify and resolve conflicts between agents
        4. Prioritize issues by severity and impact
        5. Synthesize a comprehensive final review
        6. Provide clear, actionable next steps
        7. Ensure the review stays focused and efficient
        
        Issue Priority Levels:
        - CRITICAL: Security vulnerabilities, data loss risks, crashes
        - HIGH: Significant bugs, major performance issues, broken functionality
        - MEDIUM: Code quality issues, moderate performance problems
        - LOW: Style inconsistencies, minor optimizations
        
        When agents disagree:
        - Facilitate discussion between agents
        - Consider the context and real-world impact
        - Make informed decisions based on best practices
        - Explain your reasoning clearly
        
        Final review should include:
        1. Executive Summary (2-3 sentences)
        2. Overall Grade (A+ to F)
        3. Critical Issues (must fix)
        4. High Priority Issues (should fix)
        5. Medium Priority Issues (nice to have)
        6. Low Priority Suggestions (optional)
        7. Strengths and good practices found
        8. Recommended next steps
        9. Estimated fix effort
        
        Keep reviews constructive, specific, and actionable.
        Balance thoroughness with practicality.
        """
        
        self.agent = autogen.AssistantAgent(
            name="ReviewOrchestrator",
            system_message=system_message,
            llm_config=llm_config
        )
        
        self.review_state = {
            'issues_found': [],
            'agent_feedback': {},
            'conflicts': [],
            'review_status': 'pending'
        }
    
    def create_agent(self) -> autogen.AssistantAgent:
        """Return the AutoGen agent"""
        return self.agent
    
    def initiate_review(self, code: str, config: Dict) -> str:
        """
        Start the code review process
        
        Args:
            code: Source code to review
            config: Review configuration (active agents, depth, etc.)
        
        Returns:
            Initial review message
        """
        self.review_state['review_status'] = 'in_progress'
        
        message = f"""
        Starting code review process.
        
        Configuration:
        - Analysis Depth: {config.get('depth', 'standard')}
        - Active Agents: {', '.join(config.get('active_agents', []))}
        - Max Rounds: {config.get('max_rounds', 20)}
        
        Let's begin with the Code Analyzer.
        Code Analyzer, please provide your analysis of the code quality and structure.
        """
        
        return message
    
    def collect_agent_feedback(self, agent_name: str, feedback: Dict):
        """
        Collect feedback from an agent
        
        Args:
            agent_name: Name of the agent providing feedback
            feedback: Feedback dictionary from the agent
        """
        self.review_state['agent_feedback'][agent_name] = feedback
        
        # Extract issues from feedback
        if 'issues' in feedback:
            for issue in feedback['issues']:
                issue['source'] = agent_name
                self.review_state['issues_found'].append(issue)
    
    def resolve_conflicts(self) -> List[Dict]:
        """
        Identify and resolve conflicts between agent recommendations
        
        Returns:
            List of resolved conflicts with decisions
        """
        conflicts = []
        
        # Check for conflicting recommendations
        issues = self.review_state['issues_found']
        
        # Group issues by line number
        issues_by_line = {}
        for issue in issues:
            line = issue.get('line', 0)
            if line not in issues_by_line:
                issues_by_line[line] = []
            issues_by_line[line].append(issue)
        
        # Identify conflicts (multiple agents commenting on same line with different advice)
        for line, line_issues in issues_by_line.items():
            if len(line_issues) > 1:
                conflicts.append({
                    'line': line,
                    'issues': line_issues,
                    'resolution': self._resolve_conflict(line_issues)
                })
        
        self.review_state['conflicts'] = conflicts
        return conflicts
    
    def _resolve_conflict(self, conflicting_issues: List[Dict]) -> Dict:
        """
        Resolve a specific conflict between agent recommendations
        
        Args:
            conflicting_issues: List of conflicting issue reports
        
        Returns:
            Resolution decision
        """
        # Priority: Security > Performance > Code Quality
        priority_order = ['SecurityReviewer', 'PerformanceOptimizer', 'CodeAnalyzer']
        
        # Find highest priority issue
        for agent in priority_order:
            for issue in conflicting_issues:
                if issue.get('source') == agent:
                    return {
                        'decision': 'prioritize',
                        'chosen_issue': issue,
                        'reason': f'{agent} takes priority for this issue type'
                    }
        
        # Default: choose first issue
        return {
            'decision': 'first',
            'chosen_issue': conflicting_issues[0],
            'reason': 'No clear priority, selecting first recommendation'
        }
    
    def prioritize_issues(self) -> Dict:
        """
        Prioritize all collected issues by severity
        
        Returns:
            Categorized issues by priority level
        """
        categorized = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for issue in self.review_state['issues_found']:
            severity = issue.get('severity', 'medium').lower()
            if severity in categorized:
                categorized[severity].append(issue)
        
        return categorized
    
    def synthesize_review(self) -> Dict:
        """
        Synthesize final comprehensive review from all agent feedback
        
        Returns:
            Complete review report
        """
        prioritized_issues = self.prioritize_issues()
        
        # Calculate overall grade
        grade = self._calculate_grade(prioritized_issues)
        
        # Generate executive summary
        summary = self._generate_summary(prioritized_issues, grade)
        
        # Identify strengths
        strengths = self._identify_strengths()
        
        # Determine next steps
        next_steps = self._determine_next_steps(prioritized_issues)
        
        review = {
            'summary': summary,
            'grade': grade,
            'issues': prioritized_issues,
            'strengths': strengths,
            'next_steps': next_steps,
            'conflicts_resolved': len(self.review_state['conflicts']),
            'agent_feedback': self.review_state['agent_feedback'],
            'review_status': 'complete'
        }
        
        self.review_state['review_status'] = 'complete'
        
        return review
    
    def _calculate_grade(self, issues: Dict) -> str:
        """Calculate overall grade based on issues found"""
        # Scoring system
        score = 100
        score -= len(issues['critical']) * 20
        score -= len(issues['high']) * 10
        score -= len(issues['medium']) * 5
        score -= len(issues['low']) * 2
        
        # Convert to letter grade
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 75:
            return 'C+'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _generate_summary(self, issues: Dict, grade: str) -> str:
        """Generate executive summary of the review"""
        total_issues = sum(len(v) for v in issues.values())
        
        if total_issues == 0:
            return f"Excellent code quality! Grade: {grade}. No significant issues found."
        
        summary = f"Review complete. Grade: {grade}. "
        
        if issues['critical']:
            summary += f"Found {len(issues['critical'])} critical security/stability issues that must be addressed immediately. "
        
        if issues['high']:
            summary += f"{len(issues['high'])} high-priority issues detected requiring attention. "
        
        if issues['medium'] or issues['low']:
            summary += f"Additional {len(issues['medium']) + len(issues['low'])} suggestions for improvement."
        
        return summary
    
    def _identify_strengths(self) -> List[str]:
        """Identify positive aspects of the code"""
        strengths = []
        
        # Check agent feedback for positive comments
        for agent, feedback in self.review_state['agent_feedback'].items():
            if 'strengths' in feedback:
                strengths.extend(feedback['strengths'])
        
        # Default strengths if none identified
        if not strengths:
            strengths = ["Code structure is readable", "Basic functionality is implemented"]
        
        return strengths
    
    def _determine_next_steps(self, issues: Dict) -> List[str]:
        """Determine recommended next steps"""
        steps = []
        
        if issues['critical']:
            steps.append("URGENT: Address critical security/stability issues immediately")
        
        if issues['high']:
            steps.append("Fix high-priority bugs and performance issues")
        
        if issues['medium']:
            steps.append("Refactor code quality issues for better maintainability")
        
        if not issues['critical'] and not issues['high']:
            steps.append("Consider implementing suggested optimizations")
            steps.append("Add more comprehensive test coverage")
        
        steps.append("Run review again after fixes to verify improvements")
        
        return steps
    
    def format_final_report(self, review: Dict) -> str:
        """
        Format the final review report for display
        
        Args:
            review: Review dictionary from synthesize_review
        
        Returns:
            Formatted report string
        """
        report = f"""
# Code Review Report

## Executive Summary
{review['summary']}

**Overall Grade: {review['grade']}**

---

## Issues by Priority

### 🔴 Critical Issues ({len(review['issues']['critical'])})
"""
        
        for issue in review['issues']['critical']:
            report += f"\n**{issue.get('description', 'Issue')}** (Line {issue.get('line', 'N/A')})\n"
            report += f"- Source: {issue.get('source', 'Unknown')}\n"
            report += f"- Severity: {issue.get('severity', 'Critical')}\n"
            if 'suggestion' in issue:
                report += f"- Fix: {issue['suggestion']}\n"
        
        report += f"""

### 🟡 High Priority ({len(review['issues']['high'])})
"""
        
        for issue in review['issues']['high'][:5]:  # Show top 5
            report += f"\n- {issue.get('description', 'Issue')} (Line {issue.get('line', 'N/A')})\n"
        
        report += f"""

### 💡 Additional Suggestions ({len(review['issues']['medium']) + len(review['issues']['low'])})
Review the detailed report for all suggestions.

---

## Strengths
"""
        
        for strength in review['strengths']:
            report += f"- {strength}\n"
        
        report += """

---

## Recommended Next Steps
"""
        
        for step in review['next_steps']:
            report += f"1. {step}\n"
        
        return report
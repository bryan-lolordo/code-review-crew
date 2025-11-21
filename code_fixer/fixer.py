"""
Code Fixer - Main Workflow

LangGraph-based iterative code fixer that takes issues from AutoGen
and fixes them one by one using a state machine.

Now includes LLM fallback for complex issues that don't match patterns.
"""

from typing import Dict, List
from langgraph.graph import StateGraph, END

from .state import CodeFixState
from .nodes import FixerNodes


class CodeFixer:
    """
    LangGraph-based iterative code fixer
    
    Takes issues identified by AutoGen multi-agent review and
    iteratively fixes them using a state machine workflow:
    
    Fix Issue → Test Code → (Continue or Done)
         ↑                           |
         └───────── Loop ────────────┘
    
    Features:
    - Iterative fixing with state tracking
    - Automatic testing after each fix
    - Configurable max iterations
    - Handles multiple issue types (SQL, crypto, performance, etc.)
    - Pattern-based fixes for common issues (fast, free)
    - LLM fallback for complex issues (slower, smarter)
    """
    
    def __init__(self, llm_config: Dict = None):
        """
        Initialize code fixer
        
        Args:
            llm_config: LLM configuration for fallback fixes
                       Example: {"model": "gpt-4", "api_key": "sk-..."}
                       If not provided, will use OPENAI_API_KEY from environment
        """
        import os
        
        # Ensure we have API key for LLM fallback
        if llm_config is None:
            llm_config = {}
        
        if 'api_key' not in llm_config:
            llm_config['api_key'] = os.getenv("OPENAI_API_KEY")
        
        if 'model' not in llm_config:
            llm_config['model'] = "gpt-4"
        
        self.llm_config = llm_config
        self.nodes = FixerNodes(llm_config=self.llm_config)
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow
        
        Workflow structure:
        
        [Start] → fix_issue → test_code → {decision}
                      ↑                      ↓
                      └──── continue ────────┤
                                             ↓
                                          finalize → [End]
        
        Returns:
            Compiled LangGraph workflow
        """
        
        # Create workflow with state type
        workflow = StateGraph(CodeFixState)
        
        # Add nodes
        workflow.add_node("fix_issue", self.nodes.fix_issue_node)
        workflow.add_node("test_code", self.nodes.test_code_node)
        workflow.add_node("finalize", self.nodes.finalize_node)
        
        # Set entry point
        workflow.set_entry_point("fix_issue")
        
        # Add edges
        workflow.add_edge("fix_issue", "test_code")
        
        # Conditional routing from test_code
        workflow.add_conditional_edges(
            "test_code",
            self.nodes.route_after_test,
            {
                "continue": "fix_issue",  # More issues, loop back
                "done": "finalize",        # All done!
                "failed": "finalize"       # Hit max iterations
            }
        )
        
        # Finalize always ends
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def fix_code(
        self, 
        code: str, 
        issues: List[Dict], 
        max_iterations: int = 10
    ) -> Dict:
        """
        Fix code issues iteratively
        
        This is the main entry point. It takes code with issues
        and iteratively fixes them using the LangGraph workflow.
        
        Strategy:
        1. Try pattern-based fixes first (fast, free, deterministic)
        2. Fall back to LLM for issues without patterns (slower, smarter)
        
        Args:
            code: Original code with issues
            issues: List of issues from AutoGen review
                    Format: [{"severity": "Critical", "description": "...", ...}, ...]
            max_iterations: Maximum fix attempts (default: 10)
        
        Returns:
            Dictionary with results:
            {
                "fixed_code": str,           # The fixed code
                "iterations": int,           # Number of iterations
                "issues_fixed": int,         # Number fixed
                "issues_remaining": int,     # Number not fixed
                "status": str,               # "done" or "failed"
                "fixed_issues": List[Dict]   # List of fixed issues
            }
        
        Example:
            ```python
            fixer = CodeFixer()
            
            issues = [
                {"severity": "Critical", "description": "SQL injection on line 4"},
                {"severity": "High", "description": "Weak MD5 crypto"}
            ]
            
            result = fixer.fix_code(buggy_code, issues, max_iterations=5)
            
            print(result["fixed_code"])
            print(f"Fixed {result['issues_fixed']} issues")
            ```
        """
        
        print("\n" + "="*80)
        print(f"🔧 CODE FIXER - Starting iterative fix process")
        print("="*80)
        print(f"Issues to fix: {len(issues)}")
        print(f"Max iterations: {max_iterations}")
        
        # Show LLM status
        if self.llm_config.get('api_key'):
            print(f"LLM Fallback: ✅ Enabled ({self.llm_config.get('model', 'gpt-4')})")
        else:
            print(f"LLM Fallback: ⚠️  Disabled (no API key)")
        
        # Debug: Show received issues
        print(f"\n🔍 DEBUG FIXER: Received {len(issues)} issues:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. [{issue.get('severity', '?')}] {issue.get('description', 'No desc')[:60]}")
        
        # Sort issues by severity (Critical > High > Medium > Low)
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        sorted_issues = sorted(
            issues, 
            key=lambda x: severity_order.get(x.get('severity', 'Low'), 4)
        )
        
        # Initialize state
        initial_state: CodeFixState = {
            "original_code": code,
            "current_code": code,
            "issues": sorted_issues,
            "fixed_issues": [],
            "test_results": {},
            "iteration": 0,
            "max_iterations": max_iterations,
            "status": "fixing"
        }
        
        # Run the workflow
        final_state = self.workflow.invoke(initial_state)
        
        # Return results
        return {
            "fixed_code": final_state["current_code"],
            "iterations": final_state["iteration"],
            "issues_fixed": len(final_state["fixed_issues"]),
            "issues_remaining": len(final_state["issues"]),
            "status": final_state["status"],
            "fixed_issues": final_state["fixed_issues"],
            "test_results": final_state["test_results"]
        }
    
    def fix_single_issue(self, code: str, issue: Dict) -> str:
        """
        Fix a single issue (convenience method)
        
        Args:
            code: Code to fix
            issue: Single issue to fix
        
        Returns:
            Fixed code
        """
        
        result = self.fix_code(code, [issue], max_iterations=1)
        return result["fixed_code"]


# Convenience function for quick usage
def quick_fix(code: str, issues: List[Dict], max_iterations: int = 10) -> str:
    """
    Quick fix function - returns just the fixed code
    
    Args:
        code: Code to fix
        issues: List of issues
        max_iterations: Max iterations
    
    Returns:
        Fixed code string
    
    Example:
        ```python
        from code_fixer import quick_fix
        
        fixed = quick_fix(buggy_code, issues)
        print(fixed)
        ```
    """
    
    fixer = CodeFixer()
    result = fixer.fix_code(code, issues, max_iterations)
    return result["fixed_code"]
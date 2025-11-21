"""
State Definitions for Code Fixer

Defines the state structure for the LangGraph workflow.
"""

from typing import TypedDict, List, Dict, Literal


class CodeFixState(TypedDict):
    """
    State for iterative code fixing workflow
    
    This state is passed between nodes in the LangGraph workflow
    and tracks all information needed for fixing code issues.
    """
    
    # Code
    original_code: str          # The original buggy code
    current_code: str           # Code being worked on (updated each iteration)
    
    # Issues
    issues: List[Dict]          # Issues still to fix (from AutoGen review)
    fixed_issues: List[Dict]    # Issues that have been fixed
    
    # Testing
    test_results: Dict          # Results from testing the fixed code
    
    # Iteration tracking
    iteration: int              # Current iteration number
    max_iterations: int         # Maximum iterations allowed
    
    # Status
    status: Literal["fixing", "testing", "done", "failed"]  # Current workflow status


class Issue(TypedDict):
    """
    Structure for a code issue
    
    This matches the format from AutoGen agent reviews
    """
    severity: str               # "Critical", "High", "Medium", "Low"
    description: str            # What's wrong
    line: int                   # Line number (optional)
    agent: str                  # Which agent found it (optional)


class TestResult(TypedDict):
    """
    Structure for test results
    """
    passed: bool                # Did tests pass?
    syntax_valid: bool          # Is syntax valid?
    tests_run: int              # Number of tests executed
    tests_passed: int           # Number of tests that passed
    error: str                  # Error message if failed (optional)


# Type aliases for clarity
FixStatus = Literal["fixing", "testing", "done", "failed"]
Severity = Literal["Critical", "High", "Medium", "Low"]
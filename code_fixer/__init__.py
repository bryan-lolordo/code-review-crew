"""
Code Fixer - LangGraph-based Iterative Code Fixer

A LangGraph implementation that takes issues from AutoGen code review
and iteratively fixes them using a state machine workflow.

Main exports:
- CodeFixer: Main class for fixing code
- quick_fix: Convenience function
- CodeFixState: State type definition
"""

from .fixer import CodeFixer, quick_fix
from .state import CodeFixState, Issue, TestResult
from .nodes import FixerNodes

__version__ = "1.0.0"

__all__ = [
    "CodeFixer",
    "quick_fix",
    "CodeFixState",
    "Issue",
    "TestResult",
    "FixerNodes"
]
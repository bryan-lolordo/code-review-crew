"""
Code Review Crew

Multi-agent AI system for comprehensive code review using Microsoft AutoGen.
"""

__version__ = '0.1.0'
__author__ = 'Bryan LoLordo'

from .agents import (
    CodeAnalyzer,
    SecurityReviewer,
    PerformanceOptimizer,
    TestGenerator,
    ReviewOrchestrator
)

from .tools import (
    LintingTool,
    SecurityScanner,
    ComplexityAnalyzer,
    GitTool
)

__all__ = [
    'CodeAnalyzer',
    'SecurityReviewer',
    'PerformanceOptimizer',
    'TestGenerator',
    'ReviewOrchestrator',
    'LintingTool',
    'SecurityScanner',
    'ComplexityAnalyzer',
    'GitTool'
]
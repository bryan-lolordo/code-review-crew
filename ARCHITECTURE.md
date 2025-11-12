# 🏗️ Code Review Crew - Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Multi-Agent Architecture](#multi-agent-architecture)
3. [Agent Design](#agent-design)
4. [Tool Integration](#tool-integration)
5. [Code Execution System](#code-execution-system)
6. [Communication Patterns](#communication-patterns)
7. [Data Flow](#data-flow)
8. [Security Architecture](#security-architecture)
9. [Development Guide](#development-guide)

---

## System Overview

Code Review Crew is built on a **multi-agent architecture** using Microsoft AutoGen, where specialized AI agents collaborate through group chat to perform comprehensive code reviews.

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│  (Streamlit Web UI + CLI Interface)                     │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                   Agent Orchestration Layer              │
│  (AutoGen Group Chat + Agent Team)                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                    Tool Integration Layer                │
│  (Pylint, Bandit, Radon, Pytest)                       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                    Execution Layer                       │
│  (Docker Sandbox + Code Runner)                         │
└─────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Agent Autonomy**: Each agent makes independent decisions
2. **Collaborative Intelligence**: Agents debate to reach consensus
3. **Tool Augmentation**: Agents use real static analysis tools
4. **Safe Execution**: All code runs in isolated containers
5. **Modular Architecture**: Easy to add new agents or tools

---

## Multi-Agent Architecture

### Agent Ecosystem

```
                    ┌─────────────────────────┐
                    │  Review Orchestrator    │
                    │  - Manages workflow     │
                    │  - Synthesizes feedback │
                    │  - Prioritizes issues   │
                    └───────────┬─────────────┘
                                │
                    ┌───────────┴─────────────┐
                    │   AutoGen GroupChat     │
                    │   - Multi-agent comm    │
                    │   - Turn management     │
                    │   - Message routing     │
                    └───────────┬─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐    ┌────────▼────────┐    ┌────────▼─────────┐
│ Code Analyzer  │    │ Security        │    │ Performance      │
│                │    │ Reviewer        │    │ Optimizer        │
│ AssistantAgent │    │ AssistantAgent  │    │ AssistantAgent   │
└───────┬────────┘    └────────┬────────┘    └────────┬─────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Test Generator     │
                    │  AssistantAgent     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Code Executor      │
                    │  UserProxyAgent     │
                    │  + Docker Sandbox   │
                    └─────────────────────┘
```

### AutoGen Configuration

```python
# Base LLM configuration
llm_config = {
    "model": "gpt-4",
    "temperature": 0.7,
    "api_key": os.getenv("OPENAI_API_KEY"),
    "cache_seed": None  # Disable caching for diverse responses
}

# Group chat setup
agents = [
    orchestrator,
    code_analyzer,
    security_reviewer,
    performance_optimizer,
    test_generator
]

group_chat = autogen.GroupChat(
    agents=agents,
    messages=[],
    max_round=20,  # Maximum conversation rounds
    speaker_selection_method="auto"  # Let AutoGen decide speaker order
)

manager = autogen.GroupChatManager(
    groupchat=group_chat,
    llm_config=llm_config
)
```

---

## Agent Design

### 1. Review Orchestrator

**Type:** `AssistantAgent`  
**Role:** Project manager and synthesizer

```python
orchestrator = autogen.AssistantAgent(
    name="ReviewOrchestrator",
    system_message="""
    You are the Review Orchestrator. Your responsibilities:
    
    1. Coordinate the code review process
    2. Listen to all agent feedback
    3. Identify conflicts and resolve them
    4. Prioritize issues by severity
    5. Synthesize a final comprehensive review
    6. Provide actionable next steps
    
    When agents disagree, facilitate discussion.
    Ensure all critical issues are addressed.
    Keep the review focused and efficient.
    """,
    llm_config=llm_config
)
```

**Key Responsibilities:**
- Manages review workflow
- Resolves agent disagreements
- Prioritizes issues (Critical → High → Medium → Low)
- Generates final review summary
- Estimates fix effort for each issue

### 2. Code Analyzer

**Type:** `AssistantAgent`  
**Role:** Code quality expert

```python
code_analyzer = autogen.AssistantAgent(
    name="CodeAnalyzer",
    system_message="""
    You are a Code Analyzer specializing in:
    
    - Code smells and anti-patterns
    - PEP 8 style compliance (Python)
    - Code readability and maintainability
    - DRY (Don't Repeat Yourself) violations
    - SOLID principles
    - Proper error handling
    
    Use the linting_tool to run Pylint analysis.
    Provide specific line numbers and suggestions.
    Distinguish between style issues and functional bugs.
    """,
    llm_config=llm_config,
    function_map={
        "run_pylint": linting_tool.run_pylint,
        "check_pep8": linting_tool.check_pep8
    }
)
```

**Analysis Focus:**
- Code structure and organization
- Naming conventions
- Function/class complexity
- Code duplication
- Design patterns usage

**Tool Integration:**
```python
# Pylint analysis
pylint_results = code_analyzer.run_pylint(code)
# Returns: {score: 8.5, issues: [...], suggestions: [...]}
```

### 3. Security Reviewer

**Type:** `AssistantAgent`  
**Role:** Security expert

```python
security_reviewer = autogen.AssistantAgent(
    name="SecurityReviewer",
    system_message="""
    You are a Security Reviewer specializing in:
    
    - SQL injection vulnerabilities
    - XSS (Cross-Site Scripting)
    - Authentication/authorization flaws
    - Input validation issues
    - Sensitive data exposure
    - OWASP Top 10 vulnerabilities
    
    Use the security_scanner tool (Bandit) for automated checks.
    Always explain the security impact of issues.
    Provide concrete examples of exploits.
    Suggest secure alternatives.
    """,
    llm_config=llm_config,
    function_map={
        "scan_security": security_scanner.run_bandit,
        "check_owasp": security_scanner.check_owasp_top10
    }
)
```

**Security Checks:**
- Input sanitization
- SQL injection prevention
- Authentication mechanisms
- Authorization controls
- Cryptography usage
- Dependency vulnerabilities

### 4. Performance Optimizer

**Type:** `AssistantAgent`  
**Role:** Performance expert

```python
performance_optimizer = autogen.AssistantAgent(
    name="PerformanceOptimizer",
    system_message="""
    You are a Performance Optimizer specializing in:
    
    - Algorithmic complexity (Big O analysis)
    - Memory usage optimization
    - Database query efficiency
    - Loop optimization
    - Caching opportunities
    - Profiling insights
    
    Use the complexity_analyzer tool (Radon) for metrics.
    Identify bottlenecks and suggest optimizations.
    Provide complexity analysis (O(n), O(n²), etc.).
    Balance performance with readability.
    """,
    llm_config=llm_config,
    function_map={
        "analyze_complexity": complexity_analyzer.calculate_complexity,
        "find_bottlenecks": complexity_analyzer.profile_code
    }
)
```

**Performance Analysis:**
- Time complexity
- Space complexity
- Database query optimization
- Caching strategies
- Lazy loading opportunities

### 5. Test Generator

**Type:** `AssistantAgent`  
**Role:** Testing expert

```python
test_generator = autogen.AssistantAgent(
    name="TestGenerator",
    system_message="""
    You are a Test Generator specializing in:
    
    - Unit test creation
    - Edge case identification
    - Test coverage analysis
    - Mocking and fixtures
    - Integration test design
    - Test-driven development
    
    Generate pytest-compatible tests.
    Cover happy paths and edge cases.
    Include tests for error conditions.
    Aim for high code coverage.
    """,
    llm_config=llm_config
)
```

**Test Creation:**
- Unit tests for all functions
- Edge case scenarios
- Error handling tests
- Integration test suggestions
- Mock objects for dependencies

### 6. Code Executor

**Type:** `UserProxyAgent`  
**Role:** Code execution and validation

```python
code_executor = autogen.UserProxyAgent(
    name="CodeExecutor",
    human_input_mode="NEVER",  # Fully autonomous
    max_consecutive_auto_reply=10,
    code_execution_config={
        "work_dir": "sandbox",
        "use_docker": True,
        "timeout": 60,
        "last_n_messages": 3
    }
)
```

**Execution Capabilities:**
- Runs submitted code safely
- Executes generated tests
- Validates proposed fixes
- Reports runtime errors
- Measures test coverage

---

## Tool Integration

### Linting Tool (Pylint)

**File:** `code_review_crew/tools/linting_tool.py`

```python
import subprocess
import json
from typing import Dict, List

class LintingTool:
    """Wrapper for Pylint static analysis"""
    
    def run_pylint(self, code: str) -> Dict:
        """
        Run Pylint on code and return structured results
        
        Returns:
            {
                'score': float (0-10),
                'issues': [
                    {
                        'type': 'convention|refactor|warning|error',
                        'line': int,
                        'message': str,
                        'symbol': str
                    }
                ],
                'summary': str
            }
        """
        # Write code to temp file
        with open('/tmp/temp_code.py', 'w') as f:
            f.write(code)
        
        # Run pylint
        result = subprocess.run(
            ['pylint', '/tmp/temp_code.py', '--output-format=json'],
            capture_output=True,
            text=True
        )
        
        # Parse JSON output
        issues = json.loads(result.stdout)
        
        # Calculate score
        score = self._calculate_score(issues)
        
        return {
            'score': score,
            'issues': self._format_issues(issues),
            'summary': self._generate_summary(score, issues)
        }
    
    def check_pep8(self, code: str) -> List[Dict]:
        """Check PEP 8 compliance using pycodestyle"""
        # Implementation
        pass
```

### Security Scanner (Bandit)

**File:** `code_review_crew/tools/security_scanner.py`

```python
import bandit
from bandit.core import manager as bandit_manager

class SecurityScanner:
    """Wrapper for Bandit security analysis"""
    
    def run_bandit(self, code: str) -> Dict:
        """
        Scan code for security vulnerabilities
        
        Returns:
            {
                'high_severity': [...],
                'medium_severity': [...],
                'low_severity': [...],
                'total_issues': int,
                'confidence_scores': {...}
            }
        """
        # Initialize Bandit manager
        b_mgr = bandit_manager.BanditManager(
            bandit.config.BanditConfig(), 
            'file'
        )
        
        # Run scan
        b_mgr.discover_files(['/tmp/temp_code.py'])
        b_mgr.run_tests()
        
        # Get results
        results = b_mgr.get_issue_list()
        
        return self._categorize_issues(results)
    
    def check_owasp_top10(self, code: str) -> List[str]:
        """Check for OWASP Top 10 vulnerabilities"""
        vulnerabilities = []
        
        # Check for SQL injection
        if self._has_sql_injection(code):
            vulnerabilities.append('A03:2021 - Injection')
        
        # Check for broken authentication
        if self._has_weak_auth(code):
            vulnerabilities.append('A07:2021 - Identification and Authentication Failures')
        
        # ... more checks
        
        return vulnerabilities
```

### Complexity Analyzer (Radon)

**File:** `code_review_crew/tools/complexity_analyzer.py`

```python
from radon.complexity import cc_visit
from radon.metrics import mi_visit, h_visit

class ComplexityAnalyzer:
    """Wrapper for Radon complexity analysis"""
    
    def calculate_complexity(self, code: str) -> Dict:
        """
        Calculate cyclomatic complexity
        
        Returns:
            {
                'functions': [
                    {
                        'name': str,
                        'complexity': int,
                        'rank': str (A-F),
                        'line': int
                    }
                ],
                'average_complexity': float,
                'maintainability_index': float
            }
        """
        # Cyclomatic complexity
        complexity_results = cc_visit(code)
        
        # Maintainability index
        mi_score = mi_visit(code, multi=True)
        
        # Halstead metrics
        halstead = h_visit(code)
        
        return {
            'functions': self._format_complexity(complexity_results),
            'average_complexity': self._calculate_average(complexity_results),
            'maintainability_index': mi_score,
            'halstead_metrics': halstead
        }
    
    def find_bottlenecks(self, code: str) -> List[Dict]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        # Find high-complexity functions
        complexity = self.calculate_complexity(code)
        for func in complexity['functions']:
            if func['complexity'] > 10:
                bottlenecks.append({
                    'type': 'high_complexity',
                    'function': func['name'],
                    'complexity': func['complexity'],
                    'suggestion': 'Consider refactoring into smaller functions'
                })
        
        # Find nested loops
        nested_loops = self._find_nested_loops(code)
        for loop in nested_loops:
            bottlenecks.append({
                'type': 'nested_loops',
                'line': loop['line'],
                'depth': loop['depth'],
                'suggestion': 'Consider using hash maps or preprocessing'
            })
        
        return bottlenecks
```

### Test Runner (Pytest)

**File:** `code_review_crew/tools/test_runner.py`

```python
import pytest
import coverage

class TestRunner:
    """Wrapper for pytest and coverage"""
    
    def run_tests(self, test_code: str, source_code: str) -> Dict:
        """
        Run generated tests and measure coverage
        
        Returns:
            {
                'passed': int,
                'failed': int,
                'errors': List[str],
                'coverage': float (0-100),
                'duration': float (seconds)
            }
        """
        # Write files
        with open('/tmp/test_temp.py', 'w') as f:
            f.write(test_code)
        with open('/tmp/source_temp.py', 'w') as f:
            f.write(source_code)
        
        # Initialize coverage
        cov = coverage.Coverage()
        cov.start()
        
        # Run pytest
        result = pytest.main([
            '/tmp/test_temp.py',
            '-v',
            '--tb=short'
        ])
        
        cov.stop()
        cov.save()
        
        # Get coverage data
        coverage_percent = cov.report()
        
        return {
            'passed': result.passed,
            'failed': result.failed,
            'coverage': coverage_percent,
            'duration': result.duration
        }
```

---

## Code Execution System

### Docker Sandbox Architecture

```
┌─────────────────────────────────────────┐
│           Host System                    │
│  ┌─────────────────────────────────┐   │
│  │   AutoGen UserProxyAgent        │   │
│  │   - Manages execution           │   │
│  │   - Enforces limits             │   │
│  └──────────────┬──────────────────┘   │
│                 │                       │
│  ┌──────────────▼──────────────────┐   │
│  │   Docker Container               │   │
│  │   ┌─────────────────────────┐   │   │
│  │   │ Isolated Environment    │   │   │
│  │   │ - Python runtime        │   │   │
│  │   │ - No network access     │   │   │
│  │   │ - Limited resources     │   │   │
│  │   │ - Auto cleanup          │   │   │
│  │   └─────────────────────────┘   │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### Sandbox Configuration

```python
# Dockerfile for execution environment
FROM python:3.9-slim

# Install minimal dependencies
RUN pip install pytest coverage

# Create non-root user
RUN useradd -m -u 1000 sandbox
USER sandbox

# Set working directory
WORKDIR /sandbox

# Resource limits set via Docker run
# CPU: 1 core
# Memory: 512MB
# Timeout: 60 seconds
```

### Execution Workflow

```python
class SandboxManager:
    """Manages safe code execution in Docker"""
    
    def execute_code(self, code: str, timeout: int = 60) -> Dict:
        """
        Execute code in isolated container
        
        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds
        
        Returns:
            {
                'stdout': str,
                'stderr': str,
                'exit_code': int,
                'duration': float,
                'timeout': bool
            }
        """
        # Create temporary directory
        work_dir = self._create_work_dir()
        
        # Write code to file
        code_file = os.path.join(work_dir, 'code.py')
        with open(code_file, 'w') as f:
            f.write(code)
        
        # Run Docker container
        client = docker.from_env()
        try:
            result = client.containers.run(
                image='code-review-sandbox:latest',
                command=f'python /sandbox/code.py',
                volumes={work_dir: {'bind': '/sandbox', 'mode': 'rw'}},
                mem_limit='512m',
                cpu_period=100000,
                cpu_quota=100000,  # 1 CPU
                network_disabled=True,
                timeout=timeout,
                remove=True
            )
            
            return {
                'stdout': result.decode('utf-8'),
                'stderr': '',
                'exit_code': 0,
                'timeout': False
            }
            
        except docker.errors.ContainerError as e:
            return {
                'stdout': '',
                'stderr': str(e),
                'exit_code': e.exit_status,
                'timeout': False
            }
            
        except docker.errors.Timeout:
            return {
                'stdout': '',
                'stderr': 'Execution timeout',
                'exit_code': -1,
                'timeout': True
            }
        
        finally:
            # Cleanup
            self._cleanup_work_dir(work_dir)
```

---

## Communication Patterns

### Group Chat Flow

```
User submits code
    ↓
[Orchestrator] "Let's review this code. Code Analyzer, please start."
    ↓
[Code Analyzer] "Found 3 style issues, 1 potential bug on line 45..."
    ↓
[Security Reviewer] "I agree with the bug. Also found SQL injection risk..."
    ↓
[Performance Optimizer] "The loop on line 67 is O(n²), suggest using hash map..."
    ↓
[Code Analyzer] "Good catch on performance. But security should be priority."
    ↓
[Security Reviewer] "Agreed. SQL injection is critical."
    ↓
[Orchestrator] "Prioritizing: 1. SQL injection (Critical), 2. Bug (High), 3. Performance (Medium)"
    ↓
[Test Generator] "Generated tests for edge cases including injection attempts..."
    ↓
[Code Executor] "Running tests... 2 passed, 1 failed (injection test)"
    ↓
[Orchestrator] "Confirmed. SQL injection vulnerability verified. Here's the final report..."
```

### Agent Selection Strategies

**Auto Selection** (Default)
```python
# AutoGen decides based on context
group_chat = autogen.GroupChat(
    agents=agents,
    speaker_selection_method="auto"
)
```

**Round Robin**
```python
# Each agent speaks in turn
group_chat = autogen.GroupChat(
    agents=agents,
    speaker_selection_method="round_robin"
)
```

**Custom Selection**
```python
def select_speaker(last_speaker, groupchat):
    """Custom logic for speaker selection"""
    if "security" in groupchat.messages[-1]['content'].lower():
        return security_reviewer
    elif "performance" in groupchat.messages[-1]['content'].lower():
        return performance_optimizer
    else:
        return code_analyzer

group_chat = autogen.GroupChat(
    agents=agents,
    speaker_selection_method=select_speaker
)
```

### Message Protocol

```python
# Standard message format
{
    'role': 'assistant|user',
    'content': str,
    'name': str,  # Agent name
    'function_call': {
        'name': str,
        'arguments': str
    },
    'metadata': {
        'timestamp': datetime,
        'agent_type': str,
        'confidence': float
    }
}
```

---

## Data Flow

### Review Request Flow

```
┌─────────────┐
│    User     │ Submits code via UI
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Streamlit App   │ Validates input, creates review request
└──────┬───────────┘
       │
       ▼
┌───────────────────┐
│  Orchestrator     │ Initializes group chat
└──────┬────────────┘
       │
       ▼
┌────────────────────────────────────────────┐
│         AutoGen Group Chat                 │
│  ┌────────────────────────────────────┐   │
│  │ Agents take turns analyzing        │   │
│  │ - Code Analyzer runs Pylint        │   │
│  │ - Security runs Bandit             │   │
│  │ - Performance runs Radon           │   │
│  │ - Test Generator creates tests     │   │
│  │ - Executor runs tests in Docker    │   │
│  └────────────────────────────────────┘   │
└──────┬─────────────────────────────────────┘
       │
       ▼
┌──────────────────┐
│  Report          │ Synthesized feedback
│  Generator       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  User            │ Receives comprehensive review
└──────────────────┘
```

### Tool Invocation Flow

```
Agent needs analysis
    ↓
Calls registered function
    ↓
Function executes tool
    ↓
Tool returns structured data
    ↓
Agent processes results
    ↓
Agent formulates response
    ↓
Response added to group chat
```

---

## Security Architecture

### Input Validation

```python
def validate_code_input(code: str) -> bool:
    """Validate user-submitted code before processing"""
    
    # Check length
    if len(code) > 10000:  # 10K chars max
        raise ValueError("Code too long")
    
    # Check for suspicious patterns
    suspicious = [
        '__import__',
        'exec(',
        'eval(',
        'compile(',
        'os.system',
        'subprocess'
    ]
    
    for pattern in suspicious:
        if pattern in code:
            raise SecurityError(f"Suspicious pattern detected: {pattern}")
    
    return True
```

### API Key Management

```python
# .env file (never committed)
OPENAI_API_KEY=sk-...

# Load securely
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OPENAI_API_KEY")
```

### Docker Security

```yaml
# docker-compose.yml
services:
  sandbox:
    image: code-review-sandbox
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
    networks:
      - none  # No network access
```

### Rate Limiting

```python
from functools import wraps
import time

def rate_limit(max_calls: int, period: int):
    """Rate limit decorator for API calls"""
    calls = []
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            # Remove old calls
            calls[:] = [c for c in calls if c > now - period]
            
            if len(calls) >= max_calls:
                raise RateLimitError(f"Max {max_calls} calls per {period}s")
            
            calls.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(max_calls=10, period=60)
def review_code(code: str):
    """Rate-limited review function"""
    pass
```

---

## Development Guide

### Setting Up Development Environment

```bash
# Clone and setup
git clone https://github.com/yourusername/code-review-crew.git
cd code-review-crew
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev tools

# Build Docker image
docker build -t code-review-sandbox:latest -f Dockerfile.sandbox .

# Run tests
pytest tests/ -v

# Start dev server with hot reload
streamlit run app.py --server.runOnSave=true
```

### Adding a New Agent

1. **Create agent file** in `code_review_crew/agents/`

```python
# code_review_crew/agents/documentation_reviewer.py
import autogen

class DocumentationReviewer:
    """Reviews code documentation and comments"""
    
    def create_agent(self, llm_config: dict) -> autogen.AssistantAgent:
        return autogen.AssistantAgent(
            name="DocumentationReviewer",
            system_message="""
            You are a Documentation Reviewer specializing in:
            - Docstring quality
            - Comment clarity
            - API documentation
            - README completeness
            
            Provide specific suggestions for improvement.
            """,
            llm_config=llm_config
        )
```

2. **Register in orchestrator**

```python
# code_review_crew/agents/orchestrator.py
from .documentation_reviewer import DocumentationReviewer

doc_reviewer = DocumentationReviewer().create_agent(llm_config)
agents.append(doc_reviewer)
```

### Adding a New Tool

1. **Create tool file** in `code_review_crew/tools/`

```python
# code_review_crew/tools/type_checker.py
import mypy.api

class TypeChecker:
    """Wrapper for mypy type checking"""
    
    def check_types(self, code: str) -> dict:
        """Run mypy type checking"""
        result = mypy.api.run(['/tmp/temp_code.py'])
        return self._parse_results(result)
```

2. **Register with agent**

```python
code_analyzer = autogen.AssistantAgent(
    name="CodeAnalyzer",
    function_map={
        "run_pylint": linting_tool.run_pylint,
        "check_types": type_checker.check_types  # New tool
    }
)
```

### Testing Strategies

```python
# Unit test for agent
def test_code_analyzer():
    agent = CodeAnalyzer()
    result = agent.analyze("def foo(): pass")
    assert 'issues' in result
    assert len(result['issues']) >= 0

# Integration test for group chat
@pytest.mark.asyncio
async def test_full_review():
    crew = CodeReviewCrew()
    result = await crew.review_code(sample_code)
    assert result['status'] == 'complete'
    assert len(result['issues']) > 0

# Test tool integration
def test_pylint_tool():
    tool = LintingTool()
    result = tool.run_pylint("print('hello')")
    assert 'score' in result
    assert result['score'] >= 0
```

### Code Style

```python
# Use type hints
def analyze_code(code: str, depth: str = "standard") -> Dict[str, Any]:
    pass

# Use docstrings
def complex_function(param: str) -> List[Dict]:
    """
    Brief description.
    
    Args:
        param: Description
    
    Returns:
        Description
    
    Raises:
        ValueError: When invalid
    """
    pass

# Use descriptive names
analyzed_results = analyze_code(user_code)  # Good
r = analyze(c)  # Bad
```

---

## Performance Optimization

### Caching Strategy

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def analyze_code_cached(code_hash: str) -> dict:
    """Cache analysis results by code hash"""
    return analyze_code(code)
```

### Parallel Agent Execution

```python
import asyncio

async def parallel_analysis(code: str) -> dict:
    """Run independent agents in parallel"""
    tasks = [
        code_analyzer.analyze_async(code),
        security_reviewer.scan_async(code),
        performance_optimizer.profile_async(code)
    ]
    
    results = await asyncio.gather(*tasks)
    return merge_results(results)
```

### Batch Processing

```python
def review_multiple_files(files: List[str]) -> List[Dict]:
    """Efficiently review multiple files"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(review_file, files)
    return list(results)
```

---

## Appendix

### AutoGen Best Practices

1. **Keep system messages focused** - One responsibility per agent
2. **Use function calling** - Augment agents with real tools
3. **Limit conversation rounds** - Prevent infinite loops
4. **Handle errors gracefully** - Agents can fail
5. **Test agent interactions** - Verify collaboration patterns

### Common Patterns

**Consensus Building**
```python
# Agents vote on priority
votes = {}
for agent in agents:
    priority = agent.get_priority(issue)
    votes[agent.name] = priority

consensus = max(votes.values(), key=votes.count)
```

**Iterative Refinement**
```python
# Agent improves based on feedback
for iteration in range(max_iterations):
    suggestion = agent.suggest_fix(code)
    feedback = reviewer.review_fix(suggestion)
    if feedback.approved:
        break
```

**Human-in-the-Loop**
```python
# Request human input at key points
if issue.severity == "critical":
    human_decision = await request_human_input(issue)
    if human_decision == "skip":
        continue
```

---

**End of Architecture Documentation**
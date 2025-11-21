# 🏗️ Code Review Crew - Architecture Documentation

**Version:** 1.0  
**Status:** Production Ready  
**Last Updated:** November 2024

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Multi-Agent Architecture](#multi-agent-architecture)
3. [Agent Design & Implementation](#agent-design--implementation)
4. [AutoGen Integration](#autogen-integration)
5. [Tool Integration Layer](#tool-integration-layer)
6. [Communication Patterns](#communication-patterns)
7. [Data Flow](#data-flow)
8. [Current Implementation Status](#current-implementation-status)
9. [Development Guide](#development-guide)

---

## System Overview

Code Review Crew is a **multi-agent AI system** built on Microsoft AutoGen that performs comprehensive code reviews through collaborative agent discussions.

### Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│              Presentation Layer                          │
│  ┌──────────────────┐    ┌──────────────────┐          │
│  │ Streamlit Web UI │    │ CLI Interface    │          │
│  └──────────────────┘    └──────────────────┘          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│           Agent Orchestration Layer                      │
│  ┌────────────────────────────────────────────┐         │
│  │        AutoGen Group Chat Manager          │         │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  │         │
│  │  │Agent1│  │Agent2│  │Agent3│  │Agent4│  │         │
│  │  └──────┘  └──────┘  └──────┘  └──────┘  │         │
│  └────────────────────────────────────────────┘         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│            Tool Integration Layer                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                │
│  │ Pylint  │  │ Bandit  │  │ Radon   │                │
│  └─────────┘  └─────────┘  └─────────┘                │
└─────────────────────────────────────────────────────────┘
```

### Core Components

1. **Web Interface** (`app.py`) - Streamlit-based user interface
2. **Group Chat Manager** (`run_group_chat.py`) - AutoGen orchestration
3. **Agent Classes** (`code_review_crew/agents/`) - Specialized reviewers
4. **Tool Wrappers** (`code_review_crew/tools/`) - Static analysis integration
5. **Utilities** (`code_review_crew/utils/`) - Helper functions

---

## Multi-Agent Architecture

### Agent Ecosystem

```
                    ┌─────────────────────────┐
                    │  Review Orchestrator    │
                    │  • Coordinates workflow │
                    │  • Synthesizes feedback │
                    │  • Assigns final grade  │
                    └───────────┬─────────────┘
                                │
                    ┌───────────┴─────────────┐
                    │   AutoGen GroupChat     │
                    │  • Message routing      │
                    │  • Turn management      │
                    │  • Speaker selection    │
                    └───────────┬─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐    ┌────────▼────────┐    ┌────────▼─────────┐
│ Code Analyzer  │    │ Security        │    │ Performance      │
│                │    │ Reviewer        │    │ Optimizer        │
│ GPT-4 Analysis │    │ GPT-4 Analysis  │    │ GPT-4 Analysis   │
│ + Pylint Ready │    │ + Bandit Ready  │    │ + Radon Ready    │
└────────────────┘    └─────────────────┘    └──────────────────┘
```

### Agent Roles

| Agent | Type | Primary Function | Tool Access |
|-------|------|------------------|-------------|
| **Review Orchestrator** | Coordinator | Manages workflow, synthesizes feedback | None |
| **Code Analyzer** | Analyst | Code quality, style, structure | Pylint, PEP8 checker |
| **Security Reviewer** | Security Expert | Vulnerabilities, exploits | Bandit scanner |
| **Performance Optimizer** | Performance Expert | Complexity, bottlenecks | Radon analyzer |
| **Test Generator** | Testing Expert | Unit test generation | Pytest (optional) |
| **Code Executor** | Executor | Safe code execution | Docker (optional) |

---

## Agent Design & Implementation

### Base Agent Pattern

All agents inherit from a base class providing consistent interface:

```python
# code_review_crew/agents/base_agent.py
from abc import ABC, abstractmethod
import autogen

class BaseAgent(ABC):
    """Abstract base class for all code review agents"""
    
    @abstractmethod
    def create_agent(self) -> autogen.AssistantAgent:
        """Create and return the AutoGen agent instance"""
        pass
    
    @abstractmethod
    def register_functions(self) -> Dict:
        """Register tool functions with the agent"""
        pass
    
    @abstractmethod
    def analyze(self, code: str) -> Dict:
        """Perform analysis on the provided code"""
        pass
```

### 1. Review Orchestrator

**File:** `code_review_crew/agents/orchestrator.py`

**Responsibilities:**
- Initiates review process
- Coordinates agent communication
- Resolves conflicts between agents
- Prioritizes issues by severity
- Generates final comprehensive report
- Assigns letter grade (A-F)

**System Prompt:**
```
You coordinate the code review process.

1. Start by asking CodeAnalyzer for analysis
2. Then SecurityReviewer for security assessment  
3. Then PerformanceOptimizer for performance review
4. Synthesize final report with grades (A-F)
5. List issues by priority: Critical, High, Medium, Low

Keep reviews constructive and actionable.
```

**Key Methods:**
- `initiate_review()` - Starts the process
- `collect_agent_feedback()` - Gathers responses
- `prioritize_issues()` - Categorizes by severity
- `synthesize_review()` - Creates final report
- `format_final_report()` - Formats for display

### 2. Code Analyzer

**File:** `code_review_crew/agents/code_analyzer.py`

**Analysis Focus:**
- PEP 8 style compliance
- Code smells (long methods, god objects, duplicates)
- Naming conventions
- Missing docstrings
- Error handling patterns
- Design principles (SOLID, DRY)

**Tool Integration:**
```python
{
    "run_pylint": linting_tool.run_pylint,
    "check_pep8": linting_tool.check_pep8,
    "detect_code_smells": self.detect_code_smells
}
```

**System Prompt:**
```
You analyze code quality.

Check for:
- PEP 8 style violations
- Code smells and anti-patterns
- Poor naming conventions
- Missing documentation
- Potential bugs

Provide specific line numbers and fix suggestions.
```

### 3. Security Reviewer

**File:** `code_review_crew/agents/security_reviewer.py`

**Security Checks:**
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting)
- Weak cryptography (MD5, SHA1)
- Hardcoded secrets (passwords, API keys)
- Command injection
- Insecure deserialization
- OWASP Top 10 compliance

**Tool Integration:**
```python
{
    "scan_security": security_scanner.run_bandit,
    "check_owasp": security_scanner.check_owasp_top10,
    "detect_injection": self.detect_injection_vulns
}
```

**System Prompt:**
```
You find security vulnerabilities.

Check for:
- SQL injection
- XSS vulnerabilities  
- Weak cryptography
- Hardcoded secrets
- Command injection

Mark ALL security issues as CRITICAL.
Explain the exploit and provide secure alternatives.
```

### 4. Performance Optimizer

**File:** `code_review_crew/agents/performance_optimizer.py`

**Performance Analysis:**
- Time complexity (Big O analysis)
- Space complexity
- Nested loops detection
- Inefficient algorithms
- Caching opportunities
- Memory usage patterns

**Tool Integration:**
```python
{
    "analyze_complexity": complexity_tool.calculate_complexity,
    "find_bottlenecks": complexity_tool.find_bottlenecks,
    "detect_inefficiencies": self.detect_inefficiencies
}
```

**System Prompt:**
```
You analyze performance.

Check for:
- Nested loops (O(n²) or worse)
- Inefficient string concatenation
- Missing caching opportunities
- Repeated calculations

Explain current complexity and suggest optimizations.
```

---

## AutoGen Integration

### Group Chat Configuration

```python
# run_group_chat.py
import autogen

class CodeReviewChat:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        self.llm_config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "api_key": self.api_key
        }
        
    def create_agents(self):
        """Create all AutoGen agent instances"""
        
        self.agents['orchestrator'] = autogen.AssistantAgent(
            name="ReviewOrchestrator",
            system_message="...",
            llm_config=self.llm_config
        )
        
        self.agents['code_analyzer'] = autogen.AssistantAgent(
            name="CodeAnalyzer",
            system_message="...",
            llm_config=self.llm_config
        )
        
        # ... other agents
        
    def setup_group_chat(self):
        """Setup AutoGen group chat"""
        
        agent_list = [
            self.agents['user'],
            self.agents['orchestrator'],
            self.agents['code_analyzer'],
            self.agents['security'],
            self.agents['performance']
        ]
        
        self.group_chat = autogen.GroupChat(
            agents=agent_list,
            messages=[],
            max_round=20,
            speaker_selection_method="auto"
        )
        
        self.chat_manager = autogen.GroupChatManager(
            groupchat=self.group_chat,
            llm_config=self.llm_config
        )
```

### Conversation Flow

```
1. User submits code
   ↓
2. UserProxyAgent sends initial message
   ↓
3. AutoGen selects ReviewOrchestrator
   ↓
4. Orchestrator requests CodeAnalyzer analysis
   ↓
5. CodeAnalyzer responds with findings
   ↓
6. Orchestrator requests SecurityReviewer assessment
   ↓
7. SecurityReviewer responds with vulnerabilities
   ↓
8. Orchestrator requests PerformanceOptimizer review
   ↓
9. PerformanceOptimizer responds with optimizations
   ↓
10. Orchestrator synthesizes final report
    ↓
11. Results returned to user
```

---

## Tool Integration Layer

### Architecture

```python
# Wrapper Pattern
code_review_crew/tools/
├── linting_tool.py         # Wraps Pylint
├── security_scanner.py     # Wraps Bandit
├── complexity_analyzer.py  # Wraps Radon
├── test_runner.py         # Wraps Pytest
└── git_tool.py            # Parses Git diffs
```

### Tool Wrapper Example

```python
# code_review_crew/tools/linting_tool.py
class LintingTool:
    """Wrapper for Pylint static analysis"""
    
    def run_pylint(self, code: str) -> Dict:
        """
        Run Pylint on code and return structured results
        
        Returns:
            {
                'score': float (0-10),
                'issues': [...],
                'summary': str
            }
        """
        # Write code to temp file
        temp_file = self._write_temp_file(code)
        
        # Run pylint
        result = subprocess.run(
            ['pylint', temp_file, '--output-format=json'],
            capture_output=True,
            text=True
        )
        
        # Parse and return results
        return self._parse_results(result)
```

### Current Tool Status

| Tool | Status | Integration | Usage |
|------|--------|-------------|-------|
| **Pylint** | ✅ Implemented | Ready | Can be called by agents |
| **Bandit** | ✅ Implemented | Ready | Can be called by agents |
| **Radon** | ✅ Implemented | Ready | Can be called by agents |
| **Pytest** | ✅ Implemented | Ready | Can run generated tests |
| **Docker** | ✅ Implemented | Optional | Sandbox code execution |

**Note:** Currently, agents primarily use GPT-4's native code analysis capabilities. Tools are available and can be explicitly invoked when needed for deterministic analysis.

---

## Communication Patterns

### Message Flow

```
┌──────────┐     1. Initial      ┌─────────────────┐
│   User   │────────────────────>│ GroupChat       │
└──────────┘                     │ Manager         │
                                 └────────┬────────┘
                                          │
                     2. Route to Orchestrator
                                          │
                                          ▼
                                 ┌────────────────┐
                                 │ Orchestrator   │
                                 └────────┬───────┘
                                          │
                  3. Request Agent Analysis
                                          │
          ┌───────────────────────────────┼───────────────┐
          │                               │               │
          ▼                               ▼               ▼
    ┌──────────┐                   ┌──────────┐    ┌──────────┐
    │  Code    │                   │ Security │    │Perform.  │
    │ Analyzer │                   │ Reviewer │    │Optimizer │
    └────┬─────┘                   └────┬─────┘    └────┬─────┘
         │                              │               │
         │      4. Return Analysis      │               │
         └──────────────┬───────────────┴───────────────┘
                        │
                        ▼
                ┌───────────────┐
                │ Orchestrator  │
                │ Synthesizes   │
                └───────┬───────┘
                        │
                        │ 5. Final Report
                        ▼
                ┌───────────────┐
                │     User      │
                └───────────────┘
```

### Example Conversation

```python
# Actual conversation from system
[User]: 
"Please review this code: def get_user(username): ..."

[ReviewOrchestrator]:
"CodeAnalyzer, can you please provide your analysis?"

[CodeAnalyzer]:
"Found SQL injection on line 4, weak crypto on line 17..."

[SecurityReviewer]:
"Confirming SQL injection - CRITICAL priority..."

[PerformanceOptimizer]:
"Detected O(n²) nested loop on line 12..."

[ReviewOrchestrator]:
"Final Grade: C-. Critical issues: 3. High: 1. Recommendations..."
```

---

## Data Flow

### Review Process Flow

```
1. User Input
   ├─> Code (string)
   ├─> Configuration (optional)
   └─> Context (optional)
      ↓
2. Initialization
   ├─> Create agent instances
   ├─> Initialize tools
   ├─> Setup group chat
   └─> Configure LLM
      ↓
3. Analysis Phase
   ├─> Orchestrator starts review
   ├─> Each agent analyzes code
   ├─> Agents discuss findings
   └─> Consensus building
      ↓
4. Synthesis Phase
   ├─> Collect all feedback
   ├─> Prioritize issues
   ├─> Resolve conflicts
   └─> Generate grade
      ↓
5. Output
   ├─> Structured report
   ├─> Conversation history
   ├─> Prioritized issues
   └─> Actionable recommendations
```

### Data Structures

```python
# Review Results
{
    'grade': 'C-',
    'summary': 'Review complete...',
    'issues': {
        'critical': [...],
        'high': [...],
        'medium': [...],
        'low': [...]
    },
    'conversation': [
        {'speaker': 'Agent1', 'content': '...'},
        ...
    ],
    'strengths': [...],
    'next_steps': [...]
}

# Issue Structure
{
    'description': 'SQL injection vulnerability',
    'line': 45,
    'severity': 'critical',
    'source': 'SecurityReviewer',
    'suggestion': 'Use parameterized queries',
    'code_example': '...'
}
```

---

## Current Implementation Status

### ✅ Completed Features

| Feature | Status | Notes |
|---------|--------|-------|
| **Multi-Agent System** | ✅ Complete | 4 agents working collaboratively |
| **AutoGen Integration** | ✅ Complete | Group chat fully functional |
| **Streamlit UI** | ✅ Complete | Web interface operational |
| **Agent Collaboration** | ✅ Complete | Natural dialogue between agents |
| **Issue Prioritization** | ✅ Complete | Critical/High/Medium/Low categorization |
| **Grade Assignment** | ✅ Complete | A-F grading scale |
| **Tool Wrappers** | ✅ Complete | Pylint, Bandit, Radon implemented |
| **Code Parser** | ✅ Complete | AST-based Python parsing |
| **Report Generator** | ✅ Complete | Multiple format support |
| **Sandbox Manager** | ✅ Complete | Docker integration ready |

### 🔧 Tool Usage

**Current State:**  
Agents use GPT-4's native code analysis which provides excellent results. Tool wrappers (Pylint, Bandit, Radon) are implemented and ready but not actively called in the default flow.

**Why This Works:**  
GPT-4 has been trained on vast amounts of code and can identify:
- SQL injection patterns
- Security vulnerabilities  
- Performance issues
- Code quality problems
- Best practice violations

**When Tools Would Be Used:**
- Deterministic scoring needed (e.g., exact Pylint score)
- Compliance reporting required
- Batch processing of many files
- Integration with CI/CD pipelines

### 📈 Performance Metrics

- **Average Review Time:** 30-60 seconds
- **Agent Messages:** 5-10 per review
- **API Calls:** 5-20 depending on max_rounds
- **Accuracy:** High (GPT-4 powered analysis)
- **Token Usage:** ~5,000-10,000 tokens per review

---

## Development Guide

### Adding a New Agent

```python
# 1. Create agent file in code_review_crew/agents/
class MyCustomAgent(BaseAgent):
    def __init__(self, llm_config, tools):
        self.llm_config = llm_config
        self.tools = tools
        
        self.agent = autogen.AssistantAgent(
            name="MyCustomAgent",
            system_message="Your system prompt here",
            llm_config=llm_config
        )
    
    def create_agent(self):
        return self.agent
    
    def register_functions(self):
        return {"my_tool": self.tools['my_tool'].run}
    
    def analyze(self, code):
        return {"findings": [...]}

# 2. Add to run_group_chat.py
self.agents['my_custom'] = autogen.AssistantAgent(
    name="MyCustomAgent",
    system_message="...",
    llm_config=self.llm_config
)

# 3. Include in agent_list
agent_list = [
    ...,
    self.agents['my_custom']
]
```

### Adding a New Tool

```python
# 1. Create tool file in code_review_crew/tools/
class MyTool:
    def analyze(self, code: str) -> Dict:
        """Run your analysis"""
        # Implementation
        return {"results": [...]}

# 2. Initialize in run_group_chat.py
self.my_tool = MyTool()

# 3. Register with agent
self.tool_functions['my_tool_func'] = self.my_tool.analyze

# 4. Add to agent's function map
self.agents['my_agent'].register_function(
    function_map={"my_tool_func": self.tool_functions['my_tool_func']}
)
```

### Testing

```bash
# Run standalone test
python run_group_chat_standalone.py

# Run with tools
python run_group_chat.py

# Run web interface
streamlit run app.py

# Test specific module
python -m pytest tests/test_agents.py -v
```

---

## Best Practices

### Agent Design
1. Keep system prompts focused on one responsibility
2. Provide clear examples in prompts
3. Specify output format expectations
4. Include severity classifications

### Tool Integration
1. Always handle timeouts and errors
2. Validate tool installation
3. Provide fallback mechanisms
4. Cache results when appropriate

### Performance
1. Limit max_rounds to prevent runaway conversations
2. Use temperature wisely (0.7 good default)
3. Consider token costs for large codebases
4. Implement rate limiting for production

### Security
1. Never execute untrusted code directly
2. Use Docker for isolation
3. Sanitize all inputs
4. Store API keys in environment variables
5. Log all reviews for audit

---

## Future Enhancements

### Planned Features
- [ ] Streaming responses for real-time feedback
- [ ] Multi-language support (JavaScript, Java, Go)
- [ ] GitHub PR integration
- [ ] VS Code extension
- [ ] Batch file processing
- [ ] Custom rule configuration
- [ ] Historical analytics

### Potential Improvements
- [ ] Explicit tool calling in agent prompts
- [ ] Upgrade to AutoGen 0.4+ for better function calling
- [ ] Parallel agent execution
- [ ] Caching of repeated analyses
- [ ] User feedback integration
- [ ] Fine-tuned models for specific domains

---

## Appendix

### Key Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `app.py` | Streamlit web interface | ~300 |
| `run_group_chat.py` | AutoGen integration | ~200 |
| `orchestrator.py` | Review coordinator | ~400 |
| `code_analyzer.py` | Code quality agent | ~300 |
| `security_reviewer.py` | Security agent | ~300 |
| `performance_optimizer.py` | Performance agent | ~350 |
| `linting_tool.py` | Pylint wrapper | ~250 |
| `security_scanner.py` | Bandit wrapper | ~300 |
| `complexity_analyzer.py` | Radon wrapper | ~350 |

### Dependencies

```
Core:
- pyautogen==0.2.32
- openai>=1.0.0
- streamlit>=1.28.0

Tools:
- pylint>=3.0.0
- bandit>=1.7.5
- radon>=6.0.1
- pytest>=7.4.0

Utilities:
- python-dotenv>=1.0.0
- docker>=7.0.0 (optional)
```

---

**End of Architecture Documentation**

*Last Updated: November 2024*  
*Version: 1.0*  
*Status: Production Ready*
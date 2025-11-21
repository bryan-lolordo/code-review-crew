# Architecture Documentation

> **Detailed technical architecture of the Code Review Crew system**

## 📐 System Overview

Code Review Crew is a **two-stage AI pipeline** that combines multi-agent collaboration (AutoGen) with iterative workflow automation (LangGraph) to provide intelligent code review and autonomous fixing.

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│                  (Streamlit Web App)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                UNIFIED ANALYZER                             │
│           (Orchestrates Both Stages)                        │
└──────────┬─────────────────────────┬────────────────────────┘
           │                         │
           ▼                         ▼
    ┌─────────────┐          ┌──────────────┐
    │   STAGE 1   │          │   STAGE 2    │
    │   AutoGen   │──────────▶│  LangGraph   │
    │   Review    │  Issues  │   Fixer      │
    └─────────────┘          └──────────────┘
           │                         │
           ▼                         ▼
    Review Report              Fixed Code
```

---

## 🎯 Stage 1: AutoGen Multi-Agent Review

### Architecture Pattern: **Agent Collaboration**

AutoGen uses a **Group Chat** pattern where specialized agents communicate to produce a comprehensive code review.

### Agent Hierarchy

```
┌────────────────────────────────────────────────┐
│         ReviewOrchestrator (Manager)           │
│   "Controls workflow, synthesizes feedback"    │
└────────────────┬───────────────────────────────┘
                 │
        ┌────────┴────────┐
        │  Coordinates:   │
        └────────┬────────┘
                 │
     ┌───────────┼───────────┬───────────┬──────────┐
     │           │           │           │          │
     ▼           ▼           ▼           ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│  Code   │ │Security │ │Perform. │ │  Test   │ │  Code   │
│Analyzer │ │Reviewer │ │Optimizer│ │Generator│ │Executor │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
     │           │           │           │          │
     └───────────┴───────────┴───────────┴──────────┘
                         │
                         ▼
                 ┌──────────────┐
                 │ Final Report │
                 └──────────────┘
```

### Agent Responsibilities

#### 1. ReviewOrchestrator
**Role**: Workflow coordinator and synthesizer

```python
System Message:
- Call agents in sequence: CodeAnalyzer → SecurityReviewer → 
  PerformanceOptimizer → TestGenerator
- Synthesize feedback into graded report
- Prioritize issues by severity
```

**Output**: Structured report with grades (A-F), prioritized issues, action items

#### 2. CodeAnalyzer
**Role**: Code quality and style expert

**Analyzes**:
- Code smells and anti-patterns
- PEP 8 compliance
- DRY violations
- SOLID principles
- Error handling

**Tools**:
- Pylint static analysis
- Custom pattern detection
- Complexity metrics

#### 3. SecurityReviewer
**Role**: Security vulnerability detection

**Checks for**:
- SQL injection
- XSS vulnerabilities
- Weak cryptography
- Hardcoded secrets
- OWASP Top 10

**Tools**:
- Bandit security scanner
- Custom regex patterns
- CWE mapping

#### 4. PerformanceOptimizer
**Role**: Performance analysis and optimization

**Identifies**:
- Algorithmic complexity (Big O)
- Performance bottlenecks
- Memory leaks
- Caching opportunities
- Nested loops

**Tools**:
- Radon complexity analysis
- Custom complexity detection

#### 5. TestGenerator
**Role**: Test case recommendations

**Suggests**:
- Unit tests for each function
- Edge cases
- Error handling tests
- Security test cases
- Priority rankings

#### 6. CodeExecutor (Optional)
**Role**: Safe code execution

**Features**:
- Docker sandbox execution
- Resource limits (CPU, memory, time)
- Test validation
- Runtime verification

---

## 🔧 Stage 2: LangGraph Iterative Fixing

### Architecture Pattern: **State Machine Workflow**

LangGraph implements a **cyclic state machine** that iteratively fixes issues with testing after each change.

### Workflow State Machine

```
                    ┌──────────┐
                    │  START   │
                    └────┬─────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ Fix Issue   │◄────────┐
                  │   Node      │         │
                  └──────┬──────┘         │
                         │                │
                         ▼                │
                  ┌─────────────┐         │
                  │ Test Code   │         │
                  │   Node      │         │
                  └──────┬──────┘         │
                         │                │
                         ▼                │
                  ┌─────────────┐         │
                  │   Route     │         │
                  │  Decision   │         │
                  └──────┬──────┘         │
                         │                │
              ┌──────────┼──────────┐     │
              │          │          │     │
         continue       done      failed  │
              │          │          │     │
              └──────────┘          │     │
                    │                │
                    └────────────────┴─────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  Finalize   │
                  │    Node     │
                  └──────┬──────┘
                         │
                         ▼
                    ┌──────────┐
                    │   END    │
                    └──────────┘
```

### State Definition

```python
class CodeFixState(TypedDict):
    # Code
    original_code: str          # Immutable starting point
    current_code: str           # Updated each iteration
    
    # Issues
    issues: List[Dict]          # Queue (shrinks)
    fixed_issues: List[Dict]    # History (grows)
    
    # Testing
    test_results: Dict          # Latest test results
    
    # Control
    iteration: int              # Current iteration
    max_iterations: int         # Stop condition
    status: Literal["fixing", "testing", "done", "failed"]
```

### Node Functions

#### 1. fix_issue_node
**Purpose**: Apply fix to next highest-priority issue

**Process**:
1. Pop first issue from queue (sorted by severity)
2. Call `_generate_fix()` with hybrid strategy:
   - Try pattern-based fix (fast)
   - Fall back to LLM (smart)
3. Update `current_code`
4. Move issue to `fixed_issues`
5. Increment `iteration`

**Output**: Updated state with fixed code

#### 2. test_code_node
**Purpose**: Validate the fix

**Tests**:
1. **Syntax validation**: Compile code
2. **Safety checks**: No eval/exec/dangerous patterns
3. **Future**: Could run pylint, pytest, etc.

**Output**: Test results in state

#### 3. route_after_test
**Purpose**: Decide next step

**Logic**:
```python
if iteration >= max_iterations:
    return "failed"  # Hit limit
elif len(issues) == 0:
    return "done"    # All fixed
else:
    return "continue"  # Keep fixing
```

#### 4. finalize_node
**Purpose**: Print summary, return final state

---

## 🔀 Hybrid Fixing Strategy

### Pattern-Based Fixes (Fast Lane)

**When**: Issue description matches known patterns

**Examples**:
```python
# SQL Injection
if 'sql' in description and 'injection' in description:
    return _fix_sql_injection(code)

# Weak Crypto
if 'md5' in description:
    return _fix_weak_crypto(code)

# Hardcoded Secrets
if 'hardcoded' in description and 'secret' in description:
    return _fix_hardcoded_secrets(code)
```

**Advantages**:
- ⚡ Instant (no API calls)
- 💰 Free
- 🎯 100% deterministic
- ✅ Reliable for known issues

**Disadvantages**:
- 🔒 Limited to pre-defined patterns
- 🤖 Brittle (exact string matching)
- ❌ Can't handle novel issues

### LLM-Based Fixes (Smart Lane)

**When**: No pattern matches or pattern fix fails

**Process**:
```python
prompt = f"""Fix this issue: {issue['description']}

Code:
{code}

Return ONLY fixed Python code, no explanations.
"""

response = llm.invoke(prompt)
fixed_code = response.content
```

**Advantages**:
- 🧠 Understands context and nuance
- 🔄 Learns from error feedback
- 🆕 Handles novel/complex issues
- 🎨 Creative solutions

**Disadvantages**:
- 🐌 Slower (2-5s per fix)
- 💸 Costs money ($0.01-0.03 per fix)
- 🎲 Non-deterministic
- ⚠️ Can hallucinate

### Decision Tree

```
Issue comes in
    │
    ▼
Try pattern match
    │
    ├─ Match found? ─→ Apply pattern fix ─→ Test
    │                        │
    │                        ▼
    │                   Fix worked? ─→ Done
    │                        │
    │                        ▼ (No)
    │                   Fall to LLM
    │
    └─ No match ────────────→ Use LLM fix ─→ Test
                                  │
                                  ▼
                             Fix worked? ─→ Done
                                  │
                                  ▼ (No)
                             Add TODO comment
```

---

## 🔌 Tool Integration

### Linting Tools

```python
class LintingTool:
    def run_pylint(code: str) -> Dict:
        # Static analysis with Pylint
        # Returns: score, issues, statistics
        
    def check_pep8(code: str) -> List[Dict]:
        # PEP 8 compliance with pycodestyle
        # Returns: violations with line numbers
```

### Complexity Analysis

```python
class ComplexityAnalyzer:
    def calculate_complexity(code: str) -> Dict:
        # Radon cyclomatic complexity
        # Returns: per-function complexity, averages
        
    def find_bottlenecks(code: str) -> List[Dict]:
        # Identify performance issues
        # Returns: nested loops, O(n²) patterns
```

### Security Scanning

```python
class SecurityScanner:
    def run_bandit(code: str) -> Dict:
        # Bandit security scanner
        # Returns: vulnerabilities with severity
        
    def check_owasp_top10(code: str) -> Dict:
        # Map findings to OWASP categories
        # Returns: categorized vulnerabilities
```

---

## 📊 Data Flow

### Full Pipeline Data Flow

```
User Code
    │
    ▼
┌────────────────────────────────────────┐
│ STAGE 1: AutoGen Review                │
├────────────────────────────────────────┤
│                                        │
│ Code → Agent 1 ─┐                     │
│     → Agent 2 ─┼→ Group Chat → Report │
│     → Agent 3 ─┘                     │
│                                        │
└───────────────────┬────────────────────┘
                    │
                    ▼
            Conversation Text
                    │
                    ▼
┌────────────────────────────────────────┐
│ Issue Extraction (Regex Parsing)      │
├────────────────────────────────────────┤
│                                        │
│ Parse agent messages                   │
│ → Find "Severity:", "Description:"    │
│ → Extract line numbers                 │
│ → Build structured issue list          │
│                                        │
└───────────────────┬────────────────────┘
                    │
                    ▼
        List[Dict] (Structured Issues)
                    │
                    ▼
┌────────────────────────────────────────┐
│ STAGE 2: LangGraph Fixing             │
├────────────────────────────────────────┤
│                                        │
│ For each issue:                        │
│   1. Try pattern fix                   │
│   2. Fallback to LLM                   │
│   3. Test fixed code                   │
│   4. Continue or finish                │
│                                        │
└───────────────────┬────────────────────┘
                    │
                    ▼
                Fixed Code
```

### Issue Extraction Detail

```python
# Input: Agent conversation
conversation = [
    {
        "speaker": "SecurityReviewer",
        "content": """
        - Issue type: SQL Injection
        - Line number: 4
        - Description: User input directly in query
        - Severity: CRITICAL
        """
    }
]

# Regex patterns match:
# "- Severity: CRITICAL" → severity = "Critical"
# "- Line number: 4" → line = 4
# "- Description: ..." → description = "..."

# Output: Structured issue
issue = {
    "severity": "Critical",
    "description": "User input directly in query",
    "line": 4,
    "agent": "SecurityReviewer"
}
```

---

## 🎨 UI Architecture (Streamlit)

### Component Hierarchy

```
app.py (Main App)
    │
    ├─ Sidebar
    │   ├─ Analysis Mode Selector
    │   ├─ Max Iterations Slider
    │   └─ API Key Status
    │
    ├─ Tab 1: Code Input
    │   ├─ Text Area / Example Selector
    │   └─ Submit Button
    │
    ├─ Tab 2: Results
    │   ├─ Metrics (Issues Found/Fixed/Iterations)
    │   └─ Code Comparison (Original vs. Fixed)
    │
    ├─ Tab 3: Process Logs
    │   ├─ Summary Section
    │   ├─ Step 1: AutoGen Review (collapsible)
    │   ├─ Step 2: Issue Extraction (expanded)
    │   └─ Step 3: LangGraph Fixing (per-iteration expandable)
    │
    ├─ Tab 4: Agent Conversation
    │   └─ Formatted agent messages with color coding
    │
    └─ Tab 5: Examples & Documentation
```

### Log Capture System

```python
# log_capture.py
class LogCapture:
    def start(self):
        # Redirect stdout to StringIO buffer
        
    def stop(self):
        # Restore stdout, return captured logs
        
    def get_logs(self):
        # Get logs without stopping capture
```

**Usage**:
```python
capturer = LogCapture()
capturer.start()

# All print() statements captured
print("This is captured")

logs = capturer.stop()
# logs contains all printed output
```

---

## 🔒 Security Considerations

### Docker Sandboxing
```python
# CodeExecutor uses Docker for safe execution
docker run --rm \
  -v /code.py:/code.py \
  --memory 256m \
  --cpus 0.5 \
  --network none \
  python:3.9-slim python /code.py
```

### API Key Protection
- Keys stored in `.env` file (not in git)
- Never logged or displayed in UI
- Validated before use

### Code Execution Safety
- No `eval()` or `exec()` in main code
- All user code runs in isolated Docker
- Timeout limits (30s max)
- Resource limits enforced

---

## 📈 Scalability & Performance

### Current Limitations
- **Sequential Processing**: Agents run one at a time
- **Single Thread**: LangGraph fixes issues sequentially
- **Memory**: Full conversation history in memory

### Optimization Opportunities

#### 1. Parallel Agent Execution
```python
# Future: Run agents in parallel
async def parallel_review(code):
    results = await asyncio.gather(
        code_analyzer.analyze(code),
        security_reviewer.analyze(code),
        performance_optimizer.analyze(code)
    )
```

#### 2. Batch Fixing
```python
# Fix multiple independent issues in parallel
async def batch_fix(issues):
    fixes = await asyncio.gather(*[
        fix_issue(issue) for issue in issues
        if not has_dependencies(issue)
    ])
```

#### 3. Caching
```python
# Cache pattern-based fixes
@lru_cache(maxsize=1000)
def pattern_fix(issue_type, code_hash):
    # Return cached fix if available
```

---

## 🧪 Testing Strategy

### Unit Tests
- Individual agent functionality
- Pattern-based fix functions
- Issue extraction logic
- State transitions

### Integration Tests
- AutoGen group chat workflow
- LangGraph state machine
- End-to-end fix pipeline

### E2E Tests
- Full review + fix on example code
- UI interaction tests
- Log capture validation

---

## 🔮 Future Architecture Enhancements

### 1. Plugin System
```python
# Allow custom agents and patterns
class CustomAgent(BaseAgent):
    def analyze(self, code):
        # Custom analysis logic
        
# Register plugin
registry.register_agent(CustomAgent)
```

### 2. Multi-Language Support
```python
# Language-specific analyzers
analyzers = {
    'python': PythonAnalyzer(),
    'javascript': JavaScriptAnalyzer(),
    'java': JavaAnalyzer()
}
```

### 3. Incremental Analysis
```python
# Only analyze changed code
def incremental_review(old_code, new_code):
    diff = git_diff(old_code, new_code)
    return review_changes(diff)
```

### 4. Real-time Collaboration
```python
# WebSocket for live updates
async def stream_review(code):
    async for agent_message in review_stream(code):
        yield agent_message
```

---

## 📚 Additional Resources

- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Streamlit Documentation](https://docs.streamlit.io/)

---

**For implementation details, see the codebase and inline documentation.**
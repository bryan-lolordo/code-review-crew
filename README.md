# 🔍 Code Review Crew - Multi-Agent Code Analysis System

**[📺 Demo Coming Soon](#)**

An intelligent multi-agent system powered by **Microsoft AutoGen** that performs comprehensive code reviews through collaborative AI agents. The system orchestrates specialized agents that debate, analyze, and provide actionable feedback on code quality, security, performance, and testing.

## 🎯 What is Code Review Crew?

Code Review Crew is an **autonomous multi-agent system** that replaces traditional code review processes with AI-powered analysis. Multiple specialized agents collaborate in real-time discussions to provide comprehensive, expert-level code feedback.

**Key Technologies:**
- 🤖 Microsoft AutoGen for multi-agent orchestration
- 🧠 OpenAI GPT-4 for code analysis
- 🛡️ Static analysis tools (Pylint, Bandit, Radon)
- 🎨 Streamlit for web interface
- 🐳 Docker for safe code execution

## 💡 Why This Project?

This project demonstrates **advanced multi-agent AI patterns**:

✅ **Multi-Agent Collaboration** - Agents debate and reach consensus  
✅ **Code Execution** - Safe sandboxed code running and testing  
✅ **Real Tool Integration** - Actual linting and security scanners  
✅ **Group Chat Orchestration** - Complex agent interaction patterns  
✅ **Production-Ready Architecture** - Modular, testable, documented  

---

## 🏗️ Multi-Agent Architecture

### Agent Team

```
                    ┌─────────────────────┐
                    │   User Submits Code │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Review Orchestrator │
                    │   (Manages Flow)     │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐   ┌────────▼────────┐   ┌────────▼─────────┐
│ Code Analyzer  │   │ Security        │   │ Performance      │
│ - Code smells  │   │ Reviewer        │   │ Optimizer        │
│ - Bugs         │   │ - Vulnerabilities│   │ - Complexity     │
│ - Style issues │   │ - Best practices │   │ - Bottlenecks    │
└───────┬────────┘   └────────┬────────┘   └────────┬─────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Test Generator     │
                    │  - Unit tests       │
                    │  - Edge cases       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Code Executor      │
                    │  - Runs tests       │
                    │  - Validates fixes  │
                    └─────────────────────┘
```

### Agent Roles

**Review Orchestrator**
- Manages the review workflow
- Synthesizes feedback from all agents
- Prioritizes issues by severity
- Generates final review report

**Code Analyzer**
- Identifies code smells and anti-patterns
- Checks code style and conventions
- Detects potential bugs
- Suggests refactoring opportunities

**Security Reviewer**
- Scans for security vulnerabilities
- Checks for common exploits (SQL injection, XSS, etc.)
- Reviews authentication and authorization
- Validates input sanitization

**Performance Optimizer**
- Analyzes algorithmic complexity
- Identifies performance bottlenecks
- Suggests optimization strategies
- Reviews memory usage patterns

**Test Generator**
- Creates comprehensive unit tests
- Generates edge case scenarios
- Provides test coverage analysis
- Suggests integration tests

**Code Executor**
- Safely runs code in Docker sandbox
- Executes generated tests
- Validates proposed fixes
- Reports runtime errors

---

## ✨ Key Features

### 🤖 Multi-Agent Collaboration

**Group Chat Debates**
```python
# Agents engage in iterative discussions
Code Analyzer: "This function has O(n²) complexity..."
Performance Optimizer: "Agreed. I suggest using a hash map..."
Security Reviewer: "But first, we need to sanitize the input..."
Orchestrator: "Let's prioritize security, then optimize..."
```

**Consensus Building**
- Agents can agree, disagree, or build on each other's findings
- Natural conversation flow mimics human code reviews
- Emergent insights from agent interactions

### 🛡️ Comprehensive Analysis

**Multi-Dimensional Review**
- **Code Quality:** Style, readability, maintainability
- **Security:** Vulnerabilities, exploits, best practices
- **Performance:** Complexity, bottlenecks, optimization
- **Testing:** Coverage, edge cases, test quality
- **Documentation:** Comments, docstrings, clarity

**Real Tool Integration**
```python
# Actual static analysis tools
pylint_score = run_pylint(code)
security_issues = run_bandit(code)
complexity = calculate_complexity(code)
test_coverage = run_pytest_coverage(code)
```

### 🐳 Safe Code Execution

**Docker Sandbox**
- Isolated execution environment
- No access to host system
- Resource limits (CPU, memory, time)
- Automatic cleanup after execution

**Test Validation**
```python
# Generated tests are actually executed
test_results = executor.run_tests(generated_tests)
if test_results.passed:
    print("✅ All tests pass!")
```

### 📊 Actionable Reports

**Structured Feedback**
```markdown
## Code Review Summary

### 🔴 Critical Issues (2)
1. SQL Injection vulnerability in line 45
2. Unhandled exception in line 78

### 🟡 Warnings (5)
1. Function complexity too high (12/10)
2. Missing input validation
...

### 💡 Suggestions (8)
1. Consider using list comprehension
2. Extract method for better readability
...

### ✅ Strengths
- Well-documented functions
- Good error handling in most cases
```

---

## 🛠️ Installation & Setup

### Prerequisites
```bash
Python 3.9+
OpenAI API key
Docker (for code execution)
```

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/code-review-crew.git
cd code-review-crew
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API key:
# OPENAI_API_KEY=your_key_here
```

5. **Run the application**
```bash
streamlit run app.py
```

Navigate to `http://localhost:8501`

---

## 💻 Usage

### Web Interface (Recommended)

1. **Paste or Upload Code**
   - Copy-paste code directly
   - Upload Python files
   - Load from examples

2. **Configure Review**
   - Select analysis depth (quick/standard/deep)
   - Choose which agents to include
   - Enable/disable code execution

3. **Start Review**
   - Watch agents collaborate in real-time
   - See the group chat conversation
   - Get final consolidated report

4. **Apply Fixes**
   - Review suggested changes
   - See before/after comparisons
   - Download improved code

### CLI Interface

```bash
# Review a single file
python -m code_review_crew.cli review mycode.py

# Review with specific agents
python -m code_review_crew.cli review mycode.py --agents security performance

# Generate tests only
python -m code_review_crew.cli generate-tests mycode.py

# Batch review multiple files
python -m code_review_crew.cli review-batch src/
```

---

## 📁 Project Structure

```
code-review-crew/
├── README.md
├── ARCHITECTURE.md
├── requirements.txt
├── .env
├── .gitignore
│
├── code_review_crew/                # Main package
│   ├── __init__.py
│   ├── agents/                      # Agent definitions
│   │   ├── __init__.py
│   │   ├── code_analyzer.py
│   │   ├── security_reviewer.py
│   │   ├── performance_optimizer.py
│   │   ├── test_generator.py
│   │   ├── code_executor.py
│   │   └── orchestrator.py
│   │
│   ├── tools/                       # Analysis tools
│   │   ├── __init__.py
│   │   ├── linting_tool.py         # Pylint integration
│   │   ├── security_scanner.py     # Bandit integration
│   │   ├── complexity_analyzer.py  # Radon integration
│   │   └── test_runner.py          # Pytest integration
│   │
│   ├── utils/                       # Helper utilities
│   │   ├── __init__.py
│   │   ├── code_parser.py
│   │   ├── report_generator.py
│   │   └── sandbox_manager.py
│   │
│   └── config.py                    # Configuration
│
├── app.py                           # Streamlit web interface
│
├── examples/                        # Example code for testing
│   ├── simple_function.py
│   ├── security_issues.py
│   ├── performance_issues.py
│   └── complex_class.py
│
└── tests/                           # Unit tests
    ├── __init__.py
    ├── test_agents.py
    ├── test_tools.py
    └── test_integration.py
```

---

## 🎯 AutoGen Patterns Demonstrated

### 1. **Group Chat Orchestration**
Multiple agents engage in free-form conversation to solve complex problems.

### 2. **Code Execution Agents**
Safe execution of untrusted code with UserProxyAgent and Docker.

### 3. **Tool-Augmented Agents**
Agents enhanced with real static analysis tools for concrete results.

### 4. **Iterative Refinement**
Agents can critique each other's suggestions and iterate to better solutions.

### 5. **Human-in-the-Loop**
Optional human intervention at key decision points.

### 6. **Consensus Building**
Agents negotiate and agree on prioritization of issues.

---

## 🔬 Advanced Features

### Real-Time Agent Visualization

Watch agents collaborate:
```
[Code Analyzer] 🔍 Analyzing code structure...
[Security Reviewer] 🛡️ Found potential SQL injection on line 45
[Performance Optimizer] ⚡ This loop is O(n²), suggesting optimization...
[Code Analyzer] 💬 Agreed with security concern, should be top priority
[Orchestrator] 📋 Prioritizing issues: Security (Critical) > Performance (High)
```

### Custom Agent Configuration

```python
# Create custom agent teams
quick_review = [code_analyzer, orchestrator]
security_focused = [security_reviewer, code_analyzer, orchestrator]
full_review = [code_analyzer, security_reviewer, 
               performance_optimizer, test_generator, orchestrator]
```

### Learning from Feedback

```python
# Agents improve based on user feedback
if user_accepted_suggestion:
    agent.learn_from_success(suggestion)
else:
    agent.learn_from_failure(suggestion, user_feedback)
```

---

## 📊 Example Review Output

```markdown
# Code Review: user_authentication.py

## Summary
Reviewed 150 lines of Python code
Review time: 2m 34s
Overall Grade: C+ (Needs Improvement)

## Critical Issues 🔴

### 1. SQL Injection Vulnerability (Line 45)
**Severity:** Critical  
**Agent:** Security Reviewer  
**Description:** User input directly concatenated into SQL query

```python
# ❌ Current (Vulnerable)
query = f"SELECT * FROM users WHERE username = '{username}'"

# ✅ Suggested Fix
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (username,))
```

**Impact:** Attackers could execute arbitrary SQL commands
**Fix Effort:** Low (5 minutes)

### 2. Unhandled Exception (Line 78)
**Severity:** High  
**Agent:** Code Analyzer  
...

## Performance Issues 🟡

### 1. Inefficient Algorithm (Line 112)
**Current Complexity:** O(n²)  
**Suggested Complexity:** O(n)  
...

## Generated Tests ✅

```python
def test_valid_login():
    assert authenticate("user", "pass123") == True

def test_sql_injection_attempt():
    malicious = "' OR '1'='1"
    assert authenticate(malicious, "any") == False
    
def test_empty_credentials():
    assert authenticate("", "") == False
```

## Recommendations

1. **Immediate:** Fix SQL injection (Critical)
2. **Short-term:** Add input validation
3. **Long-term:** Implement rate limiting
```

---

## 🔐 Security Considerations

1. **Code Execution Safety**: All code runs in isolated Docker containers
2. **API Key Management**: Environment variables, never committed
3. **Input Sanitization**: All user code sanitized before analysis
4. **Resource Limits**: CPU, memory, and time limits on execution
5. **Audit Logging**: All reviews logged for security auditing

---

## 🚧 Roadmap

**Planned Features:**
- Support for multiple languages (JavaScript, Java, Go)
- GitHub PR integration for automated reviews
- VS Code extension
- Custom rule configuration
- Team collaboration features
- Historical review analytics
- AI-powered fix generation

---

## 📚 Documentation

For detailed technical architecture, see [ARCHITECTURE.md](ARCHITECTURE.md)

Topics covered:
- Multi-agent system design
- AutoGen group chat patterns
- Tool integration architecture
- Code execution sandboxing
- Agent communication protocols

---

## 🙏 Acknowledgments

**AI Frameworks**
- [Microsoft AutoGen](https://github.com/microsoft/autogen) - Multi-agent orchestration
- [OpenAI API](https://openai.com/) - Language models

**Analysis Tools**
- [Pylint](https://pylint.org/) - Code linting
- [Bandit](https://bandit.readthedocs.io/) - Security scanning
- [Radon](https://radon.readthedocs.io/) - Complexity analysis
- [Pytest](https://pytest.org/) - Testing framework

---

## 📄 License

MIT License

---

## 👤 Author

**Bryan LoLordo**
- Specialization: Multi-Agent AI Systems, Code Analysis
- Focus: Production-ready AI agents with Microsoft AutoGen

---

**Built with ❤️ using Multi-Agent AI patterns**

*Demonstrating advanced agent collaboration for code review automation* 🎯
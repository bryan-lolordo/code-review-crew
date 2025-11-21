# 🔍 Code Review Crew - Multi-Agent Code Analysis System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![AutoGen](https://img.shields.io/badge/AutoGen-0.2.32-green.svg)](https://github.com/microsoft/autogen)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent multi-agent system powered by **Microsoft AutoGen** that performs comprehensive code reviews through collaborative AI agents. Multiple specialized agents work together, discussing and debating code quality, security vulnerabilities, and performance optimizations to provide expert-level feedback.

## 🎯 What is Code Review Crew?

Code Review Crew is an **autonomous multi-agent system** where AI agents collaborate in real-time discussions to analyze code from multiple perspectives. Think of it as having a team of expert developers reviewing your code simultaneously.

**Core Technologies:**
- 🤖 **Microsoft AutoGen** - Multi-agent orchestration and group chat
- 🧠 **OpenAI GPT-4** - Advanced code analysis capabilities
- 🛠️ **Static Analysis Tools** - Pylint, Bandit, Radon integration
- 🎨 **Streamlit** - Interactive web interface
- 🐳 **Docker** - Safe code execution (optional)

## 💡 Why This Project?

This project demonstrates **production-ready multi-agent AI patterns**:

✅ **Multi-Agent Collaboration** - Agents discuss and reach consensus through natural dialogue  
✅ **Group Chat Orchestration** - Complex agent interaction patterns using AutoGen  
✅ **Tool Integration Architecture** - Extensible design for static analysis tools  
✅ **Comprehensive Analysis** - Security, performance, quality, and testing coverage  
✅ **Real-World Application** - Solves actual code review challenges  

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
                    │   (Coordinates Team) │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐   ┌────────▼────────┐   ┌────────▼─────────┐
│ Code Analyzer  │   │ Security        │   │ Performance      │
│ • Style issues │   │ Reviewer        │   │ Optimizer        │
│ • Code smells  │   │ • Vulnerabilities│   │ • Complexity     │
│ • Best practices│   │ • OWASP Top 10  │   │ • Bottlenecks    │
└────────────────┘   └─────────────────┘   └──────────────────┘
```

### How It Works

1. **User submits code** via Streamlit UI or CLI
2. **Review Orchestrator** coordinates the review process
3. **Specialized agents** analyze from different perspectives:
   - **Code Analyzer**: Style, structure, maintainability
   - **Security Reviewer**: Vulnerabilities, exploits, security best practices
   - **Performance Optimizer**: Algorithm complexity, bottlenecks, optimizations
4. **Agents discuss** findings through AutoGen group chat
5. **Orchestrator synthesizes** final report with prioritized issues
6. **User receives** comprehensive review with grades and actionable fixes

---

## ✨ Key Features

### 🤖 Multi-Agent Collaboration

Agents engage in natural conversations to analyze code:

```
[ReviewOrchestrator]: "Let's begin the review. CodeAnalyzer, please start."

[CodeAnalyzer]: "I found SQL injection on line 4, nested loops causing O(n²) 
complexity, and MD5 hashing which is cryptographically weak."

[SecurityReviewer]: "Confirming SQL injection - this is CRITICAL. Also found 
hardcoded API key on line 24. These must be addressed immediately."

[PerformanceOptimizer]: "The nested loop is O(n²). Suggesting hash map approach 
for O(n) complexity. Also recommend caching for repeated calls."

[ReviewOrchestrator]: "Final grade: C-. Priority: Fix SQL injection (Critical), 
then O(n²) loops (High), then hardcoded secrets (Critical)."
```

### 🛡️ Comprehensive Analysis

**Multi-Dimensional Review:**
- **Code Quality**: PEP 8 compliance, readability, maintainability
- **Security**: SQL injection, XSS, weak crypto, hardcoded secrets
- **Performance**: Time/space complexity, bottlenecks, optimizations
- **Best Practices**: Error handling, documentation, design patterns

**Tool Integration Ready:**
- Pylint for code quality metrics
- Bandit for security vulnerability scanning
- Radon for cyclomatic complexity analysis
- Extensible architecture for additional tools

### 📊 Structured Reports

```markdown
## Code Review Summary
Grade: C-

### 🔴 Critical Issues (3)
1. SQL Injection in get_user function (Line 4)
2. Weak MD5 cryptography in hash_password (Line 21)
3. Hardcoded API key (Line 24)

### 🟡 High Priority (1)
1. O(n²) nested loops in process_data (Line 12-15)

### 💡 Recommendations
- Use parameterized queries for SQL
- Replace MD5 with bcrypt
- Move secrets to environment variables
- Optimize nested loop with hash map
```

---

## 🛠️ Installation & Setup

### Prerequisites

```bash
Python 3.9+
OpenAI API key
```

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/bryan-lolordo/code-review-crew.git
cd code-review-crew
```

2. **Create virtual environment**
```bash
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Mac/Linux:
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
# Create .env file
echo "OPENAI_API_KEY=your_key_here" > .env
```

5. **Run the application**
```bash
streamlit run app.py
```

Navigate to `http://localhost:8501` in your browser.

---

## 💻 Usage

### Web Interface

1. **Load Example Code**
   - Click "Load Example" radio button
   - Select from predefined examples (SQL Injection, Performance Issues, etc.)
   - Or paste your own Python code

2. **Configure Review** (Optional)
   - Adjust max conversation rounds (5-30)
   - Set AI temperature (0.0-1.0)
   - Choose analysis depth

3. **Start Review**
   - Click "🚀 Start Review" button
   - Wait 30-60 seconds while agents analyze
   - Watch agents collaborate in real-time

4. **View Results**
   - **Results Tab**: See final grades and prioritized issues
   - **Agent Chat Tab**: Watch full conversation between agents
   - Each agent provides specific analysis and recommendations

### Command Line

```bash
# Test the standalone version
python run_group_chat_standalone.py

# Test with real tools integration
python run_group_chat.py
```

---

## 📁 Project Structure

```
code-review-crew/
├── README.md                        # This file
├── ARCHITECTURE.md                  # Detailed technical documentation
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (create this)
├── .gitignore
│
├── app.py                          # Streamlit web interface
├── run_group_chat.py               # AutoGen integration with tools
├── run_group_chat_standalone.py    # Standalone demo version
├── autogen_integration.py          # Helper for agent integration
│
├── code_review_crew/               # Main package
│   ├── agents/                     # Agent definitions
│   │   ├── base_agent.py          # Abstract base class
│   │   ├── orchestrator.py        # Review coordinator
│   │   ├── code_analyzer.py       # Code quality expert
│   │   ├── security_reviewer.py   # Security expert
│   │   ├── performance_optimizer.py # Performance expert
│   │   ├── test_generator.py      # Test creation expert
│   │   └── code_executor.py       # Safe code execution
│   │
│   ├── tools/                      # Analysis tools
│   │   ├── linting_tool.py        # Pylint wrapper
│   │   ├── security_scanner.py    # Bandit wrapper
│   │   ├── complexity_analyzer.py # Radon wrapper
│   │   ├── test_runner.py         # Pytest wrapper
│   │   └── git_tool.py            # Git diff parser
│   │
│   └── utils/                      # Helper utilities
│       ├── code_parser.py         # AST parsing
│       ├── report_generator.py    # Report formatting
│       └── sandbox_manager.py     # Docker management
│
└── examples/                       # Example code files
    ├── sql_injection.py
    ├── performance_issues.py
    └── security_issues.py
```

---

## 🎯 AutoGen Patterns Demonstrated

### 1. **Group Chat Orchestration**
Multiple agents engage in structured conversations to analyze code collaboratively.

### 2. **Agent Specialization**
Each agent has a specific expertise and system prompt guiding their analysis.

### 3. **Consensus Building**
Agents discuss, debate, and agree on issue priorities through natural dialogue.

### 4. **Tool Integration Architecture**
Extensible design allows agents to call external analysis tools when needed.

### 5. **Iterative Refinement**
Agents can build on each other's findings for comprehensive analysis.

---

## 📊 Example Output

### Input Code:
```python
def get_user(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return db.execute(query)

def hash_password(password):
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()

API_KEY = "sk-1234567890abcdef"
```

### Agent Analysis:

**CodeAnalyzer** identified:
- SQL injection vulnerability (Line 3)
- Import statement inside function (Line 6)
- Hardcoded secret (Line 9)

**SecurityReviewer** confirmed:
- CRITICAL: SQL injection - Use parameterized queries
- CRITICAL: Weak MD5 hashing - Use bcrypt instead
- CRITICAL: Hardcoded API key - Use environment variables

**ReviewOrchestrator** synthesized:
- Overall Grade: **C-**
- 3 Critical issues requiring immediate attention
- Provided specific code fixes for each issue

---

## 🔑 Core Dependencies

```
pyautogen==0.2.32          # Multi-agent orchestration
openai>=1.0.0              # LLM API
streamlit>=1.28.0          # Web interface
pylint>=3.0.0              # Code quality analysis
bandit>=1.7.5              # Security scanning
radon>=6.0.1               # Complexity analysis
python-dotenv>=1.0.0       # Environment management
```

---

## 🚀 What Makes This Special

### Advanced Multi-Agent Patterns

1. **Natural Language Collaboration**: Agents communicate through conversation, not just API calls
2. **Emergent Intelligence**: Insights arise from agent interactions
3. **Modular Architecture**: Easy to add new agents or modify existing ones
4. **Production-Ready Design**: Proper error handling, logging, and testing structure

### Real-World Application

- Solves actual code review challenges
- Provides actionable feedback with specific line numbers
- Grades code quality (A-F scale)
- Prioritizes issues by severity
- Demonstrates multi-agent systems at scale

---

## 📚 Documentation

For detailed technical architecture and implementation details:
- [ARCHITECTURE.md](ARCHITECTURE.md) - Complete technical documentation
- [API Documentation](#) - Coming soon
- [Tutorial Videos](#) - Coming soon

---

## 🙏 Acknowledgments

**AI Frameworks:**
- [Microsoft AutoGen](https://github.com/microsoft/autogen) - Multi-agent orchestration
- [OpenAI API](https://openai.com/) - Language models

**Analysis Tools:**
- [Pylint](https://pylint.org/) - Python code analysis
- [Bandit](https://bandit.readthedocs.io/) - Security linting
- [Radon](https://radon.readthedocs.io/) - Code metrics

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 👤 Author

**Bryan LoLordo**
- GitHub: [@bryan-lolordo](https://github.com/bryan-lolordo)
- Focus: Multi-Agent AI Systems & Production ML
- Portfolio: Demonstrating advanced AutoGen patterns

---

## 🎓 Learning Outcomes

This project demonstrates proficiency in:

✅ Multi-agent system architecture and design  
✅ Microsoft AutoGen framework and group chat patterns  
✅ LLM orchestration and prompt engineering  
✅ Tool integration and API design  
✅ Production-ready Python development  
✅ Modular, testable, maintainable code architecture  

---

**Built with ❤️ using Multi-Agent AI**

*Transforming code review through collaborative AI agents* 🚀
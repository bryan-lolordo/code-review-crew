"""
Code Review Crew - Streamlit Web Interface

Multi-agent code review system using AutoGen
"""

import streamlit as st
import os
import warnings
warnings.filterwarnings('ignore', message='flaml.automl is not available')
from dotenv import load_dotenv
from run_group_chat import CodeReviewChat

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Code Review Crew",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .agent-chat {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .issue-critical {
        color: #d32f2f;
        font-weight: bold;
    }
    .issue-high {
        color: #f57c00;
        font-weight: bold;
    }
    .issue-medium {
        color: #fbc02d;
        font-weight: bold;
    }
    .issue-low {
        color: #388e3c;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'review_history' not in st.session_state:
    st.session_state.review_history = []
if 'current_code' not in st.session_state:
    st.session_state.current_code = ""
if 'review_running' not in st.session_state:
    st.session_state.review_running = False
if 'current_results' not in st.session_state:
    st.session_state.current_results = None

# Header
st.markdown('<div class="main-header">🔍 Code Review Crew</div>', unsafe_allow_html=True)
st.markdown("""
<p style='text-align: center; font-size: 1.2rem; color: #666;'>
    Multi-Agent AI System for Comprehensive Code Analysis
</p>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Review settings
    st.subheader("Review Settings")
    review_depth = st.selectbox(
        "Analysis Depth",
        ["Quick", "Standard", "Deep"],
        index=1,
        help="Quick: Basic checks only. Standard: All agents. Deep: Extended analysis with iterations."
    )
    
    # Agent selection
    st.subheader("Active Agents")
    enable_code_analyzer = st.checkbox("Code Analyzer", value=True)
    enable_security = st.checkbox("Security Reviewer", value=True)
    enable_performance = st.checkbox("Performance Optimizer", value=True)
    enable_test_gen = st.checkbox("Test Generator", value=False)
    enable_executor = st.checkbox("Code Executor", value=False, 
                                   help="Run code in Docker sandbox (requires Docker)")
    
    # Advanced settings
    with st.expander("Advanced Settings"):
        max_rounds = st.slider("Max Conversation Rounds", 5, 30, 10)
        timeout = st.slider("Review Timeout (seconds)", 60, 600, 300)
        temperature = st.slider("AI Temperature", 0.0, 1.0, 0.7, 0.1)
    
    # API status
    st.divider()
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        st.success("✅ OpenAI API Key Configured")
    else:
        st.error("❌ OpenAI API Key Missing")
        st.info("Add OPENAI_API_KEY to .env file")

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["📝 Review Code", "📊 Results", "💬 Agent Chat", "📚 Examples"])

with tab1:
    st.header("Submit Code for Review")
    
    # Code input methods
    input_method = st.radio(
        "Input Method",
        ["Paste Code", "Upload File", "Load Example"],
        horizontal=True
    )
    
    if input_method == "Paste Code":
        code_input = st.text_area(
            "Paste your Python code here:",
            value=st.session_state.current_code,
            height=400,
            placeholder="def my_function():\n    # Your code here\n    pass"
        )
    
    elif input_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Choose a Python file",
            type=['py'],
            help="Upload a .py file to review"
        )
        if uploaded_file:
            code_input = uploaded_file.read().decode('utf-8')
            st.code(code_input, language='python')
        else:
            code_input = ""
    
    else:  # Load Example
        example_choice = st.selectbox(
            "Choose an example:",
            [
                "SQL Injection",
                "Performance Issues",
                "Security Issues",
                "All Issues"
            ]
        )
        
        # Example code samples
        examples = {
            "SQL Injection": """
def get_user(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return db.execute(query)
""",
            "Performance Issues": """
def process_data(items):
    result = []
    for i in items:
        for j in items:
            if i['id'] == j['parent']:
                result.append(i)
    return result
""",
            "Security Issues": """
def hash_password(password):
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()

API_KEY = "sk-1234567890abcdef"
""",
            "All Issues": """
def get_user(username):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return db.execute(query)

def process_data(items):
    # O(n²) nested loop
    result = []
    for i in items:
        for j in items:
            if i['id'] == j['parent']:
                result.append(i)
    return result

def hash_password(password):
    # Weak crypto
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()

# Hardcoded secret
API_KEY = "sk-1234567890abcdef"
"""
        }
        
        code_input = examples[example_choice]
        st.code(code_input, language='python')
    
    # Review button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Review", use_container_width=True, type="primary"):
            if not code_input:
                st.error("Please provide code to review")
            elif not api_key:
                st.error("OpenAI API key not configured")
            else:
                st.session_state.current_code = code_input
                st.session_state.review_running = True
                
                # Run the AutoGen code review
                with st.spinner("🤖 Agents are analyzing your code..."):
                    try:
                        # Initialize the review system
                        chat = CodeReviewChat()
                        
                        # Run the review
                        results = chat.review_code(code_input)
                        
                        # Store results in session state
                        st.session_state.review_history.append(results)
                        st.session_state.current_results = results
                        
                        st.success("✅ Review complete! Check the Results and Agent Chat tabs.")
                        
                    except Exception as e:
                        st.error(f"Error during review: {str(e)}")
                        st.exception(e)
                        st.session_state.current_results = None
                
                st.session_state.review_running = False

with tab2:
    st.header("📊 Review Results")
    
    if st.session_state.current_results is None:
        st.info("No reviews yet. Submit code in the 'Review Code' tab to get started.")
    else:
        results = st.session_state.current_results
        
        st.subheader("✅ Review Complete")
        
        # Show total messages
        st.metric("Total Agent Messages", len(results['conversation']))
        
        st.divider()
        
        # Display the conversation in expandable sections
        st.subheader("Agent Analysis")
        
        for i, msg in enumerate(results['conversation']):
            speaker = msg['speaker']
            content = msg['content']
            
            # Skip the initial user message
            if speaker == "User":
                continue
            
            # Use different icons for different agents
            icon = {
                "ReviewOrchestrator": "🎯",
                "CodeAnalyzer": "🔍",
                "SecurityReviewer": "🛡️",
                "PerformanceOptimizer": "⚡"
            }.get(speaker, "🤖")
            
            with st.expander(f"{icon} {speaker}", expanded=(i <= 2)):
                st.markdown(content)

with tab3:
    st.header("💬 Agent Conversation")
    
    if st.session_state.current_results is None:
        st.info("Agent conversations will appear here during review")
    else:
        results = st.session_state.current_results
        
        st.write(f"**Total messages exchanged:** {len(results['conversation'])}")
        
        st.divider()
        
        for msg in results['conversation']:
            speaker = msg['speaker']
            content = msg['content']
            
            # Color code by agent
            if speaker == "ReviewOrchestrator":
                st.markdown(f'<div class="agent-chat" style="border-left: 4px solid #667eea;">', unsafe_allow_html=True)
            elif speaker == "CodeAnalyzer":
                st.markdown(f'<div class="agent-chat" style="border-left: 4px solid #4299e1;">', unsafe_allow_html=True)
            elif speaker == "SecurityReviewer":
                st.markdown(f'<div class="agent-chat" style="border-left: 4px solid #f56565;">', unsafe_allow_html=True)
            elif speaker == "PerformanceOptimizer":
                st.markdown(f'<div class="agent-chat" style="border-left: 4px solid #48bb78;">', unsafe_allow_html=True)
            else:
                st.markdown('<div class="agent-chat">', unsafe_allow_html=True)
            
            st.markdown(f"**[{speaker}]**")
            st.write(content)
            st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.header("📚 Code Examples")
    
    st.markdown("""
    Try these example code snippets to see the review system in action:
    
    ### 1. SQL Injection
    Example with SQL injection vulnerability
    ```python
    def get_user(username):
        query = f"SELECT * FROM users WHERE name = '{username}'"
        return db.execute(query)
    ```
    
    ### 2. Performance Issues
    Code with O(n²) nested loops
    ```python
    def process_data(items):
        result = []
        for i in items:
            for j in items:
                if i['id'] == j['parent']:
                    result.append(i)
        return result
    ```
    
    ### 3. Security Issues
    Weak cryptography and hardcoded secrets
    ```python
    import hashlib
    
    def hash_password(password):
        return hashlib.md5(password.encode()).hexdigest()
    
    API_KEY = "sk-1234567890abcdef"
    ```
    
    ### 4. All Issues Combined
    Select "All Issues" from the Load Example dropdown to see multiple problems
    
    ---
    
    ## What the Agents Will Find:
    
    - **CodeAnalyzer**: Style issues, code smells, missing docstrings
    - **SecurityReviewer**: SQL injection, weak crypto, hardcoded secrets
    - **PerformanceOptimizer**: O(n²) complexity, inefficient algorithms
    
    Click "Load Example" above and select an example to try it!
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    Built with ❤️ using AutoGen and Streamlit<br>
    <a href='https://github.com/bryan-lolordo/code-review-crew'>View on GitHub</a>
</div>
""", unsafe_allow_html=True)
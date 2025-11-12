"""
Code Review Crew - Streamlit Web Interface

Multi-agent code review system using AutoGen
"""

import streamlit as st
import os
from dotenv import load_dotenv

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
    enable_test_gen = st.checkbox("Test Generator", value=True)
    enable_executor = st.checkbox("Code Executor", value=False, 
                                   help="Run code in Docker sandbox (requires Docker)")
    
    # Advanced settings
    with st.expander("Advanced Settings"):
        max_rounds = st.slider("Max Conversation Rounds", 5, 30, 20)
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
                "Simple Function",
                "Security Issues",
                "Performance Issues",
                "Complex Class"
            ]
        )
        # Placeholder - would load from examples/ directory
        code_input = "# Example code would be loaded here\npass"
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
                
                # Placeholder for actual review logic
                with st.spinner("🤖 Agents are analyzing your code..."):
                    st.info("Review system will be implemented here")
                    # TODO: Initialize AutoGen agents and run review
                    # review_results = run_review(code_input, config)
                
                st.session_state.review_running = False

with tab2:
    st.header("📊 Review Results")
    
    if not st.session_state.review_history:
        st.info("No reviews yet. Submit code in the 'Review Code' tab to get started.")
    else:
        # Placeholder for results display
        st.subheader("Latest Review Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Overall Score", "B+", "85/100")
        with col2:
            st.metric("Critical Issues", "2", "🔴")
        with col3:
            st.metric("Warnings", "5", "🟡")
        with col4:
            st.metric("Suggestions", "8", "💡")
        
        # Issues list
        st.subheader("🔴 Critical Issues")
        with st.expander("SQL Injection Vulnerability (Line 45)", expanded=True):
            st.markdown("""
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
            """)
        
        st.subheader("🟡 Warnings")
        st.info("High complexity function detected on line 112")
        
        st.subheader("💡 Suggestions")
        st.success("Consider using list comprehension on line 67")

with tab3:
    st.header("💬 Agent Conversation")
    
    if not st.session_state.review_running and not st.session_state.review_history:
        st.info("Agent conversations will appear here during review")
    else:
        # Placeholder for agent chat display
        st.markdown('<div class="agent-chat">', unsafe_allow_html=True)
        st.markdown("**[Review Orchestrator]** 🎯")
        st.write("Let's begin the code review. Code Analyzer, please start with your analysis.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="agent-chat">', unsafe_allow_html=True)
        st.markdown("**[Code Analyzer]** 🔍")
        st.write("I've identified 3 style issues and 1 potential bug. Running Pylint analysis...")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="agent-chat">', unsafe_allow_html=True)
        st.markdown("**[Security Reviewer]** 🛡️")
        st.write("Critical security issue detected: SQL injection vulnerability on line 45.")
        st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.header("📚 Code Examples")
    
    st.markdown("""
    Try these example code snippets to see the review system in action:
    
    ### 1. Simple Function
    Basic function with style issues
    
    ### 2. Security Issues
    Code with common security vulnerabilities:
    - SQL injection
    - Weak password hashing
    - Unvalidated input
    
    ### 3. Performance Issues
    Code with performance problems:
    - Nested loops (O(n²))
    - Inefficient algorithms
    - Memory leaks
    
    ### 4. Complex Class
    Large class demonstrating:
    - High cyclomatic complexity
    - Code smells
    - Missing documentation
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    Built with ❤️ using AutoGen and Streamlit<br>
    <a href='https://github.com/yourusername/code-review-crew'>View on GitHub</a>
</div>
""", unsafe_allow_html=True)
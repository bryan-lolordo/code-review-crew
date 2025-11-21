"""
Code Review Crew - Streamlit Web Interface

Multi-agent code review system using AutoGen + LangGraph
"""

import streamlit as st
import os
import warnings
warnings.filterwarnings('ignore', message='flaml.automl is not available')
from dotenv import load_dotenv
from run_group_chat import CodeReviewChat
from unified_analyzer import UnifiedCodeAnalyzer

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
    .issue-critical { color: #d32f2f; font-weight: bold; }
    .issue-high { color: #f57c00; font-weight: bold; }
    .issue-medium { color: #fbc02d; font-weight: bold; }
    .issue-low { color: #388e3c; }
    .log-section {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 15px;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        overflow-x: auto;
        margin: 10px 0;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .log-success { color: #4ec9b0; }
    .log-warning { color: #ce9178; }
    .log-error { color: #f48771; }
    .log-info { color: #569cd6; }
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
    Multi-Agent AI System: Review + Auto-Fix
</p>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Mode selector
    st.subheader("Analysis Mode")
    analysis_mode = st.radio(
        "Choose:",
        ["Review Only", "Review + Auto-Fix 🔥"],
        help="Review Only: AutoGen review | Auto-Fix: AutoGen + LangGraph"
    )
    
    if "Auto-Fix" in analysis_mode:
        st.info("🔥 LangGraph will fix issues iteratively!")
        max_fix_iterations = st.slider("Max Fix Iterations", 1, 20, 5)
    
    st.divider()
    api_key = os.getenv("OPENAI_API_KEY")
    st.success("✅ API Key" if api_key else "❌ API Key Missing")

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Code", "📊 Results", "🔍 Process Logs", "💬 Chat", "📚 Examples"])

with tab1:
    st.header("Submit Code")
    
    input_method = st.radio("Input:", ["Paste Code", "Load Example"], horizontal=True)
    
    if input_method == "Paste Code":
        code_input = st.text_area("Python code:", height=400)
    else:
        example = st.selectbox("Choose:", ["All Issues", "SQL Injection", "Security", "Complex Example"])
        examples = {
            "All Issues": """def get_user(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return db.execute(query)

def hash_password(password):
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()

API_KEY = "sk-1234567890abcdef"
""",
            "SQL Injection": """def get_user(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return db.execute(query)
""",
            "Security": """def hash_password(password):
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()

API_KEY = "sk-1234567890abcdef"
""",
            "Complex Example": """class UserManager:
    def __init__(self):
        self.users = {}
        self.cache = []
    
    def add_user(self, user_id, data):
        if user_id not in self.users:
            self.users[user_id] = data
            self.cache.append(user_id)
    
    def get_users_by_age(self, min_age, max_age):
        results = []
        for user_id, data in self.users.items():
            if min_age <= data['age'] <= max_age:
                results.append(data)
        return results
    
    def batch_update(self, updates):
        for user_id, new_data in updates:
            if user_id in self.users:
                old_data = self.users[user_id]
                self.users[user_id] = {**old_data, **new_data}
                self.cache.append(user_id)
    
    def serialize(self):
        import pickle
        return pickle.dumps(self.users)
    
    @staticmethod
    def calculate_metrics(user_list):
        total_age = sum(u['age'] for u in user_list)
        avg_age = total_age / len(user_list)
        return avg_age

def process_payment(amount, card_number):
    print(f"Processing payment: ${amount} with card {card_number}")
    if amount > "100":
        apply_discount(amount)
    return {"status": "success", "amount": amount}
"""
        }
        code_input = examples[example]
        st.code(code_input, language='python')
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        btn_label = "🚀 Start" if analysis_mode == "Review Only" else "🔥 Review + Fix"
        
        if st.button(btn_label, use_container_width=True, type="primary"):
            if not code_input:
                st.error("Please provide code")
            elif not api_key:
                st.error("API key missing")
            else:
                st.session_state.current_code = code_input 
                
                if analysis_mode == "Review Only":
                    with st.spinner("🤖 Analyzing..."):
                        try:
                            analyzer = UnifiedCodeAnalyzer()
                            results = analyzer.review_only(code_input)
                            st.session_state.current_results = results
                            st.success("✅ Done!")
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    with st.spinner("🔥 Reviewing and fixing..."):
                        try:
                            analyzer = UnifiedCodeAnalyzer()
                            results = analyzer.review_and_fix(code_input, max_fix_iterations)
                            st.session_state.current_results = results
                            if results.get('success'):
                                st.success(f"✅ Fixed {results['issues_fixed']} issues!")
                        except Exception as e:
                            st.error(f"Error: {e}")

with tab2:
    st.header("📊 Results")
    
    if st.session_state.current_results is None:
        st.info("No results yet")
    else:
        results = st.session_state.current_results
        
        if results.get('mode') == 'review_and_fix':
            # Review + Fix results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Found", results.get('issues_found', 0))
            with col2:
                st.metric("Fixed", results.get('issues_fixed', 0))
            with col3:
                st.metric("Iterations", results.get('iterations', 0))
            
            st.divider()
            st.subheader("Code Comparison")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Original**")
                st.code(st.session_state.current_code, language='python')
            with col_b:
                st.markdown("**Fixed**")
                if 'fixed_code' in results:
                    st.code(results['fixed_code'], language='python')
                    st.download_button("⬇️ Download", results['fixed_code'], "fixed.py")
        
        else:
            # Review only results
            if 'conversation' in results:
                st.metric("Messages", len(results['conversation']))
                st.divider()
                
                for msg in results['conversation']:
                    if msg['speaker'] != "User":
                        icon = {"ReviewOrchestrator": "🎯", "CodeAnalyzer": "🔍", 
                               "SecurityReviewer": "🛡️", "PerformanceOptimizer": "⚡"}.get(msg['speaker'], "🤖")
                        with st.expander(f"{icon} {msg['speaker']}"):
                            st.markdown(msg['content'])

with tab3:
    st.header("🔍 Process Logs")
    
    if st.session_state.current_results:
        results = st.session_state.current_results
        
        # Show logs if available
        if 'logs' in results and results['logs']:
            logs = results['logs']
            
            # Extract sections
            sections = {
                'review': '',
                'extraction': '',
                'fixing': '',
                'summary': ''
            }
            
            if "STEP 1:" in logs:
                sections['review'] = logs.split("STEP 1:")[1].split("STEP 2:")[0] if "STEP 2:" in logs else logs.split("STEP 1:")[1]
            
            if "STEP 2:" in logs:
                sections['extraction'] = logs.split("STEP 2:")[1].split("STEP 3:")[0] if "STEP 3:" in logs else logs.split("STEP 2:")[1]
            
            if "STEP 3:" in logs:
                sections['fixing'] = logs.split("STEP 3:")[1].split("SUMMARY")[0] if "SUMMARY" in logs else logs.split("STEP 3:")[1]
            
            if "SUMMARY" in logs:
                sections['summary'] = logs.split("SUMMARY")[1]
            
            # Display summary first if available
            if sections['summary']:
                st.markdown("### 📊 Summary")
                st.markdown(f'<div class="log-section">{sections["summary"]}</div>', unsafe_allow_html=True)
                st.divider()
            
            # AutoGen Review
            if sections['review']:
                with st.expander("📋 Step 1: AutoGen Multi-Agent Review", expanded=False):
                    st.markdown(f'<div class="log-section">{sections["review"]}</div>', unsafe_allow_html=True)
            
            # Issue Extraction
            if sections['extraction']:
                with st.expander("🔍 Step 2: Issue Extraction", expanded=True):
                    st.markdown(f'<div class="log-section">{sections["extraction"]}</div>', unsafe_allow_html=True)
            
            # LangGraph Fixing
            if sections['fixing']:
                st.markdown("### 🔧 Step 3: LangGraph Iterative Fixing")
                
                # Split by iterations
                iterations = sections['fixing'].split("🔧 Iteration")
                
                for i, iteration_text in enumerate(iterations[1:], 1):  # Skip first empty split
                    # Determine if should be expanded (first 3 iterations)
                    expanded = (i <= 3)
                    
                    with st.expander(f"🔧 Iteration {i}", expanded=expanded):
                        st.markdown(f'<div class="log-section">🔧 Iteration{iteration_text}</div>', unsafe_allow_html=True)
        else:
            st.info("No process logs available. Run a review to see detailed logs.")
    else:
        st.info("No results yet. Run a code review to see the process logs.")

with tab4:
    st.header("💬 Conversation")
    
    if st.session_state.current_results:
        results = st.session_state.current_results
        conversation = results.get('conversation', [])
        
        if results.get('mode') == 'review_and_fix':
            conversation = results.get('original_review', {}).get('conversation', [])
        
        # Added safety check for None conversation
        if conversation:
            for msg in conversation:
                colors = {"ReviewOrchestrator": "#667eea", "CodeAnalyzer": "#4299e1",
                         "SecurityReviewer": "#f56565", "PerformanceOptimizer": "#48bb78"}
                color = colors.get(msg['speaker'], "#999")
                st.markdown(f'<div class="agent-chat" style="border-left: 4px solid {color};">', unsafe_allow_html=True)
                st.markdown(f"**[{msg['speaker']}]**")
                st.write(msg['content'])
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No conversation history available")
    else:
        st.info("No results yet. Run a code review to see the conversation.")

with tab5:
    st.header("📚 Examples")
    st.markdown("""
    ## 🎯 Two Modes
    
    **Review Only**: Multi-agent code review
    **Review + Auto-Fix 🔥**: Review + iterative fixing with LangGraph
    
    ## 💡 Examples Available
    
    ### All Issues
    - SQL injection → Parameterized queries
    - Weak MD5 → SHA256
    - Hardcoded secrets → Environment variables
    
    ### Complex Example (Tests LLM Fallback)
    - Race conditions → Thread safety
    - Memory leaks → Data structure optimization
    - Pickle vulnerabilities → Safe serialization
    - Division by zero → Input validation
    - PCI compliance → Sensitive data masking
    
    **The complex example will use GPT-4 for fixes since these issues don't match simple patterns!**
    
    ## 🔍 Process Logs Tab
    
    The new **Process Logs** tab shows you:
    - Step-by-step execution of the review and fixing process
    - Which patterns matched vs. which needed LLM fallback
    - Detailed iteration-by-iteration progress
    - Test results for each fix
    
    This gives you full visibility into how the AI agents are working together!
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    Built with AutoGen + LangGraph + Streamlit
</div>
""", unsafe_allow_html=True)
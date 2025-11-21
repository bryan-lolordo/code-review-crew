"""
Standalone AutoGen Group Chat Runner

This is a self-contained version for testing without the full project structure.
For production, use the version that imports from code_review_crew package.
"""

import os
import autogen
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class CodeReviewChat:
    """Standalone class to run AutoGen group chat code reviews"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.llm_config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "api_key": self.api_key
        }
        
        # Agents
        self.agents = {}
        self.group_chat = None
        self.chat_manager = None
        
    def create_agents(self):
        """Create all AutoGen agents"""
        
        # Orchestrator
        self.agents['orchestrator'] = autogen.AssistantAgent(
            name="ReviewOrchestrator",
            system_message="""You coordinate the code review process. 
            
            Your workflow:
            1. Start by asking CodeAnalyzer for their analysis
            2. Then ask SecurityReviewer for security assessment
            3. Then ask PerformanceOptimizer for performance review
            4. Synthesize all feedback into a final report
            
            Your final report must include:
            - Overall Grade (A-F)
            - Issues categorized by priority: Critical, High, Medium, Low
            - Specific line numbers for each issue
            - Clear, actionable recommendations
            
            Keep the conversation focused and efficient.""",
            llm_config=self.llm_config
        )
        
        # Code Analyzer
        self.agents['code_analyzer'] = autogen.AssistantAgent(
            name="CodeAnalyzer",
            system_message="""You are a code quality expert.
            
            Analyze code for:
            - PEP 8 style violations
            - Code smells (long functions, duplicate code, god objects)
            - Poor naming conventions
            - Missing docstrings
            - Potential bugs
            
            Provide specific line numbers and clear fix suggestions.
            Categorize issues by severity: Critical, High, Medium, Low.""",
            llm_config=self.llm_config
        )
        
        # Security Reviewer
        self.agents['security'] = autogen.AssistantAgent(
            name="SecurityReviewer",
            system_message="""You are a security expert.
            
            Check for:
            - SQL injection vulnerabilities (string concatenation in queries)
            - XSS vulnerabilities
            - Hardcoded secrets (passwords, API keys)
            - Weak cryptography (MD5, SHA1)
            - Command injection (os.system, eval, exec)
            - Insecure deserialization (pickle)
            
            Mark ALL security issues as CRITICAL priority.
            Explain the exploit and provide secure alternatives.""",
            llm_config=self.llm_config
        )
        
        # Performance Optimizer
        self.agents['performance'] = autogen.AssistantAgent(
            name="PerformanceOptimizer",
            system_message="""You are a performance optimization expert.
            
            Analyze for:
            - Nested loops (O(n²) or worse complexity)
            - Inefficient string concatenation in loops
            - Missing caching opportunities
            - Repeated database/API calls
            - Inefficient data structures (list vs set for lookups)
            
            For each issue:
            - Explain current complexity (e.g., O(n²))
            - Suggest optimization with improved complexity
            - Provide code example of the fix""",
            llm_config=self.llm_config
        )
        
        # User proxy
        self.agents['user'] = autogen.UserProxyAgent(
            name="User",
            system_message="User submitting code for review",
            code_execution_config=False,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0
        )
    
    def setup_group_chat(self):
        """Setup the AutoGen group chat"""
        
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
            max_round=5,
            speaker_selection_method="auto"
        )
        
        self.chat_manager = autogen.GroupChatManager(
            groupchat=self.group_chat,
            llm_config=self.llm_config
        )
    
    def review_code(self, code: str) -> Dict:
        """Run code review"""
        
        # Setup
        self.create_agents()
        self.setup_group_chat()
        
        # Initial message
        message = f"""Please conduct a comprehensive code review of the following Python code:

```python
{code}
```

ReviewOrchestrator: Please start the review process by coordinating with each specialized agent."""
        
        # Run chat
        print("Starting code review...")
        print("="*80)
        
        self.agents['user'].initiate_chat(
            self.chat_manager,
            message=message
        )
        
        print("="*80)
        print("Review complete!")
        
        # Return results
        return {
            'messages': self.group_chat.messages,
            'conversation': [
                {
                    'speaker': m.get('name', 'Unknown'), 
                    'content': m.get('content', '')
                } 
                for m in self.group_chat.messages
            ]
        }


def main():
    """Test the group chat with example code"""
    
    # Example code with multiple issues
    test_code = """
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
    
    print("\n" + "="*80)
    print("TESTING AUTOGEN CODE REVIEW GROUP CHAT")
    print("="*80)
    print("\nCode to review:")
    print(test_code)
    print("\n" + "="*80)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\nERROR: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    try:
        # Run the review
        chat = CodeReviewChat()
        results = chat.review_code(test_code)
        
        # Display conversation
        print("\n" + "="*80)
        print("CODE REVIEW CONVERSATION")
        print("="*80)
        
        for msg in results['conversation']:
            print(f"\n{'='*80}")
            print(f"[{msg['speaker']}]")
            print(f"{'='*80}")
            print(msg['content'])
        
        print(f"\n\n{'='*80}")
        print(f"Total messages exchanged: {len(results['messages'])}")
        print("="*80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
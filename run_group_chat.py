"""
AutoGen Group Chat Runner for Code Review Crew

This module orchestrates the multi-agent code review system using custom agent classes.
"""

import os
import sys
import autogen
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import agent classes
try:
    from code_review_crew.agents.orchestrator import ReviewOrchestrator
    from code_review_crew.agents.code_analyzer import CodeAnalyzer
    from code_review_crew.agents.security_reviewer import SecurityReviewer
    from code_review_crew.agents.performance_optimizer import PerformanceOptimizer
    from code_review_crew.agents.test_generator import TestGenerator
    from code_review_crew.agents.code_executor import CodeExecutor
    from code_review_crew.tools.linting_tool import LintingTool
    from code_review_crew.tools.complexity_analyzer import ComplexityAnalyzer
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import agent classes: {e}")
    print("Falling back to direct AutoGen agents")
    AGENTS_AVAILABLE = False


class CodeReviewChat:
    """Main class to run AutoGen group chat code reviews using custom agent classes"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        self.llm_config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "api_key": self.api_key
        }
        
        # Initialize tools
        self.linting_tool = LintingTool()
        self.complexity_tool = ComplexityAnalyzer()
        
        # Create tools dictionary for agents
        self.tools = {
            'linting': self.linting_tool,
            'complexity': self.complexity_tool
        }
        
        # Agents (will be created later)
        self.agents = {}
        self.agent_instances = {}  # Store our custom agent class instances
        self.group_chat = None
        self.chat_manager = None
        
    def create_agents(self):
        """Create all agents using custom agent classes"""
        
        if not AGENTS_AVAILABLE:
            # Fallback to simple agents if imports failed
            self._create_simple_agents()
            return
        
        # Create custom agent instances
        self.agent_instances['orchestrator'] = ReviewOrchestrator(self.llm_config)
        self.agent_instances['code_analyzer'] = CodeAnalyzer(self.llm_config, self.tools)
        self.agent_instances['security'] = SecurityReviewer(self.llm_config, self.tools)
        self.agent_instances['performance'] = PerformanceOptimizer(self.llm_config, self.tools)
        self.agent_instances['test_generator'] = TestGenerator(self.llm_config, self.tools)
        self.agent_instances['code_executor'] = CodeExecutor(self.llm_config, self.tools)
        
        # Get AutoGen agents from our instances
        self.agents['orchestrator'] = self.agent_instances['orchestrator'].create_agent()
        self.agents['code_analyzer'] = self.agent_instances['code_analyzer'].create_agent()
        self.agents['security'] = self.agent_instances['security'].create_agent()
        self.agents['performance'] = self.agent_instances['performance'].create_agent()
        self.agents['test_generator'] = self.agent_instances['test_generator'].create_agent()
        self.agents['code_executor'] = self.agent_instances['code_executor'].create_agent()
        
        # User proxy agent
        self.agents['user'] = autogen.UserProxyAgent(
            name="User",
            system_message="User submitting code for review",
            code_execution_config=False,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0
        )
        
        print("✅ Created 6 agents using custom agent classes")
    
    def _create_simple_agents(self):
        """Fallback: Create simple agents directly with AutoGen"""
        
        self.agents['orchestrator'] = autogen.AssistantAgent(
            name="ReviewOrchestrator",
            system_message="""You coordinate the code review. 
            1. Start by asking CodeAnalyzer for analysis
            2. Then SecurityReviewer for security check
            3. Then PerformanceOptimizer for performance review
            4. Then TestGenerator for test suggestions
            5. Synthesize final report with grades (A-F)
            6. List issues by priority: Critical, High, Medium, Low""",
            llm_config=self.llm_config
        )
        
        self.agents['code_analyzer'] = autogen.AssistantAgent(
            name="CodeAnalyzer",
            system_message="""You analyze code quality.
            Report: style issues, bugs, code smells with line numbers.""",
            llm_config=self.llm_config
        )
        
        self.agents['security'] = autogen.AssistantAgent(
            name="SecurityReviewer",
            system_message="""You find security vulnerabilities.
            Check for: SQL injection, XSS, weak crypto, hardcoded secrets.
            Mark all security issues as CRITICAL.""",
            llm_config=self.llm_config
        )
        
        self.agents['performance'] = autogen.AssistantAgent(
            name="PerformanceOptimizer",
            system_message="""You analyze performance.
            Report: nested loops, O(n²) issues, caching opportunities.""",
            llm_config=self.llm_config
        )
        
        self.agents['test_generator'] = autogen.AssistantAgent(
            name="TestGenerator",
            system_message="""You generate test cases.
            Suggest pytest test cases for the code.""",
            llm_config=self.llm_config
        )
        
        self.agents['code_executor'] = autogen.UserProxyAgent(
            name="CodeExecutor",
            system_message="Executes code safely",
            code_execution_config=False,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0
        )
        
        self.agents['user'] = autogen.UserProxyAgent(
            name="User",
            system_message="User submitting code",
            code_execution_config=False,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0
        )
        
        print("⚠️  Using simple fallback agents (6 specialists)")
    
    def register_functions(self):
        """Register tool functions with agents"""
        
        if not AGENTS_AVAILABLE or not self.agent_instances:
            # Simple function registration for fallback
            return
        
        # Register functions from our custom agent classes
        for agent_name, agent_instance in self.agent_instances.items():
            if agent_name == 'orchestrator':
                continue  # Orchestrator doesn't need tools
            
            function_map = agent_instance.register_functions()
            if function_map:
                self.agents[agent_name].register_function(function_map=function_map)
        
        print("✅ Registered tool functions with agents")
    
    def setup_group_chat(self):
        """Setup the AutoGen group chat"""
        
        agent_list = [
            self.agents['user'],
            self.agents['orchestrator'],
            self.agents['code_analyzer'],
            self.agents['security'],
            self.agents['performance'],
            self.agents['test_generator'],
            self.agents['code_executor']
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
        
        print("✅ Setup group chat with 7 agents (6 specialists + 1 user)")
    
    def review_code(self, code: str) -> Dict:
        """
        Run comprehensive code review using multi-agent system
        
        Args:
            code: Python source code to review
        
        Returns:
            Dictionary containing review results and conversation history
        """
        
        print("\n" + "="*80)
        print("🚀 Starting Code Review with Multi-Agent System")
        print("="*80)
        
        # Setup
        self.create_agents()
        self.register_functions()
        self.setup_group_chat()
        
        # Initial message
        message = f"""Review this Python code:

```python
{code}
```

ReviewOrchestrator: Start the review process."""
        
        print("\n📨 Sending code to agents...")
        
        # Run chat
        self.agents['user'].initiate_chat(
            self.chat_manager,
            message=message
        )
        
        print("\n✅ Review complete!")
        print("="*80 + "\n")
        
        # Return results
        return {
            'messages': self.group_chat.messages,
            'conversation': [
                {'speaker': m.get('name'), 'content': m.get('content')} 
                for m in self.group_chat.messages
            ]
        }


def main():
    """Test the group chat with custom agent classes"""
    
    test_code = """
def get_user(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return db.execute(query)

def process_data(items):
    result = []
    for i in items:
        for j in items:
            if i['id'] == j['parent']:
                result.append(i)
    return result

def hash_password(password):
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()

API_KEY = "sk-1234567890abcdef"
"""
    
    print("\n" + "="*80)
    print("CODE REVIEW CREW - Multi-Agent System Test")
    print("="*80)
    
    chat = CodeReviewChat()
    results = chat.review_code(test_code)
    
    print("\n" + "="*80)
    print("REVIEW CONVERSATION")
    print("="*80)
    
    for i, msg in enumerate(results['conversation'], 1):
        print(f"\n[{i}] {msg['speaker']}:")
        print("-" * 40)
        # Truncate long messages for display
        content = msg['content']
        if len(content) > 300:
            content = content[:300] + "..."
        print(content)
    
    print(f"\n\n📊 Total messages: {len(results['messages'])}")
    print("="*80)


if __name__ == "__main__":
    main()
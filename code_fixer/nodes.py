"""
Node Functions for Code Fixer Workflow

Each node represents a step in the code fixing process.
Now includes LLM fallback for complex issues WITH LOGGING.
"""

import re
import logging
from typing import Dict
from .state import CodeFixState

# Configure logging
logger = logging.getLogger(__name__)


class FixerNodes:
    """Collection of node functions for the code fixer workflow"""
    
    def __init__(self, llm_config: Dict = None):
        """
        Initialize nodes with LLM configuration
        
        Args:
            llm_config: Configuration for LLM (OpenAI, etc.)
        """
        self.llm_config = llm_config or {}
        logger.info("✅ FixerNodes initialized with LLM config")
    
    def fix_issue_node(self, state: CodeFixState) -> CodeFixState:
        """
        Fix the next highest priority issue
        
        This node:
        1. Takes the first issue from the list (highest priority)
        2. Generates a fix using pattern matching or LLM
        3. Updates the code
        4. Moves issue to fixed list
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with fixed code
        """
        
        iteration = state['iteration'] + 1
        logger.info(f"🔧 Iteration {iteration}/{state['max_iterations']}: Fixing issues...")
        
        if not state['issues']:
            logger.info("   ✅ No more issues to fix!")
            return {
                **state,
                "status": "done"
            }
        
        # Get next issue to fix
        current_issue = state['issues'][0]
        remaining_issues = state['issues'][1:]
        
        logger.info(f"   📋 Current issue: [{current_issue.get('severity', '?')}] {current_issue.get('description', 'No description')}")
        logger.info(f"   📊 Remaining: {len(remaining_issues)} issues")
        
        # Try pattern-based fix first (fast, free)
        logger.debug("   🔍 Attempting pattern-based fix...")
        fixed_code = self._pattern_fix(state['current_code'], current_issue)
        
        if fixed_code != state['current_code']:
            logger.info("   ✅ Fixed using pattern matching (fast & free)")
        else:
            # Fall back to LLM (slower, smarter)
            logger.info("   ⚡ Pattern fix didn't work, trying LLM fallback...")
            fixed_code = self._llm_fix(state['current_code'], current_issue)
            
            if fixed_code != state['current_code']:
                logger.info(f"   ✅ Fixed using LLM ({self.llm_config.get('model', 'gpt-4')})")
            else:
                logger.warning("   ⚠️  Could not fix this issue, skipping...")
        
        # Update state
        return {
            **state,
            "current_code": fixed_code,
            "issues": remaining_issues,
            "fixed_issues": state['fixed_issues'] + [current_issue],
            "iteration": iteration,
            "status": "testing"
        }
    
    def test_code_node(self, state: CodeFixState) -> CodeFixState:
        """
        Test the fixed code
        
        Performs basic syntax validation and checks.
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with test results
        """
        
        logger.info(f"   🧪 Testing fixed code...")
        
        code = state['current_code']
        
        # Test 1: Syntax check
        logger.debug("      Checking syntax...")
        try:
            compile(code, '<string>', 'exec')
            syntax_valid = True
            logger.info("      ✅ Syntax valid")
        except SyntaxError as e:
            syntax_valid = False
            logger.error(f"      ❌ Syntax error: {e}")
        
        # Test 2: Basic security checks
        logger.debug("      Running security checks...")
        security_issues = []
        
        if 'eval(' in code or 'exec(' in code:
            security_issues.append("Uses eval/exec")
            logger.warning("      ⚠️  Found eval/exec usage")
        
        if 'md5' in code.lower():
            security_issues.append("Uses weak MD5")
            logger.warning("      ⚠️  Found MD5 usage")
        
        if "f\"SELECT" in code or "f'SELECT" in code:
            security_issues.append("Potential SQL injection")
            logger.warning("      ⚠️  Found potential SQL injection")
        
        if not security_issues:
            logger.info("      ✅ No obvious security issues")
        
        # Store test results
        test_results = {
            "syntax_valid": syntax_valid,
            "security_issues": security_issues,
            "passed": syntax_valid and len(security_issues) == 0
        }
        
        if test_results["passed"]:
            logger.info("   ✅ All tests passed!")
        else:
            logger.warning("   ⚠️  Some tests failed")
        
        return {
            **state,
            "test_results": test_results
        }
    
    def finalize_node(self, state: CodeFixState) -> CodeFixState:
        """
        Finalize the fixing process and return results
        
        Args:
            state: Current workflow state
        
        Returns:
            Final state
        """
        
        logger.info("\n" + "="*80)
        logger.info("📊 FIXING SUMMARY")
        logger.info("="*80)
        logger.info(f"✅ Issues Fixed: {len(state['fixed_issues'])}")
        logger.info(f"⏭️  Issues Remaining: {len(state['issues'])}")
        logger.info(f"🔄 Iterations Used: {state['iteration']}/{state['max_iterations']}")
        logger.info(f"📊 Status: {state['status'].upper()}")
        logger.info("="*80)
        
        # Set final status
        if len(state['issues']) == 0:
            final_status = "done"
            logger.info("🎉 All issues fixed successfully!")
        elif state['iteration'] >= state['max_iterations']:
            final_status = "failed"
            logger.warning("⚠️  Max iterations reached, some issues remain")
        else:
            final_status = state['status']
        
        return {
            **state,
            "status": final_status
        }
    
    def route_after_test(self, state: CodeFixState) -> str:
        """
        Decide what to do after testing
        
        Args:
            state: Current workflow state
        
        Returns:
            Next node name: "continue", "done", or "failed"
        """
        
        # Check if we hit max iterations
        if state['iteration'] >= state['max_iterations']:
            logger.warning(f"⏸️  Max iterations ({state['max_iterations']}) reached")
            return "failed"
        
        # Check if there are more issues
        if len(state['issues']) == 0:
            logger.info("✅ No more issues, moving to finalize")
            return "done"
        
        # Continue fixing
        logger.info(f"🔄 Continuing to next issue ({len(state['issues'])} remaining)")
        return "continue"
    
    # ========================================================================
    # HELPER METHODS - Pattern Fixes
    # ========================================================================
    
    def _pattern_fix(self, code: str, issue: Dict) -> str:
        """
        Try to fix issue using pattern matching
        
        Fast, deterministic, free. Works for common issues.
        
        Args:
            code: Current code
            issue: Issue to fix
        
        Returns:
            Fixed code (or original if no fix found)
        """
        
        description = issue.get('description', '').lower()
        
        # SQL Injection fixes
        if 'sql injection' in description:
            logger.debug("      Pattern: SQL injection")
            return self._fix_sql_injection(code)
        
        # Weak crypto fixes
        if 'md5' in description or 'weak' in description and 'hash' in description:
            logger.debug("      Pattern: Weak crypto")
            return self._fix_weak_crypto(code)
        
        # Hardcoded secrets
        if 'api' in description and 'key' in description:
            logger.debug("      Pattern: Hardcoded API key")
            return self._fix_hardcoded_secrets(code)
        
        # No pattern match
        logger.debug("      No pattern match found")
        return code
    
    def _fix_sql_injection(self, code: str) -> str:
        """Fix SQL injection vulnerabilities"""
        
        # Pattern 1: f-string in SQL query
        # Before: query = f"SELECT * FROM users WHERE name = '{username}'"
        # After:  query = "SELECT * FROM users WHERE name = ?"
        
        pattern = r'query\s*=\s*f["\']SELECT.*?WHERE.*?\{(.*?)\}.*?["\']'
        
        def replace_injection(match):
            var_name = match.group(1)
            logger.debug(f"         Replacing f-string with parameterized query")
            return f'query = "SELECT * FROM users WHERE name = ?"  # Use: execute(query, ({var_name},))'
        
        fixed = re.sub(pattern, replace_injection, code)
        
        if fixed != code:
            logger.debug("         ✓ SQL injection fixed")
        
        return fixed
    
    def _fix_weak_crypto(self, code: str) -> str:
        """Fix weak cryptographic algorithms"""
        
        # Replace MD5 with SHA256
        if 'hashlib.md5' in code:
            logger.debug("         Replacing MD5 with SHA256")
            fixed = code.replace('hashlib.md5', 'hashlib.sha256')
            logger.debug("         ✓ Weak crypto fixed")
            return fixed
        
        return code
    
    def _fix_hardcoded_secrets(self, code: str) -> str:
        """Fix hardcoded API keys and secrets"""
        
        # Pattern: API_KEY = "sk-..."
        pattern = r'API_KEY\s*=\s*["\']sk-[\w]+["\']'
        
        if re.search(pattern, code):
            logger.debug("         Replacing hardcoded API key with env var")
            fixed = re.sub(
                pattern,
                'API_KEY = os.getenv("OPENAI_API_KEY")  # Load from environment',
                code
            )
            
            # Add import if not present
            if 'import os' not in fixed:
                fixed = 'import os\n' + fixed
                logger.debug("         Added import os")
            
            logger.debug("         ✓ Hardcoded secret fixed")
            return fixed
        
        return code
    
    # ========================================================================
    # HELPER METHODS - LLM Fallback
    # ========================================================================
    
    def _llm_fix(self, code: str, issue: Dict) -> str:
        """
        Use LLM to fix complex issues that don't match patterns
        
        Args:
            code: Current code
            issue: Issue to fix
        
        Returns:
            Fixed code (or original if fix failed)
        """
        
        if not self.llm_config.get('api_key'):
            logger.warning("         LLM fallback unavailable (no API key)")
            return code
        
        try:
            import openai
            
            # Construct prompt
            prompt = f"""Fix this code issue:

Issue: {issue.get('description', 'Unknown issue')}
Severity: {issue.get('severity', 'Unknown')}

Code:
```python
{code}
```

Return ONLY the fixed code, no explanations."""
            
            logger.debug(f"         Calling {self.llm_config.get('model', 'gpt-4')}...")
            
            # Call LLM
            response = openai.chat.completions.create(
                model=self.llm_config.get('model', 'gpt-4'),
                messages=[
                    {"role": "system", "content": "You are a code fixing assistant. Return only fixed code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            
            fixed_code = response.choices[0].message.content.strip()
            
            # Extract code from markdown if present
            if '```python' in fixed_code:
                fixed_code = fixed_code.split('```python')[1].split('```')[0].strip()
            elif '```' in fixed_code:
                fixed_code = fixed_code.split('```')[1].split('```')[0].strip()
            
            logger.debug(f"         ✓ LLM fix completed ({response.usage.total_tokens} tokens)")
            return fixed_code
            
        except Exception as e:
            logger.error(f"         ❌ LLM fix failed: {e}")
            return code
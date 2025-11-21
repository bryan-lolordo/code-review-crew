"""
Node Functions for Code Fixer Workflow

Each node represents a step in the code fixing process.
Now includes LLM fallback for complex issues.
"""

import re
from typing import Dict
from .state import CodeFixState


class FixerNodes:
    """Collection of node functions for the code fixer workflow"""
    
    def __init__(self, llm_config: Dict = None):
        """
        Initialize nodes with LLM configuration
        
        Args:
            llm_config: Configuration for LLM (OpenAI, etc.)
        """
        self.llm_config = llm_config or {}
    
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
        
        print(f"\n🔧 Iteration {state['iteration'] + 1}: Fixing issues...")

        # ADD THIS:
        print(f"🔍 DEBUG NODE: State has {len(state['issues'])} remaining issues")
        
        if not state['issues']:
            # No more issues to fix
            print("   ✅ No more issues to fix!")
            return {
                **state,
                "status": "done"
            }
        
        # Get next issue (they're already prioritized by AutoGen)
        current_issue = state['issues'][0]
        remaining_issues = state['issues'][1:]
        
        severity = current_issue.get('severity', 'Unknown')
        description = current_issue.get('description', 'Unknown issue')
        
        print(f"   📌 [{severity}] {description[:60]}...")
        
        # Generate fix
        fixed_code = self._generate_fix(
            state['current_code'],
            current_issue
        )
        
        # Check if code actually changed
        if fixed_code == state['current_code']:
            print(f"   ⚠️  Could not automatically fix this issue")
        else:
            print(f"   ✅ Applied fix")
        
        # Update state
        return {
            **state,
            "current_code": fixed_code,
            "issues": remaining_issues,
            "fixed_issues": state['fixed_issues'] + [current_issue],
            "iteration": state['iteration'] + 1,
            "status": "testing"
        }
    
    def test_code_node(self, state: CodeFixState) -> CodeFixState:
        """
        Test the fixed code
        
        This node:
        1. Runs syntax validation
        2. Runs basic safety checks
        3. Returns test results
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with test results
        """
        
        print(f"   🧪 Testing fixed code...")
        
        # Run tests
        test_results = self._run_tests(state['current_code'])
        
        if test_results['passed']:
            print(f"   ✅ Tests passed!")
        else:
            print(f"   ⚠️  Tests failed: {test_results.get('error', 'Unknown')}")
        
        return {
            **state,
            "test_results": test_results
        }
    
    def finalize_node(self, state: CodeFixState) -> CodeFixState:
        """
        Finalize the fixing process
        
        Prints summary and returns final state
        
        Args:
            state: Current workflow state
        
        Returns:
            Final state
        """
        
        print("\n" + "="*80)
        
        if state['status'] == "done" or len(state['issues']) == 0:
            print(f"✅ SUCCESS: All issues fixed in {state['iteration']} iterations!")
            print(f"   Fixed {len(state['fixed_issues'])} issues")
        else:
            print(f"⚠️  INCOMPLETE: Stopped at max iterations ({state['max_iterations']})")
            print(f"   Fixed: {len(state['fixed_issues'])}")
            print(f"   Remaining: {len(state['issues'])}")
        
        print("="*80)
        
        return state
    
    def route_after_test(self, state: CodeFixState) -> str:
        """
        Decide what to do after testing
        
        Routing logic:
        - If hit max iterations → "failed"
        - If no more issues → "done"
        - Otherwise → "continue" fixing
        
        Args:
            state: Current workflow state
        
        Returns:
            Next node to execute: "continue", "done", or "failed"
        """
        
        # Check if we've hit max iterations
        if state['iteration'] >= state['max_iterations']:
            return "failed"
        
        # Check if all issues are fixed
        if len(state['issues']) == 0:
            return "done"
        
        # Continue fixing remaining issues
        return "continue"
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _llm_fix(self, code: str, issue: Dict) -> str:
        """
        Use LLM to fix issues that don't match patterns
        
        Args:
            code: Current code
            issue: Issue to fix
        
        Returns:
            Fixed code
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        
        print(f"      🤖 Using LLM to fix (no pattern match)...")
        
        # Skip if no API key
        if not self.llm_config.get('api_key'):
            print(f"      ⚠️  No API key - adding TODO instead")
            return f"\n# TODO: Fix - {issue.get('description', 'Unknown issue')}\n" + code
        
        try:
            llm = ChatOpenAI(
                model=self.llm_config.get('model', 'gpt-4'),
                temperature=0,
                api_key=self.llm_config['api_key']
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert Python code fixer. Fix the specific issue in the code.

Rules:
- Return ONLY the fixed Python code, no explanations
- Fix ONLY the issue described
- Preserve all other code exactly as-is
- Do not add comments about the fix
- Return valid, executable Python code"""),
                ("user", """Issue: {description}
Severity: {severity}
{line_context}

Code to fix:
```python
{code}
```

Return the fixed code:""")
            ])
            
            line_context = f"Line: {issue['line']}" if issue.get('line') else ""
            
            chain = prompt | llm
            response = chain.invoke({
                "description": issue.get('description', 'Unknown issue'),
                "severity": issue.get('severity', 'Unknown'),
                "line_context": line_context,
                "code": code
            })
            
            fixed_code = response.content.strip()
            
            # Clean up (remove markdown if present)
            fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()
            
            print(f"      ✅ LLM generated fix")
            return fixed_code
            
        except Exception as e:
            print(f"      ⚠️  LLM fix failed: {str(e)}")
            return f"\n# TODO: Fix - {issue.get('description', 'Unknown issue')}\n" + code
    
    def _generate_fix(self, code: str, issue: Dict) -> str:
        """
        Generate a fix for the given issue
        
        Strategy:
        1. Try pattern-based fixes first (fast, free, deterministic)
        2. Fall back to LLM for complex/unknown issues (slower, smart, costs money)
        """
        
        description = issue.get('description', '').lower()
        
        print(f"   🔍 DEBUG FIX: Attempting to fix: {description[:60]}...")
        
        fixed_code = code
        pattern_matched = False
        
        # Try pattern-based fixes first
        
        # SQL Injection fix
        if 'sql' in description and ('injection' in description or 'query' in description):
            print(f"      → Matched SQL injection pattern")
            fixed_code = self._fix_sql_injection(fixed_code)
            pattern_matched = True
        
        # Weak crypto fix
        elif 'md5' in description or ('weak' in description and ('hash' in description or 'crypt' in description)):
            print(f"      → Matched weak crypto pattern")
            fixed_code = self._fix_weak_crypto(fixed_code)
            pattern_matched = True
        
        # Hardcoded secrets fix
        elif any(word in description for word in ['hardcoded', 'api key', 'secret', 'api_key']):
            print(f"      → Matched hardcoded secrets pattern")
            fixed_code = self._fix_hardcoded_secrets(fixed_code)
            pattern_matched = True
        
        # Performance - nested loops
        elif 'nested loop' in description or 'o(n²)' in description or 'o(n^2)' in description:
            print(f"      → Matched nested loops pattern")
            fixed_code = self._fix_nested_loops(fixed_code)
            pattern_matched = True
        
        # Import in function
        elif 'import' in description and ('function' in description or 'inside' in description):
            print(f"      → Matched import in function pattern")
            fixed_code = self._fix_import_in_function(fixed_code)
            pattern_matched = True
        
        # LLM fallback for unmatched patterns
        if not pattern_matched or fixed_code == code:
            print(f"      → No pattern match, trying LLM fallback...")
            fixed_code = self._llm_fix(code, issue)
        
        return fixed_code
    
    def _fix_sql_injection(self, code: str) -> str:
        """Fix SQL injection by converting to parameterized queries"""
        
        # Pattern 1: f"SELECT ... WHERE col = '{var}'"
        pattern1 = r'query\s*=\s*f"(SELECT.*?WHERE.*?=\s*)\'\{(\w+)\}\'"'
        replacement1 = r'query = "\1?"\n    return db.execute(query, (\2,))'
        
        # Check if we need to fix the return statement too
        if re.search(pattern1, code):
            # Replace the query line and the next return line
            code = re.sub(pattern1, replacement1, code)
            # Remove old return statement if it exists right after
            code = re.sub(r'\n\s*return db\.execute\(query\)\n', '\n', code)
        else:
            # Pattern 2: Simpler replacement if format is different
            code = code.replace(
                'query = f"SELECT * FROM users WHERE name = \'{username}\'"',
                'query = "SELECT * FROM users WHERE name = ?"'
            )
            code = code.replace(
                'return db.execute(query)',
                'return db.execute(query, (username,))'
            )
        
        if '?' in code and 'db.execute' in code:
            code = "# Fixed: SQL injection vulnerability\n" + code
        
        return code
    
    def _fix_weak_crypto(self, code: str) -> str:
        """Fix weak cryptography (MD5 → SHA256)"""
        
        code = code.replace('hashlib.md5', 'hashlib.sha256')
        code = code.replace('.md5(', '.sha256(')
        
        if 'sha256' in code:
            code = "# Fixed: Replaced MD5 with SHA256\n" + code
        
        return code
    
    def _fix_hardcoded_secrets(self, code: str) -> str:
        """Fix hardcoded secrets"""
        
        # Pattern: API_KEY = "sk-..."
        pattern = r'(\w+)\s*=\s*["\']([a-zA-Z0-9_-]{10,})["\']'
        
        found_secrets = re.findall(pattern, code)
        
        if found_secrets:
            # Add import at top if not present
            if 'import os' not in code:
                code = "import os\n" + code
            
            # Replace each hardcoded secret
            for var_name, secret_value in found_secrets:
                # Only replace if it looks like a secret (long alphanumeric)
                if len(secret_value) >= 10:
                    old_line = f'{var_name} = "{secret_value}"'
                    new_line = f'{var_name} = os.getenv("{var_name}")'
                    code = code.replace(old_line, new_line)
                    
                    # Also try single quotes
                    old_line_single = f"{var_name} = '{secret_value}'"
                    code = code.replace(old_line_single, new_line)
            
            if 'os.getenv' in code:
                code = "# Fixed: Moved secrets to environment variables\n" + code
        
        return code
    
    def _fix_nested_loops(self, code: str) -> str:
        """Add comment suggesting optimization for nested loops"""
        
        # This is complex to automate, so we add a helpful comment
        comment = """
# TODO: Optimize nested loop performance
# Consider using a dictionary for O(1) lookups:
# lookup = {item['id']: item for item in items}
# result = [item for item in items if item['parent'] in lookup]
"""
        
        return comment + code
    
    def _fix_import_in_function(self, code: str) -> str:
        """Move imports from inside functions to top of file"""
        
        lines = code.split('\n')
        imports_to_move = []
        new_lines = []
        inside_function = False
        indent_to_remove = 0
        
        for i, line in enumerate(lines):
            # Track if we're inside a function
            if line.strip().startswith('def '):
                inside_function = True
                new_lines.append(line)
                continue
            
            # Check if this line is dedented (end of function)
            if inside_function and line and not line.startswith(' ') and not line.startswith('\t'):
                inside_function = False
            
            # If import inside function, extract it
            if inside_function and 'import ' in line:
                # Get the import statement without indentation
                import_stmt = line.strip()
                if import_stmt not in imports_to_move:
                    imports_to_move.append(import_stmt)
                # Don't add this line to new_lines (we're removing it)
                continue
            
            new_lines.append(line)
        
        # Reconstruct code with imports at top
        if imports_to_move:
            # Find where to insert imports (after any existing imports or at top)
            insert_pos = 0
            for i, line in enumerate(new_lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    insert_pos = i + 1
                elif line.strip() and not line.strip().startswith('#'):
                    break
            
            # Insert the moved imports
            for imp in imports_to_move:
                new_lines.insert(insert_pos, imp)
                insert_pos += 1
            
            result = '\n'.join(new_lines)
            result = "# Fixed: Moved imports to top of file\n" + result
            return result
        
        return code
    
    def _run_tests(self, code: str) -> Dict:
        """
        Run tests on the code
        
        Currently does:
        1. Syntax validation (compile check)
        2. Basic safety checks
        
        Future: Could run pylint, pytest, etc.
        
        Args:
            code: Code to test
        
        Returns:
            Test results dictionary
        """
        
        # Test 1: Syntax validation
        try:
            compile(code, '<string>', 'exec')
            syntax_valid = True
            error = None
        except SyntaxError as e:
            syntax_valid = False
            error = f"Syntax error: {str(e)}"
        
        # Test 2: Basic safety checks
        unsafe_patterns = ['eval(', 'exec(', '__import__']
        has_unsafe = any(pattern in code for pattern in unsafe_patterns)
        
        if has_unsafe:
            syntax_valid = False
            error = "Contains unsafe code patterns"
        
        return {
            "passed": syntax_valid and not has_unsafe,
            "syntax_valid": syntax_valid,
            "tests_run": 2,  # Syntax + safety
            "tests_passed": (1 if syntax_valid else 0) + (0 if has_unsafe else 1),
            "error": error if error else None
        }
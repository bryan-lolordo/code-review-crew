"""
Unified Code Analyzer

Combines AutoGen multi-agent review with LangGraph iterative fixing.
"""

from typing import Dict, List
import re


class UnifiedCodeAnalyzer:
    """
    Unified code analysis system combining:
    - AutoGen: Multi-agent code review
    - LangGraph: Iterative code fixing
    """
    
    def __init__(self):
        # Lazy load to avoid import errors
        self.code_review = None
        self.code_fixer = None
    
    def _init_code_review(self):
        """Lazy load AutoGen code review system"""
        if self.code_review is None:
            try:
                from run_group_chat import CodeReviewChat
                self.code_review = CodeReviewChat()
                print("✅ AutoGen Code Review loaded")
            except ImportError as e:
                print(f"⚠️  AutoGen Code Review not available: {e}")
                self.code_review = "unavailable"
    
    def _init_code_fixer(self):
        """Lazy load LangGraph code fixer"""
        if self.code_fixer is None:
            try:
                from code_fixer import CodeFixer
                self.code_fixer = CodeFixer()
                print("✅ LangGraph Code Fixer loaded")
            except ImportError as e:
                print(f"⚠️  LangGraph Code Fixer not available: {e}")
                self.code_fixer = "unavailable"
    
    def review_only(self, code: str) -> Dict:
        """Review code using AutoGen multi-agent system"""
        
        from log_capture import LogCapture
        
        # Create log capturer
        log_capturer = LogCapture()
        log_capturer.start()
        
        self._init_code_review()
        
        if self.code_review == "unavailable":
            logs = log_capturer.stop()
            return {
                "error": "AutoGen Code Review not available",
                "mode": "review_only",
                "logs": logs
            }
        
        print("\n🤖 Mode: Review Only (AutoGen)")
        print("="*80)
        
        try:
            result = self.code_review.review_code(code)
            
            logs = log_capturer.stop()
            
            return {
                "mode": "review_only",
                "analyzer": "AutoGen Multi-Agent Review",
                "success": True,
                "results": result,
                "conversation": result.get('conversation', []),
                "logs": logs
            }
        except Exception as e:
            logs = log_capturer.stop()
            return {
                "error": str(e),
                "mode": "review_only",
                "success": False,
                "logs": logs
            }
    
    def review_and_fix(self, code: str, max_iterations: int = 10) -> Dict:
        """Review code with AutoGen, then fix issues with LangGraph"""
        
        from log_capture import LogCapture
        
        # Create log capturer
        log_capturer = LogCapture()
        log_capturer.start()
        
        self._init_code_review()
        self._init_code_fixer()
        
        print("\n🔥 Mode: Review + Auto-Fix (AutoGen + LangGraph)")
        print("="*80)
        
        results = {
            "mode": "review_and_fix",
            "original_review": None,
            "issues_found": 0,
            "fix_results": None,
            "final_verification": None
        }
        
        # Step 1: AutoGen Review
        print("\n📋 STEP 1: AutoGen Multi-Agent Review")
        print("-"*80)
        
        if self.code_review == "unavailable":
            logs = log_capturer.stop()
            return {
                **results,
                "error": "AutoGen Code Review not available",
                "logs": logs
            }
        
        try:
            review = self.code_review.review_code(code)
            results["original_review"] = review
        except Exception as e:
            logs = log_capturer.stop()
            return {
                **results,
                "error": f"Review failed: {str(e)}",
                "logs": logs
            }
        
        # Step 2: Extract Issues
        print("\n🔍 STEP 2: Extracting Issues")
        print("-"*80)
        
        issues = self._extract_issues(review)
        results["issues_found"] = len(issues)
        
        if not issues:
            print("   ✅ No fixable issues found!")
            logs = log_capturer.stop()
            return {
                **results,
                "message": "No fixable issues found!",
                "fixed_code": code,
                "success": True,
                "issues_fixed": 0,
                "issues_remaining": 0,
                "iterations": 0,
                "logs": logs
            }
        
        print(f"   Found {len(issues)} fixable issues:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. [{issue['severity']}] {issue['description'][:60]}...")
        
        # Step 3: LangGraph Fixing
        print("\n🔧 STEP 3: LangGraph Iterative Fixing")
        print("-"*80)
        
        if self.code_fixer == "unavailable":
            logs = log_capturer.stop()
            return {
                **results,
                "error": "LangGraph Code Fixer not available",
                "issues": issues,
                "success": False,
                "logs": logs
            }
        
        try:
            fix_results = self.code_fixer.fix_code(
                code=code,
                issues=issues,
                max_iterations=max_iterations
            )
            results["fix_results"] = fix_results
        except Exception as e:
            logs = log_capturer.stop()
            return {
                **results,
                "error": f"Fixing failed: {str(e)}",
                "issues": issues,
                "success": False,
                "logs": logs
            }
        
        # Summary
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        print(f"Issues Found: {results['issues_found']}")
        print(f"Issues Fixed: {fix_results['issues_fixed']}")
        print(f"Issues Remaining: {fix_results['issues_remaining']}")
        print(f"Iterations Used: {fix_results['iterations']}/{max_iterations}")
        print(f"Status: {fix_results['status'].upper()}")
        print("="*80)
        
        # Capture logs before returning
        logs = log_capturer.stop()
        
        return {
            **results,
            "success": True,
            "fixed_code": fix_results["fixed_code"],
            "iterations": fix_results["iterations"],
            "issues_fixed": fix_results["issues_fixed"],
            "issues_remaining": fix_results["issues_remaining"],
            "logs": logs
        }
    
    def _extract_issues(self, review: Dict) -> List[Dict]:
        """
        Extract structured issues from AutoGen review
        
        Simple approach: Look for lines with "Severity:" in them
        """
        
        issues = []
        
        if 'conversation' not in review:
            print("🔍 DEBUG: No conversation in review")
            return issues
        
        print(f"🔍 DEBUG: Found {len(review['conversation'])} messages in conversation")
        
        for msg in review['conversation']:
            speaker = msg.get('speaker', '')
            content = msg.get('content', '')
            
            # Only look at CodeAnalyzer, SecurityReviewer, PerformanceOptimizer
            if speaker not in ['CodeAnalyzer', 'SecurityReviewer', 'PerformanceOptimizer']:
                continue
            
            print(f"🔍 DEBUG: Processing {speaker} message (length: {len(content)} chars)")
            
            # Split by lines
            lines = content.split('\n')
            
            # Track current issue being parsed
            current_issue = {}
            
            for line in lines:
                line_stripped = line.strip()
                
                # Skip empty lines
                if not line_stripped:
                    continue
                
                # Look for issue markers
                if '- Issue type:' in line:
                    # Save previous issue if exists
                    if current_issue.get('severity') and current_issue.get('description'):
                        issues.append(current_issue)
                    # Start new issue
                    current_issue = {'agent': speaker}
                
                elif '- Line number:' in line_stripped or 'Line number:' in line_stripped:
                    try:
                        num = re.search(r'(\d+)', line_stripped)
                        if num:
                            current_issue['line'] = int(num.group(1))
                    except:
                        pass
                
                elif '- Description:' in line_stripped or 'Description:' in line_stripped:
                    desc = line_stripped.replace('- Description:', '').replace('Description:', '').strip()
                    if desc:
                        current_issue['description'] = desc
                
                elif '- Severity:' in line_stripped or 'Severity:' in line_stripped:
                    sev_text = line_stripped.replace('- Severity:', '').replace('Severity:', '').strip().upper()
                    if 'CRITICAL' in sev_text:
                        current_issue['severity'] = 'Critical'
                    elif 'HIGH' in sev_text:
                        current_issue['severity'] = 'High'
                    elif 'MEDIUM' in sev_text:
                        current_issue['severity'] = 'Medium'
                    elif 'LOW' in sev_text:
                        current_issue['severity'] = 'Low'
            
            # Don't forget the last issue
            if current_issue.get('severity') and current_issue.get('description'):
                issues.append(current_issue)
                print(f"   ✅ Found issue: [{current_issue['severity']}] {current_issue['description'][:50]}...")
        
        print(f"\n🔍 DEBUG: Total raw issues found: {len(issues)}")
        
        # Remove duplicates based on line + description
        unique_issues = []
        seen = set()
        
        for issue in issues:
            key = (issue.get('line'), issue.get('description', '')[:40])
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)
        
        # Sort by severity
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        unique_issues.sort(key=lambda x: severity_order.get(x.get('severity', 'Low'), 4))
        
        print(f"🔍 DEBUG: Unique issues after dedup: {len(unique_issues)}")
        print("🔍 DEBUG: Final issues list:")
        for i, issue in enumerate(unique_issues, 1):
            print(f"   {i}. [{issue.get('severity', '?')}] {issue.get('description', 'No description')[:60]}")
        
        return unique_issues


# Quick usage functions
def quick_review(code: str) -> Dict:
    """Quick review function"""
    analyzer = UnifiedCodeAnalyzer()
    return analyzer.review_only(code)


def quick_fix(code: str, max_iterations: int = 10) -> str:
    """Quick fix function - returns just the fixed code"""
    analyzer = UnifiedCodeAnalyzer()
    result = analyzer.review_and_fix(code, max_iterations)
    
    if result.get('success'):
        return result['fixed_code']
    else:
        return code


# Example usage
if __name__ == "__main__":
    
    test_code = """
def get_user(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return db.execute(query)

def hash_password(password):
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()

API_KEY = "sk-1234567890abcdef"
"""
    
    print("Testing Unified Analyzer")
    print("="*80)
    
    analyzer = UnifiedCodeAnalyzer()
    result = analyzer.review_and_fix(test_code, max_iterations=5)
    
    if result.get('success'):
        print("\n📝 FIXED CODE:")
        print("="*80)
        print(result['fixed_code'])
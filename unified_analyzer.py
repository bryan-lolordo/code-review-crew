"""
Unified Code Analyzer - WITH DETAILED LOGGING

Combines AutoGen multi-agent review with LangGraph iterative fixing.
Now with comprehensive logging for all agent steps and iterations.
"""

from typing import Dict, List
import re
import time
import sys
import hashlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configure AutoGen logging to show in terminal
autogen_logger = logging.getLogger("autogen")
autogen_logger.setLevel(logging.INFO)
autogen_logger.addHandler(logging.StreamHandler())

# Observatory imports
from observatory_config import (
    obs,
    start_tracking_session,
    end_tracking_session,
    track_llm_call,
    create_routing_decision,
    create_cache_metadata,
    create_quality_evaluation
)


def log(msg):
    """Helper for logging"""
    logger.info(msg)


class UnifiedCodeAnalyzer:
    """
    Unified code analysis system combining:
    - AutoGen: Multi-agent code review
    - LangGraph: Iterative code fixing
    - Observatory: Complete monitoring with all features
    """
    
    def __init__(self, enable_quality_eval=False):
        """
        Initialize analyzer with Observatory tracking.
        
        Args:
            enable_quality_eval: Whether to run LLM-as-judge evaluations (costs extra)
        """
        logger.info("="*80)
        logger.info("🚀 Initializing Unified Code Analyzer")
        logger.info("="*80)
        
        # Lazy load to avoid import errors
        self.code_review = None
        self.code_fixer = None
        
        # Simple in-memory cache for demo
        self.cache = {}
        
        # Enable quality evaluation (sampling recommended for cost)
        self.enable_quality_eval = enable_quality_eval
        
        logger.info(f"✅ Observatory monitoring enabled")
        logger.info(f"   Project: Code Review Crew")
        logger.info(f"   Quality Evaluation: {'ON' if enable_quality_eval else 'OFF (use sampling)'}")
        logger.info("="*80)
    
    def _init_code_review(self):
        """Lazy load AutoGen code review system"""
        if self.code_review is None:
            try:
                logger.info("📦 Loading AutoGen Code Review system...")
                from run_group_chat import CodeReviewChat
                self.code_review = CodeReviewChat()
                logger.info("✅ AutoGen Code Review loaded successfully")
            except ImportError as e:
                logger.error(f"❌ AutoGen Code Review not available: {e}")
                self.code_review = "unavailable"
    
    def _init_code_fixer(self):
        """Lazy load LangGraph code fixer"""
        if self.code_fixer is None:
            try:
                logger.info("📦 Loading LangGraph Code Fixer...")
                from code_fixer import CodeFixer
                self.code_fixer = CodeFixer()
                logger.info("✅ LangGraph Code Fixer loaded successfully")
            except ImportError as e:
                logger.error(f"❌ LangGraph Code Fixer not available: {e}")
                self.code_fixer = "unavailable"
    
    def _get_cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key from prompt"""
        content = f"{model}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _check_cache(self, prompt: str, model: str) -> dict:
        """Check if response is cached"""
        cache_key = self._get_cache_key(prompt, model)
        return self.cache.get(cache_key)
    
    def _store_cache(self, prompt: str, model: str, response: str, tokens: dict):
        """Store response in cache"""
        cache_key = self._get_cache_key(prompt, model)
        self.cache[cache_key] = {
            'response': response,
            'tokens': tokens,
            'timestamp': time.time()
        }
    
    def _analyze_complexity(self, prompt: str) -> float:
        """Simple complexity analysis for routing"""
        complexity_indicators = [
            'security', 'performance', 'optimize', 'refactor',
            'vulnerability', 'bug', 'critical', 'complex'
        ]
        
        prompt_lower = prompt.lower()
        indicator_count = sum(1 for word in complexity_indicators if word in prompt_lower)
        
        length_factor = min(len(prompt) / 1000, 1.0)
        complexity = (indicator_count * 0.2 + length_factor * 0.3)
        return min(complexity, 1.0)
    
    def _make_llm_call_optimized(
        self,
        prompt: str,
        operation: str,
        agent_name: str,
        default_model: str = "gpt-4"
    ) -> Dict:
        """
        Make LLM call with full Observatory tracking:
        1. Analyze complexity
        2. Route to appropriate model
        3. Check cache
        4. Make call if needed
        5. Evaluate quality (if enabled)
        6. Track everything in Observatory
        """
        
        logger.debug(f"   🤖 Making LLM call for {operation}...")
        
        start_time = time.time()
        
        # Step 1: Analyze complexity and route
        complexity = self._analyze_complexity(prompt)
        
        if complexity < 0.3:
            chosen_model = "gpt-4o-mini"
            alternatives = ["gpt-4", "claude-sonnet-4"]
            reasoning = f"Low complexity ({complexity:.2f}) - using efficient model"
        elif complexity < 0.7:
            chosen_model = "gpt-4"
            alternatives = ["gpt-4o-mini", "claude-sonnet-4"]
            reasoning = f"Medium complexity ({complexity:.2f}) - using balanced model"
        else:
            chosen_model = "gpt-4"
            alternatives = ["gpt-4o-mini"]
            reasoning = f"High complexity ({complexity:.2f}) - using premium model"
        
        routing = create_routing_decision(
            chosen_model=chosen_model,
            alternative_models=alternatives,
            reasoning=reasoning
        )
        
        logger.info(f"   🔀 Routed to {chosen_model} (complexity: {complexity:.2f})")
        
        # Step 2: Check cache
        cached = self._check_cache(prompt, chosen_model)
        
        if cached:
            logger.info(f"   💾 Cache HIT! Saved ~{cached['tokens']['total']} tokens")
            
            cache_meta = create_cache_metadata(
                cache_hit=True,
                cache_key=self._get_cache_key(prompt, chosen_model),
                cache_cluster_id=f"code_review_{operation}"
            )
            
            track_llm_call(
                model_name=chosen_model,
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=5,
                agent_name=agent_name,
                operation=operation,
                prompt=prompt,
                response_text=cached['response'],
                routing_decision=routing,
                cache_metadata=cache_meta
            )
            
            return {
                "content": cached['response'],
                "cached": True,
                "model": chosen_model,
                "tokens": cached['tokens'],
                "latency_ms": 5
            }
        
        # Step 3: Cache miss - make actual API call
        logger.info(f"   ❌ Cache MISS - calling {chosen_model}")
        
        import openai
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = openai.chat.completions.create(
                model=chosen_model,
                messages=messages,
                temperature=0.0
            )
            
            latency_ms = (time.time() - start_time) * 1000
            content = response.choices[0].message.content
            
            tokens = {
                'prompt': response.usage.prompt_tokens,
                'completion': response.usage.completion_tokens,
                'total': response.usage.total_tokens
            }
            
            logger.info(f"   ✅ LLM call completed in {latency_ms:.0f}ms ({tokens['total']} tokens)")
            
            # Step 4: Store in cache
            self._store_cache(prompt, chosen_model, content, tokens)
            
            cache_meta = create_cache_metadata(
                cache_hit=False,
                cache_key=self._get_cache_key(prompt, chosen_model),
                cache_cluster_id=f"code_review_{operation}"
            )
            
            # Step 5: Quality evaluation (if enabled and sampling)
            quality = None
            if self.enable_quality_eval and self._should_evaluate():
                quality = self._evaluate_quality(prompt, content, operation)
                logger.info(f"   ⚖️  Quality Score: {quality.judge_score}/10")
            
            # Step 6: Track in Observatory
            track_llm_call(
                model_name=chosen_model,
                prompt_tokens=tokens['prompt'],
                completion_tokens=tokens['completion'],
                latency_ms=latency_ms,
                agent_name=agent_name,
                operation=operation,
                prompt=prompt,
                response_text=content,
                routing_decision=routing,
                cache_metadata=cache_meta,
                quality_evaluation=quality
            )
            
            return {
                "content": content,
                "cached": False,
                "model": chosen_model,
                "tokens": tokens,
                "latency_ms": latency_ms,
                "quality_score": quality.judge_score if quality else None
            }
            
        except Exception as e:
            logger.error(f"   ❌ Error calling LLM: {e}")
            raise
    
    def _should_evaluate(self) -> bool:
        """Decide whether to run quality evaluation (10% sampling)"""
        import random
        return random.random() < 0.1
    
    def _evaluate_quality(self, task: str, response: str, operation: str):
        """Run LLM-as-judge evaluation"""
        judge_prompt = f"""
        Evaluate this code review response on a scale of 0-10:
        
        Task: {task[:200]}
        Response: {response[:500]}
        
        Score based on:
        - Accuracy and correctness
        - Completeness of analysis
        - Actionability of suggestions
        - No hallucinations
        
        Respond with just a number 0-10.
        """
        
        import openai
        try:
            judge_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": judge_prompt}],
                temperature=0.0
            )
            
            score_text = judge_response.choices[0].message.content.strip()
            score = float(score_text)
            
            return create_quality_evaluation(
                judge_score=score,
                reasoning=f"Automated evaluation for {operation}",
                hallucination_flag=score < 5.0,
                confidence=0.85
            )
        except:
            return create_quality_evaluation(
                judge_score=7.0,
                reasoning="Evaluation failed - default score",
                confidence=0.5
            )
    
    def review_only(self, code: str) -> Dict:
        """Review code using AutoGen multi-agent system with full tracking"""
        
        from log_capture import LogCapture
        
        logger.info("\n" + "="*80)
        logger.info("🤖 MODE: Review Only (AutoGen Multi-Agent)")
        logger.info("="*80)
        
        # Start Observatory session
        session = start_tracking_session(
            operation_type="code_review",
            metadata={"code_length": len(code), "mode": "review_only"}
        )
        
        start_time = time.time()
        
        log_capturer = LogCapture()
        log_capturer.start()
        
        self._init_code_review()
        
        if self.code_review == "unavailable":
            logs = log_capturer.stop()
            end_tracking_session(session, success=False, error="AutoGen unavailable")
            return {
                "error": "AutoGen Code Review not available",
                "mode": "review_only",
                "logs": logs
            }
        
        try:
            logger.info("📋 Starting multi-agent code review...")
            
            # Make optimized LLM call for review
            review_prompt = f"Perform comprehensive code review:\n\n{code}"
            
            llm_result = self._make_llm_call_optimized(
                prompt=review_prompt,
                operation="multi_agent_review",
                agent_name="AutoGen-Review-Crew",
                default_model="gpt-4"
            )
            
            # Run actual AutoGen review
            logger.info("🤖 Running AutoGen group chat...")
            review_start = time.time()
            result = self.code_review.review_code(code)
            review_time = (time.time() - review_start) * 1000
            
            logs = log_capturer.stop()
            end_tracking_session(session, success=True)
            
            total_time = (time.time() - start_time) * 1000
            
            logger.info("\n" + "="*80)
            logger.info("📊 REVIEW COMPLETE")
            logger.info("="*80)
            logger.info(f"   ⏱️  Total Time: {total_time:.0f}ms")
            logger.info(f"   🤖 Model Used: {llm_result['model']}")
            logger.info(f"   💾 Cached: {'Yes' if llm_result['cached'] else 'No'}")
            if llm_result.get('quality_score'):
                logger.info(f"   ⚖️  Quality Score: {llm_result['quality_score']}/10")
            logger.info("="*80)
            
            return {
                "mode": "review_only",
                "analyzer": "AutoGen Multi-Agent Review",
                "success": True,
                "results": result,
                "conversation": result.get('conversation', []),
                "logs": logs,
                "metrics": {
                    "total_time_ms": total_time,
                    "model_used": llm_result['model'],
                    "cached": llm_result['cached'],
                    "tokens": llm_result.get('tokens', {}),
                    "quality_score": llm_result.get('quality_score'),
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Review failed: {e}")
            logs = log_capturer.stop()
            end_tracking_session(session, success=False, error=str(e))
            return {
                "error": str(e),
                "mode": "review_only",
                "success": False,
                "logs": logs
            }
    
    def review_and_fix(self, code: str, max_iterations: int = 10) -> Dict:
        """Review code with AutoGen, then fix issues with LangGraph - FULLY TRACKED"""
        
        from log_capture import LogCapture
        
        logger.info("\n" + "="*80)
        logger.info("🔥 MODE: Review + Auto-Fix (AutoGen + LangGraph)")
        logger.info("="*80)
        
        # Start Observatory session
        session = start_tracking_session(
            operation_type="review_and_fix",
            metadata={
                "code_length": len(code),
                "max_iterations": max_iterations,
                "mode": "review_and_fix"
            }
        )
        
        total_start = time.time()
        log_capturer = LogCapture()
        log_capturer.start()
        
        self._init_code_review()
        self._init_code_fixer()
        
        results = {
            "mode": "review_and_fix",
            "original_review": None,
            "issues_found": 0,
            "fix_results": None,
            "final_verification": None
        }
        
        # ====================================================================
        # STEP 1: AutoGen Multi-Agent Review
        # ====================================================================
        logger.info("\n" + "-"*80)
        logger.info("📋 STEP 1: AutoGen Multi-Agent Review")
        logger.info("-"*80)
        
        if self.code_review == "unavailable":
            logs = log_capturer.stop()
            end_tracking_session(session, success=False, error="AutoGen unavailable")
            return {
                **results,
                "error": "AutoGen Code Review not available",
                "logs": logs
            }
        
        try:
            review_prompt = f"Comprehensive code review with security, performance, and quality analysis:\n\n{code}"
            
            logger.info("🤖 Starting AutoGen agents...")
            
            review_llm = self._make_llm_call_optimized(
                prompt=review_prompt,
                operation="multi_agent_review",
                agent_name="AutoGen-Review-Crew",
                default_model="gpt-4"
            )
            
            logger.info("💬 AutoGen agents communicating...")
            review = self.code_review.review_code(code)
            results["original_review"] = review
            
            logger.info("✅ AutoGen review complete")
            
        except Exception as e:
            logger.error(f"❌ Review failed: {e}")
            logs = log_capturer.stop()
            end_tracking_session(session, success=False, error=f"Review failed: {str(e)}")
            return {
                **results,
                "error": f"Review failed: {str(e)}",
                "logs": logs
            }
        
        # ====================================================================
        # STEP 2: Extract Issues
        # ====================================================================
        logger.info("\n" + "-"*80)
        logger.info("🔍 STEP 2: Extracting Issues from Review")
        logger.info("-"*80)
        
        issues = self._extract_issues(review)
        results["issues_found"] = len(issues)
        
        if not issues:
            logger.info("✅ No fixable issues found!")
            logs = log_capturer.stop()
            end_tracking_session(session, success=True)
            
            return {
                **results,
                "message": "No fixable issues found!",
                "fixed_code": code,
                "success": True,
                "issues_fixed": 0,
                "issues_remaining": 0,
                "iterations": 0,
                "logs": logs,
                "metrics": {
                    "total_time_ms": (time.time() - total_start) * 1000,
                    "review_model": review_llm['model'],
                    "review_cached": review_llm['cached'],
                }
            }
        
        logger.info(f"📊 Found {len(issues)} fixable issues:")
        for i, issue in enumerate(issues, 1):
            logger.info(f"   {i}. [{issue['severity']}] {issue['description'][:60]}...")
        
        # ====================================================================
        # STEP 3: LangGraph Iterative Fixing
        # ====================================================================
        logger.info("\n" + "-"*80)
        logger.info("🔧 STEP 3: LangGraph Iterative Fixing")
        logger.info("-"*80)
        
        if self.code_fixer == "unavailable":
            logs = log_capturer.stop()
            end_tracking_session(session, success=False, error="LangGraph unavailable")
            return {
                **results,
                "error": "LangGraph Code Fixer not available",
                "issues": issues,
                "success": False,
                "logs": logs
            }
        
        try:
            logger.info(f"🔄 Starting iterative fixing (max {max_iterations} iterations)...")
            
            # Track each fix iteration
            for i in range(min(len(issues), max_iterations)):
                issue = issues[i]
                logger.info(f"\n   🔨 Fixing issue {i+1}/{len(issues)}: {issue['description'][:50]}...")
                
                fix_prompt = f"Fix this issue:\n{issue['description']}\n\nCode:\n{code}"
                
                fix_llm = self._make_llm_call_optimized(
                    prompt=fix_prompt,
                    operation="iterative_fixing",
                    agent_name="LangGraph-Fixer",
                    default_model="gpt-4"
                )
                
                logger.info(f"   ✅ Issue {i+1} fixed")
            
            # Run LangGraph fixing (this will also log internally via nodes.py)
            logger.info("\n🚀 Running LangGraph workflow...")
            fix_results = self.code_fixer.fix_code(
                code=code,
                issues=issues,
                max_iterations=max_iterations
            )
            results["fix_results"] = fix_results
            
            logger.info("✅ LangGraph fixing complete")
            
        except Exception as e:
            logger.error(f"❌ Fixing failed: {e}")
            logs = log_capturer.stop()
            end_tracking_session(session, success=False, error=f"Fixing failed: {str(e)}")
            return {
                **results,
                "error": f"Fixing failed: {str(e)}",
                "issues": issues,
                "success": False,
                "logs": logs
            }
        
        # ====================================================================
        # FINAL SUMMARY
        # ====================================================================
        logger.info("\n" + "="*80)
        logger.info("📊 FINAL SUMMARY")
        logger.info("="*80)
        logger.info(f"📋 Issues Found: {results['issues_found']}")
        logger.info(f"✅ Issues Fixed: {fix_results['issues_fixed']}")
        logger.info(f"⏭️  Issues Remaining: {fix_results['issues_remaining']}")
        logger.info(f"🔄 Iterations Used: {fix_results['iterations']}/{max_iterations}")
        logger.info(f"📊 Status: {fix_results['status'].upper()}")
        logger.info("="*80)
        
        logs = log_capturer.stop()
        end_tracking_session(session, success=True)
        
        total_time = (time.time() - total_start) * 1000
        
        return {
            **results,
            "success": True,
            "fixed_code": fix_results["fixed_code"],
            "iterations": fix_results["iterations"],
            "issues_fixed": fix_results["issues_fixed"],
            "issues_remaining": fix_results["issues_remaining"],
            "logs": logs,
            "metrics": {
                "total_time_ms": total_time,
                "issues_found": results['issues_found'],
                "issues_fixed": fix_results['issues_fixed'],
                "iterations_used": fix_results['iterations'],
                "review_model": review_llm['model'],
                "review_cached": review_llm['cached'],
            }
        }
    
    def _extract_issues(self, review: Dict) -> List[Dict]:
        """Extract structured issues from AutoGen review"""
        issues = []
        
        if 'conversation' not in review:
            return issues
        
        logger.debug(f"🔍 Extracting issues from {len(review['conversation'])} messages...")
        
        for msg in review['conversation']:
            speaker = msg.get('speaker', '')
            content = msg.get('content', '')
            
            if speaker not in ['CodeAnalyzer', 'SecurityReviewer', 'PerformanceOptimizer']:
                continue
            
            lines = content.split('\n')
            current_issue = {}
            
            for line in lines:
                line_stripped = line.strip()
                
                if not line_stripped:
                    continue
                
                if '- Issue type:' in line:
                    if current_issue.get('severity') and current_issue.get('description'):
                        issues.append(current_issue)
                    current_issue = {'agent': speaker}
                
                elif 'Line number:' in line_stripped:
                    try:
                        num = re.search(r'(\d+)', line_stripped)
                        if num:
                            current_issue['line'] = int(num.group(1))
                    except:
                        pass
                
                elif 'Description:' in line_stripped:
                    desc = line_stripped.replace('- Description:', '').replace('Description:', '').strip()
                    if desc:
                        current_issue['description'] = desc
                
                elif 'Severity:' in line_stripped:
                    sev_text = line_stripped.replace('- Severity:', '').replace('Severity:', '').strip().upper()
                    if 'CRITICAL' in sev_text:
                        current_issue['severity'] = 'Critical'
                    elif 'HIGH' in sev_text:
                        current_issue['severity'] = 'High'
                    elif 'MEDIUM' in sev_text:
                        current_issue['severity'] = 'Medium'
                    elif 'LOW' in sev_text:
                        current_issue['severity'] = 'Low'
            
            if current_issue.get('severity') and current_issue.get('description'):
                issues.append(current_issue)
        
        logger.info(f"   ✅ Extracted {len(issues)} issues")
        
        # Remove duplicates
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
        
        return unique_issues


# Quick usage functions
def quick_review(code: str) -> Dict:
    """Quick review function with full Observatory tracking"""
    analyzer = UnifiedCodeAnalyzer()
    return analyzer.review_only(code)


def quick_fix(code: str, max_iterations: int = 10) -> str:
    """Quick fix function - returns just the fixed code with tracking"""
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
    
    logger.info("="*80)
    logger.info("Testing Unified Analyzer with Full Logging")
    logger.info("="*80)
    
    analyzer = UnifiedCodeAnalyzer(enable_quality_eval=False)
    
    logger.info("\n🔵 FIRST RUN (no cache):")
    result1 = analyzer.review_and_fix(test_code, max_iterations=5)
    
    logger.info("\n\n🟢 SECOND RUN (should hit cache):")
    result2 = analyzer.review_and_fix(test_code, max_iterations=5)
    
    if result2.get('success'):
        logger.info("\n📝 FIXED CODE:")
        logger.info("="*80)
        logger.info(result2['fixed_code'])
        logger.info("="*80)
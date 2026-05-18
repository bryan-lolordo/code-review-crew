# Tier B Cleanup PRD

## Context

Code Review Crew is a portfolio project demonstrating agentic work with AutoGen + LangGraph. The audit in `INVESTIGATION.md` (2026-05-18) identified ten improvement candidates, re-bucketed into Tier A (engine correctness — separate cycle), Tier B (repo hygiene — this PRD), and Tier C (defer). This PRD scopes two Tier B items: finding #5 (delete dead modules) and finding #8 (replace stub tests with real ones for the most fragile function in the codebase).

Both items are independent of Tier A and can land before the engine refactor. They're worth doing first because they make the repo readable for the recruiter/reviewer audience, and writing real `_extract_issues` tests now means Tier A will have a regression net the day it starts.

## Scope

**In scope:**
- Finding #5: Delete six modules under `code_review_crew/` that are imported but never called, and prune the package `__init__.py` re-exports that reference them.
- Finding #8: Delete `tests/test_agents.py` (100% TODO stubs); add `tests/test_extract_issues.py` with real coverage of `unified_analyzer._extract_issues`.

**Out of scope:**
- Tier A: structured-fix-pipeline refactor (separate cycle).
- `tests/test_baseline.py` and `observatory_config` (user is restoring `observatory_config` later — leave both untouched).
- Hardcoded LinkedIn demo tab in `app.py` (intentional screenshot scaffolding).
- `.gitignore` cleanup (Tier C — low signal).
- Model-config and cost work (Tier B-eligible but deferred to its own cycle).

## Item 1: Delete unused modules

### Files to delete

| File | LOC | Imported by runtime? |
|---|---|---|
| `code_review_crew/utils/code_parser.py` | 414 | No |
| `code_review_crew/utils/report_generator.py` | 450 | No |
| `code_review_crew/utils/sandbox_manager.py` | 500 | No |
| `code_review_crew/tools/security_scanner.py` | 278 | No (SecurityReviewer reimplements inline) |
| `code_review_crew/tools/test_runner.py` | 344 | No (CodeExecutor reimplements inline) |
| `code_review_crew/tools/git_tool.py` | 347 | No (no diff-review flow exists) |

Total: ~2,333 LOC. The `code_review_crew/utils/` directory has no `__init__.py`, so deleting the three files removes the directory cleanly.

### Files to edit

- `code_review_crew/__init__.py`: drop `SecurityScanner` and `GitTool` from imports and `__all__`. `LintingTool` and `ComplexityAnalyzer` stay (used by `run_group_chat.py`).
- `code_review_crew/tools/__init__.py`: drop `SecurityScanner` and `GitTool` (same reasoning).

### Pre-deletion verification

Confirm zero runtime callers before deleting. Each command should return zero matches outside docs and the `__init__.py` files being edited:

```bash
git grep -l "from code_review_crew.utils"
git grep -l "code_review_crew\.utils"
git grep -n "SecurityScanner\|TestRunner\|GitTool" -- ':!INVESTIGATION.md' ':!TIER_B_PRD.md' ':!README.md' ':!ARCHITECTURE.md'
```

Expected output for the third command: only `code_review_crew/__init__.py` and `code_review_crew/tools/__init__.py` (the files being edited). If anything else appears, stop and investigate before deleting.

### Risk

Low. None of the deleted modules are imported on the runtime path (`app.py` → `unified_analyzer` → `run_group_chat` + `code_fixer`). The package `__init__.py` re-exports are convenience aliases; runtime imports use specific paths (`from code_review_crew.agents.code_analyzer import CodeAnalyzer`).

### Rollback

`git revert <commit>` — single commit per item recommended so revert is clean.

## Item 2: Real tests for `_extract_issues`

### Target

`unified_analyzer.UnifiedCodeAnalyzer._extract_issues` (lines 215–311). This is the bridge between the AutoGen review stage and the LangGraph fix stage; per the audit, it's the most fragile function in the codebase and the silent-failure mode when format drifts.

### Test plan

New file: `tests/test_extract_issues.py`. Framework: pytest (already in `requirements.txt`). No fixtures needed — synthetic review dicts are inlined per test.

Nine tests:

1. **`test_happy_path_three_agents`** — Conversation contains one well-formed issue from each of `CodeAnalyzer`, `SecurityReviewer`, `PerformanceOptimizer` in the documented `- Issue type: / - Line number: / - Description: / - Severity:` format. Assert: 3 issues returned, each tagged with the correct `agent`, severities canonicalized to `"Critical"` / `"High"` / `"Medium"`.

2. **`test_missing_conversation_key_returns_empty`** — Pass `{}`. Assert: `[]`.

3. **`test_filters_non_review_speakers`** — Conversation contains messages from `User`, `TestGenerator`, `CodeExecutor`, `ReviewOrchestrator` only (no reviewer agents). Assert: `[]`.

4. **`test_rejects_issue_missing_severity`** — Issue block has `Description:` but no `Severity:` line. Assert: not included.

5. **`test_rejects_issue_missing_description`** — Issue block has `Severity:` but no `Description:` line. Assert: not included.

6. **`test_severity_normalization_case_insensitive`** — Inputs `"CRITICAL"`, `"High"`, `"medium"`, `"LOW"`. Assert: outputs `"Critical"`, `"High"`, `"Medium"`, `"Low"`.

7. **`test_dedups_by_line_and_description_prefix`** — Same `line` and same first 40 chars of description, reported by two different agents. Assert: 1 issue returned (current dedup semantics).

8. **`test_sorts_by_severity_critical_first`** — Conversation supplies issues in `Low → High → Critical → Medium` order. Assert: output order is `Critical, High, Medium, Low`.

9. **`test_xfail_markdown_bold_format_drift`** — Marked `pytest.mark.xfail(reason="format drift not yet handled; Tier A will fix")`. Agent emits `**Severity:** CRITICAL` (markdown bold instead of dash prefix). Asserts issue is correctly extracted. Currently expected to fail — flips to passing when Tier A replaces string-matched extraction with structured issue emission, at which point the `xfail` mark gets removed. This test is the regression net for Tier A.

### Also delete in this commit

`tests/test_agents.py` — 106 lines of `pass` stubs across `TestCodeAnalyzer`, `TestSecurityReviewer`, `TestPerformanceOptimizer`, `TestToolIntegration`, `TestGroupChat`, `TestIntegration`. None are implemented; their presence falsely suggests coverage. Real tests for those agents are out of scope for this cycle (they'd be a larger investment, and most of them become obsolete after Tier A anyway).

### Verification

```bash
pytest tests/test_extract_issues.py -v
```

Expected: 8 passed, 1 xfailed.

```bash
pytest tests/
```

Expected: 8 passed, 1 xfailed, 0 collected from `test_agents.py` (deleted), `test_baseline.py` still errors on `observatory_config` import (unchanged — user is restoring later).

## Success criteria

- All six target files deleted; `code_review_crew/utils/` directory gone.
- `git grep "SecurityScanner\|TestRunner\|GitTool"` returns matches only in docs (`README.md`, `ARCHITECTURE.md`, `INVESTIGATION.md`, `TIER_B_PRD.md`) — zero in `.py` files.
- `python -c "import code_review_crew"` succeeds (package imports cleanly after `__init__.py` prune).
- `streamlit run app.py` starts without `ImportError` (smoke test — don't need to exercise a full review).
- `pytest tests/test_extract_issues.py` reports `8 passed, 1 xfailed`.
- Net LOC delta: ~–2,439 (deletions) + ~+200 (new test file) = roughly –2,200 lines.

## Effort estimate

1.5–2 hours total:
- Item 1: ~30 min (verification greps, deletes, `__init__.py` prune, smoke test).
- Item 2: ~60–90 min (write 9 tests with synthetic conversation fixtures, debug any extraction quirks discovered while writing them — likely at least one).

Recommend two separate commits, one per item, for clean rollback and reviewability.

## Out of scope (explicit)

- Anything in Tier A (structured issue contract, real pattern fixers, real test node).
- `observatory_config` restoration or `test_baseline.py` repair.
- Demo tab refactor.
- README updates to reflect deleted modules — defer to README pass at end of Tier A so it's one update, not two.
- Type hints, docstrings, or formatting on surviving code.

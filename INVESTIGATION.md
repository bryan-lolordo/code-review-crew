# Code Review Crew — Investigation

## Phase 1: Surface Scan

**What this project is:** A Streamlit demo that runs Python code through a 6-agent AutoGen group chat (review) and then a LangGraph state machine (auto-fix). Single-file in, fixed-file out. Targeted at LinkedIn-screenshot demos.

**Stack:** Python 3.9+; `pyautogen` (multi-agent), `langgraph` + `langchain-openai` (state machine), GPT-4 via OpenAI API, Streamlit UI. Static analyzers wrapped: pylint, pycodestyle, bandit, radon.

**Top-level layout (2 levels):**
```
code-review-crew/
├── app.py                       Streamlit UI (711 lines)
├── unified_analyzer.py          Two-stage orchestrator
├── run_group_chat.py            AutoGen GroupChat runner
├── log_capture.py               stdout → StringIO for UI
├── code_review_crew/
│   ├── agents/                  6 BaseAgent subclasses
│   ├── tools/                   linting/complexity (used); security_scanner/test_runner/git_tool (unused)
│   └── utils/                   code_parser, report_generator, sandbox_manager (all unused, ~1.4k lines)
├── code_fixer/                  LangGraph workflow (fixer + nodes + state)
├── examples/                    Demo code samples
└── tests/                       test_agents.py (all `pass`); test_baseline.py (broken import)
```

**Maturity signals:**
- Tests folder: exists, **non-functional** — `test_agents.py` is 100% TODO stubs; `test_baseline.py` imports `observatory_config` (file not present).
- CI: **none** (no `.github/`, no workflow files).
- Docs: README + ARCHITECTURE.md present. README references files/modules that don't exist (`tests/integration/`, `tests/e2e/`, `code_review_crew.examples.test_all_examples`).
- License: MIT.
- `.gitignore` lists `examples/` and `tests/` — both are committed anyway. `.cache/` was scrubbed in commit `0debb67`, `observatory.db` (221 KB SQLite) is untracked but present.

---

## Phase 2: Entry Points and Flow

**Entry points:**
- `app.py` — Streamlit (`streamlit run app.py`), 6 tabs incl. a hardcoded "LinkedIn Demo Flow" tab.
- `unified_analyzer.py:UnifiedCodeAnalyzer` — programmatic API (`review_only`, `review_and_fix`).
- `run_group_chat.py:CodeReviewChat` — direct AutoGen group-chat invocation.

**Representative flow (review + fix):**
1. `app.py` → `UnifiedCodeAnalyzer.review_and_fix(code, max_iterations)`
2. Stage 1 — AutoGen GroupChat: `ReviewOrchestrator` prompts `CodeAnalyzer → SecurityReviewer → PerformanceOptimizer → TestGenerator` in a 7-agent chat (`max_round=20`, `speaker_selection_method="auto"`). Returns conversation history.
3. `_extract_issues` parses agent free text by string-matching `"- Issue type:"`, `"- Severity:"`, `"- Description:"`. **This is the bridge between the two stages and is extremely brittle.**
4. Stage 2 — LangGraph: `fix_issue → test_code → {continue|done|failed}` loop. Each iteration: try regex pattern fix → fallback to LLM (`langchain-openai`) → `compile()` check.
5. Returns `fixed_code`, counts, logs.

**External dependencies:** OpenAI API (required, hardcoded `gpt-4`); Docker (optional, defaults off — `CodeExecutor.docker_available` is almost always `False`); shell subprocesses for `pylint`/`bandit`/`radon`/`pycodestyle`.

---

## Phase 3: Conventions and Patterns

**Test framework:** pytest declared in requirements; **not actually exercised** (stubs only).
**Linting setup:** None for this repo's own code — the static analyzers are tools the system *applies to user input*, not tools applied to the project itself.
**Idiomatic patterns observed:**
- Heavy reliance on `print()` + `LogCapture` (StringIO) for UI feedback rather than structured logging.
- `from X import Y` with broad try/except + fallback to "simple agents" in `run_group_chat.py` (defensive but masks import failures).
- Regex-based code introspection throughout — no `ast` module use anywhere despite Python's built-in being far more reliable.
- Severity strings inconsistent: `"Critical"` vs `"CRITICAL"`, `"High"` vs `"HIGH"`, normalized late in `_extract_issues`.

**Recent activity (last ~10 commits):** All housekeeping — README updates, removing `.cache`, UI tweaks, "fixed", "not needed". No feature work in flight.

---

## Phase 4: Leverage Map — Prioritized Improvements

**Context (from user, 2026-05-18):** This is a **portfolio project** demonstrating agentic work with AutoGen + LangGraph. Reviewers (recruiters, interviewers, other engineers) will read the code. The biggest risk isn't ugly UI — it's the gap between what the README claims and what the system actually does. Tab 5's hardcoded LinkedIn-demo report is intentional screenshot scaffolding and stays as-is. `observatory_config` is coming back later, so `test_baseline.py` is left alone for now. The `utils/` directory was meant to be wired in but never connected. The `code_review_crew/tools/{security_scanner,test_runner,git_tool}.py` modules are in the same "intended but not connected" bucket.

Items below are the same ten findings from the previous draft, re-bucketed by portfolio impact.

### Tier A — "the system doesn't do what it claims" (highest signal to a reviewer)

These three read as a single problem: the auto-fix pipeline is, end-to-end, a demo prop. Fix them together as one coherent change.

**1. Replace string-matched issue extraction with a structured contract.**
`unified_analyzer.py:215` (`_extract_issues`) parses LLM free-text by substring matching `"- Issue type:"`, `"- Severity:"`, etc. Agents are told "use this format" but GPT-4 routinely deviates (numbered lists, markdown bold, code fences). When extraction fails, the system silently reports "0 issues found" and exits successfully. Fix: agents emit JSON via AutoGen's function-calling, validate against a Pydantic schema (`pydantic` is already a dependency), surface parse failures.

**2. Pattern fixers are demo-specific string replacements, not real fixers.**
`code_fixer/nodes.py:316-323` literally does `.replace('query = f"SELECT * FROM users WHERE name = \'{username}\'"', ...)` — the exact string from the LinkedIn demo. `_fix_hardcoded_secrets` regex-replaces *every* string ≥10 chars assigned to a variable (will mangle real strings). `_fix_nested_loops` just prepends a TODO comment. Fix: either (a) make pattern fixers honest via line-number gating + AST inspection, or (b) drop the pattern path entirely and route everything through the LLM with a strict diff-only prompt.

**3. The "test" node doesn't actually test anything.**
`code_fixer/nodes.py:436` (`_run_tests`) runs `compile()` and greps for `eval(`/`exec(`/`__import__`. That's a syntax check, not a test. `CodeExecutor.validate_fix` already implements the right idea (Docker-sandboxed before/after exec, verdict assignment) but is **never called by the LangGraph workflow**. Fix: replace `_run_tests` with detector re-run — iteration only succeeds if the originally-reported issue no longer fires against the patched code.

### Tier B — cleanup that makes the repo look maintained

**5. ~2.3k lines of unused infrastructure imported but never called.**
`code_review_crew/utils/{code_parser,report_generator,sandbox_manager}.py` (~1,364 lines combined) imported by nothing in the runtime path. `code_review_crew/tools/{security_scanner,test_runner,git_tool}.py` (~969 lines) re-exported from `__init__.py` but never instantiated outside the package's own re-exports. `SecurityReviewer` reimplements regex-based secret detection inline instead of using `SecurityScanner`; `CodeExecutor` inlines its own Docker-pytest flow instead of using `TestRunner`. Per user: these were intended to be wired in but never connected. Decision needed: wire in (proves agentic competence) or delete (proves discipline). Either beats the current state.

**8. Broken test infrastructure that gives a false sense of coverage.**
`tests/test_agents.py` is 8 test classes × ~3 methods each, all `pass` with `# TODO: Implement`. README §Testing says `pytest tests/` works — it would, but it tests nothing. `tests/test_baseline.py` imports `observatory_config` which doesn't exist locally — user is bringing it back later, so leave this file alone. Fix: replace `test_agents.py` stubs with 5–10 real tests starting with `_extract_issues` (the most fragile function in the codebase).

**9. Hardcoded model (`gpt-4`) in three places; no Anthropic support despite README.**
`run_group_chat.py:45`, `code_fixer/fixer.py:55`, README §Environment Variables — README mentions `ANTHROPIC_API_KEY` as optional but no code path uses it. Fix: read model from env (`OPENAI_MODEL`, default `gpt-4o-mini` to cut cost ~30×); plumb through `langchain-anthropic` if the Claude path is intended.

**10. GroupChat cost is hidden and likely understated.**
7 agents in `speaker_selection_method="auto"` with `max_round=20` means up to 20 selection LLM calls + 20 agent response calls per review on GPT-4. README claims $0.05–0.10/review which is implausible for this volume on GPT-4 (likely $0.30–0.80 in practice). Fix: switch to `speaker_selection_method="round_robin"` (orchestrator already dictates strict order in its prompt anyway); cap `max_round` at 8; or move agents to a cheaper model and reserve GPT-4 for the LLM-fallback fixer. Re-measure and update README.

**4. Pattern fixers stack `# Fixed: X` header comments across iterations.**
`_fix_sql_injection`, `_fix_weak_crypto`, `_fix_hardcoded_secrets`, `_fix_import_in_function` each prepend a single-line comment when their fix applies. Across 4–5 issues you get 4–5 stacked banners, sometimes duplicated when the same fixer runs twice. LLM fallback also prepends `# TODO: Fix - ...` on failure. Fix: emit fix metadata into the state object, render in UI; do not mutate code with provenance comments. (Falls out naturally if Tier A #2 is done well.)

### Tier C — skip for now

**6. Hardcoded LinkedIn Demo Flow tab.** Intentional screenshot scaffolding per user. Leave as-is.

**7. `.gitignore` entries for `examples/` and `tests/`.** Low signal; both dirs are already tracked so the contradiction is cosmetic. Defer.

`test_baseline.py` / `observatory_config`: user is bringing `observatory_config` back later. Leave the import as-is.

---

## Resolved Open Questions (2026-05-18)

- **Tab 5 (`app.py:426-660`):** hardcoded for LinkedIn screenshots, intentional. Leave as-is.
- **`observatory_config`:** user is bringing it back eventually. Don't repair or remove `test_baseline.py`.
- **`utils/` and unused tools:** were meant to be wired in, but the connection was never made. Either wire in or delete — both options are open.
- **Audience:** portfolio project for demonstrating agentic AutoGen + LangGraph work. Prioritize correctness/defensibility under code-review over user-facing polish.

## Next Steps

Tier A is the next cycle (or several). It's a real refactor — restructure agents to emit structured issues, replace the demo-string pattern fixers with AST/LLM-driven fixes, and replace the `compile()`-only test node with detector re-runs. Estimated 4–6 hours touching ~6 files. Will be scoped and started in a separate `/start` cycle.

Tier B items are independent of Tier A and can be picked off in any order as smaller cycles.


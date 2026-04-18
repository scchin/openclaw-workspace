# ClaudeCode Programmer Decision Logic & Behavioral Analysis

This document analyzes the decision-making heuristics, anti-patterns, and trade-offs implemented in the ClaudeCode programmer perspective, based on the analysis of `coordinatorMode.ts`, `security_reminder_hook.py`, and the `code-review` plugin.

## 1. Decision Heuristics (啟發式決策)

The system operates on a hierarchy of "Coordinator $\rightarrow$ Worker $\rightarrow$ Verifier" with strict rules to ensure high-signal output and efficient resource use.

### A. Orchestration & Delegation (Coordinator Level)
- **Direct Action Preference**: The coordinator should answer questions directly if no tools are required. Delegation is a secondary choice to avoid unnecessary latency and token cost.
- **Parallelism as Default for Research**: Independent read-only tasks (research) are executed in parallel to cover multiple angles quickly.
- **Serialization for State Mutation**: Write-heavy tasks are serialized per file set to prevent race conditions and conflicting edits.
- **Synthesis Requirement**: The coordinator is strictly forbidden from "lazy delegation" (e.g., "Fix the bug based on the research"). It must synthesize findings into a precise specification including file paths and line numbers before directing a worker.
- **Context-Aware Continuation**: 
    - **Continue**: Used when there is high context overlap (e.g., the worker who researched the file is the one who should edit it) or when correcting a failure.
    - **Spawn Fresh**: Used for narrow implementation tasks (to avoid noise), verification (to ensure "fresh eyes"), or when the previous approach was fundamentally wrong.

### B. Security Guardrails (Hook Level)
- **Pre-emptive Blocking**: Security risks are handled via "PreToolUse" hooks that block execution (`exit 2`) if a known dangerous pattern is detected.
- **Remediation-First Guidance**: Warnings do not just block; they provide a specific "Safe Alternative" (e.g., replacing `child_process.exec` with `execFileNoThrow`).
- **Context-Specific Risk Profiles**: Different rules apply based on file paths (e.g., GitHub Actions workflows trigger specific injection warnings that generic JS files do not).
- **Stateful Warning Suppression**: To prevent "warning fatigue," security reminders are tracked per session and per file, ensuring the user isn't nagged by the same warning repeatedly.

### C. Quality Assurance (Review Level)
- **Triage-First Filtering**: PRs are filtered for status (closed/draft) and triviality before any expensive review agents are launched.
- **Ensemble Review (Diversification)**: Multiple agents (Sonnet/Opus) review the same code independently with different personas (Compliance vs. Bug hunting) to reduce individual model bias.
- **Double-Blind Validation**: Every flagged issue must be validated by a separate subagent. If the validator cannot confirm the issue with high confidence, it is discarded.

---

## 2. Anti-Patterns (禁止/避免的行為)

The system explicitly encodes "what NOT to do" to maintain trust and system stability.

| Category | Anti-Pattern | Rationale | Evidence |
| :--- | :--- | :--- | :--- |
| **Coordination** | **Lazy Delegation** | Shifting the burden of "understanding" to the worker leads to hallucinations and imprecise edits. | `coordinatorMode.ts` (Section 5) |
| **Coordination** | **Recursive Monitoring** | Using one worker to check on another creates redundant loops and waste. | `coordinatorMode.ts` (Section 2) |
| **Review** | **Nitpicking** | Subjective style suggestions or "potential" issues erode trust and waste reviewer time. | `code-review.md` (Step 4/Critial) |
| **Review** | **Half-Baked Suggestions** | Providing a committable suggestion that requires further manual steps. | `code-review.md` (Step 9) |
| **Security** | **Shell Execution** | Using `eval()` or `child_process.exec()` with dynamic strings. | `security_reminder_hook.py` |
| **Security** | **Unsafe DOM Access** | Using `innerHTML` or `dangerouslySetInnerHTML` without sanitization. | `security_reminder_hook.py` |

---

## 3. Trade-offs (權衡取捨)

### A. Precision $\gg$ Recall (in Code Review)
The system explicitly chooses to **ignore potential bugs** rather than **report a false positive**. 
- **Decision**: If an agent is not 100% certain an issue is real, it is told *not* to flag it.
- **Trade-off**: Higher risk of missing subtle bugs, but ensures that every reported issue is "High Signal" and actionable, preserving the reviewer's trust.

### B. Reliability $\gg$ Cost/Latency (in Verification)
The system utilizes a heavy, multi-stage agent pipeline (Ensemble $\rightarrow$ Validator).
- **Decision**: Launching 4+ parallel agents followed by a validation layer for every PR.
- **Trade-off**: Significantly higher token consumption and increased time-to-result in exchange for near-zero false-positive rates in the final report.

### C. Structure $\gg$ Flexibility (in Prompting)
The coordinator is forced to follow a rigid "Research $\rightarrow$ Synthesis $\rightarrow$ Implementation $\rightarrow$ Verification" workflow.
- **Decision**: Forcing the coordinator to write a "Synthesized Spec" rather than allowing a fluid conversation.
- **Trade-off**: Slower initial turn-around, but ensures that workers have the exact context needed, reducing the number of "correction turns" required to get the code right.

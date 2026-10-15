# A. Open-source frameworks and commercial systems: prior art for AgentPause

**Scope:** open-source software and industry/commercial systems (2023 to 2026) that implement human-in-the-loop approval, confirmation, interruption, permission or escalation for AI agents.
**Compiled:** 2026-10-14.
**Method:** web search, then fetching each item's official docs, repo, system card or code (via WebFetch, `gh api`, or direct PDF download and text extraction). Every entry below was checked against at least one primary source (official docs, official blog/system card, or source code). Dates come from those sources, from GitHub release/commit metadata, or are marked as approximate. Anything I could not confirm from a primary source is listed in the final section rather than in the main catalogue.
**Search note:** the shared web-search budget for this session ran out near the end. A few last items (Salesforce Agentforce confirmation settings, Google Project Mariner's official page) were therefore checked only partially; see "Could not verify".

AgentPause reference (for the comparison columns): middleware between agent and environment; input = proposed action + context (uncertainty, consequence severity, reversibility, user-intent ambiguity, task progress, interruption cost, user preferences, past user decisions); output = CONTINUE / CLARIFY / ASK_HUMAN / DEFER / BLOCK + explanation (including counterfactual "why not earlier/later"); experiment harness comparing full autonomy, always confirm, fixed risk threshold, adaptive multi-signal expected-value-of-asking, and user-customized policies.

---

## 0. Summary table

| # | Name | Year | Org | Type | Direct competitor? |
|---|---|---|---|---|---|
| 1 | LangGraph `interrupt()` | 2024 (Dec) | LangChain | software artifact | no |
| 2 | LangChain `HumanInTheLoopMiddleware` | 2025 | LangChain | software artifact | partial |
| 3 | OpenAI Agents SDK (`needs_approval`, guardrails) | 2025 (JS) / 2026 (Py HITL) | OpenAI | software artifact | partial |
| 4 | OpenAI Agent Builder "Human approval" node | 2025 | OpenAI | commercial product | no |
| 5 | AutoGen `human_input_mode` and AgentChat HITL | 2023 / 2025 | Microsoft | software artifact | no |
| 6 | Microsoft Agent Framework tool approval (+ Semantic Kernel filters) | 2025 to 2026 | Microsoft | software artifact | partial |
| 7 | Magentic-UI action guards / approval policies | 2025 | Microsoft Research | both | **partial (close)** |
| 8 | Copilot Studio multistage and AI approvals | 2025 | Microsoft | commercial product | partial |
| 9 | CrewAI `human_input` / `@human_feedback` / HITL webhooks | 2023+ | CrewAI | software artifact + commercial | no |
| 10 | Pydantic AI deferred tools (`requires_approval`, `ApprovalRequired`) | 2025 | Pydantic | software artifact | no |
| 11 | Vercel AI SDK tool approval (`needsApproval` / `toolApproval`) | 2025 (Dec) | Vercel | software artifact | no |
| 12 | Mastra tool approval (`requireToolApproval`, incl. classifier example) | 2026 | Mastra | software artifact | partial |
| 13 | LlamaIndex Workflows HITL events | 2024+ | LlamaIndex | software artifact | no |
| 14 | Google ADK tool confirmation | 2025 | Google | software artifact | no |
| 15 | n8n Human review for AI tools | 2025 to 2026 | n8n | software + commercial | no |
| 16 | HumanLayer (`require_approval`, `human_as_tool`) | 2024 | HumanLayer | software + commercial | no |
| 17 | gotoHuman | 2024 to 2025 | gotoHuman | commercial product | no |
| 18 | Permit.io Access Request MCP | 2025 | Permit.io | software + commercial | no |
| 19 | Auth0 for AI Agents: Async Authorization (CIBA) | 2025 | Auth0/Okta | commercial product | no |
| 20 | MCP elicitation (form / URL mode) | 2025 | MCP project | spec | no |
| 21 | OSS approval gateways: Phantasm, Cordum, AEGIS, AgentSafe/Decionis | 2024 to 2026 | various | software (AEGIS: both) | partial |
| 22 | Claude Code permission modes + **auto mode classifier** | 2025 / 2026 | Anthropic | commercial product | **partial (closest commercial)** |
| 23 | Claude Code hooks (`permissionDecision` allow/deny/ask/defer) | 2025 to 2026 | Anthropic | commercial product (extension point) | no (integration target) |
| 24 | OpenAI Codex approval policies + **auto-review** + smart approvals | 2025 / 2026 | OpenAI | software + commercial | **partial (close)** |
| 25 | Cline auto-approve (+ model-set `requires_approval`) | 2024+ | Cline | software artifact | partial |
| 26 | Roo Code auto-approve per category | 2024+ | Roo Code | software artifact | partial |
| 27 | Cursor run modes + **Auto-review classifier** | 2026 | Anysphere | commercial product | partial |
| 28 | VS Code / GitHub Copilot agent approvals + **Assisted permissions** | 2025 to 2026 | Microsoft/GitHub | software + commercial | partial |
| 29 | Gemini CLI policy engine | 2025 | Google | software artifact | no |
| 30 | Devin Desktop (formerly Windsurf) auto-execution levels | 2025 to 2026 | Cognition | commercial product | partial |
| 31 | Warp agent permissions ("Agent decides") | 2025 to 2026 | Warp | commercial product | partial |
| 32 | goose permission modes (Smart Approval) | 2025 | Block / AAIF | software artifact | partial |
| 33 | OpenHands confirmation mode + security analyzer (`ConfirmRisky`) | 2024 | All Hands AI | software artifact | **partial (fixed-threshold baseline)** |
| 34 | OpenAI Operator (CUA) confirmations / watch / takeover | 2025 (Jan) | OpenAI | commercial product | partial |
| 35 | ChatGPT agent confirmations / watch mode | 2025 (Jul) | OpenAI | commercial product | partial |
| 36 | Claude for Chrome / Claude in Chrome permissions + action screening | 2025 | Anthropic | commercial product | partial |
| 37 | Gemini in Chrome agentic security (User Alignment Critic + confirmations) | 2025 (Dec) | Google | commercial product | partial |
| 38 | Gemini Computer Use `safety_decision` (`require_confirmation`) | 2025 | Google | commercial API | partial |
| 39 | Amazon Bedrock Agents user confirmation / return of control | 2024 to 2025 | AWS | commercial product | no |
| 40 | Amazon Nova Act HITL (human approval, UI takeover) | 2025 | AWS | software + commercial | no |
| 41 | Salesforce Agentforce escalation via topic instructions | 2024 to 2025 | Salesforce | commercial product | no |
| 42 | NeMo Guardrails | 2023 | NVIDIA | software artifact | no |
| 43 | Guardrails AI | 2023 | Guardrails AI | software artifact | no |
| 44 | Invariant Guardrails | 2024 to 2025 | Invariant Labs | software artifact | no |
| 45 | LlamaFirewall (`ALLOW / HUMAN_IN_THE_LOOP_REQUIRED / BLOCK`) | 2025 | Meta | both | partial |
| 46 | Long-tail research repos on adaptive asking (TELEMACHUS, ask-or-act/Kiri, xtid, PPO intervention, ALL, RishiM19/AEGIS) | 2026 | individuals | academic/software | partial (conceptual) |

---

## 1. Agent frameworks (general-purpose)

### 1. LangGraph `interrupt()` / human-in-the-loop
- **Year:** 2024. LangChain blog "Making it easier to build human-in-the-loop agents with interrupt" is dated 14 Dec 2024. Earlier precursors were breakpoints, `NodeInterrupt`, and OpenGPTs "interrupt/authorize" modes (Feb 2024).
- **Authors / company:** LangChain Inc.
- **URL:** https://docs.langchain.com/oss/python/langgraph/interrupts (blog: https://blog.langchain.com/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt)
- **What it does:** `interrupt(value)` called anywhere in a node pauses the graph. State is checkpointed under a `thread_id`, and the payload goes to the caller (`__interrupt__`). Execution resumes with `Command(resume=...)`. Documented patterns: approve/reject before a critical action, review/edit state, validate input. *When* to ask is whatever conditional the developer writes in node code; the framework has no notion of risk or timing. Typed resume schemas exist since langgraph 1.2.12.
- **Overlap with AgentPause:** this is the pause/resume substrate: durable suspension, human response injection, routing on the answer.
- **What AgentPause would do differently:** decide *whether and when* to call `interrupt()`, from multiple signals plus explanations, instead of leaving that to a hand-written `if`. AgentPause could ship as a LangGraph node or wrapper that emits `interrupt()` for ASK_HUMAN/CLARIFY and holds a checkpoint for DEFER.
- **Direct competitor?** No. It is mechanism, not policy.
- **Type:** software artifact (MIT).

### 2. LangChain `HumanInTheLoopMiddleware`
- **Year:** 2025. Commits from Sep to Oct 2025 introduced and refactored it for LangChain v1. The `when` predicate requires `langchain>=1.3.3`, and `interrupt_mode="per_call"` requires `>=1.4.6`.
- **Authors / company:** LangChain Inc.
- **URL:** https://docs.langchain.com/oss/python/langchain/human-in-the-loop
- **What it does:** agent middleware with an `interrupt_on` map from tool name to policy (`True`, `False`, or `InterruptOnConfig`). Allowed decisions are `approve`, `edit`, `reject`, and `respond`. An optional **`when` predicate** (receives the `ToolCallRequest`) makes gating conditional on arguments, but it must be deterministic across resume. A per-tool `description` (static string or callable) sets the text the reviewer sees. Batched or per-call interrupt modes.
- **Overlap with AgentPause:** a middleware layer that intercepts proposed tool calls and decides interrupt vs. auto-approve, with a human-readable description. This is the same architectural slot as AgentPause.
- **What AgentPause would do differently:** the `when` predicate is a user-written boolean over one call. AgentPause supplies the policy itself: multi-signal scoring (uncertainty, reversibility, progress, interruption cost, history), more outcomes (CLARIFY, DEFER, BLOCK beyond approve/reject), counterfactual explanations, and a policy-comparison harness. AgentPause could plug in as the `when` callable plus the `description` generator.
- **Direct competitor?** Partial. Same interception point and allows conditional gating, but no decision model.
- **Type:** software artifact (MIT).

### 3. OpenAI Agents SDK: `needs_approval`, tool guardrails, interruptions
- **Year:** 2025 for the JS SDK (repo created May 2025; approval-related fixes from Jul 2025). The Python SDK added HITL on 29 Jan 2026 (commit "Add human-in-the-loop (HITL) support (#2230)").
- **Authors / company:** OpenAI.
- **URL:** https://openai.github.io/openai-agents-python/human_in_the_loop/ ; guardrails: https://openai.github.io/openai-agents-python/guardrails/
- **What it does:** `needs_approval` on a tool is `bool` or an async callable `(ctx, params, call_id) -> bool`, so approval can depend on arguments and context. If arguments can't be parsed, it fails safe to manual approval. The run pauses with `interruptions` (`ToolApprovalItem`). The developer calls `state.approve()`/`state.reject()` (optionally `always_approve`/`always_reject` sticky per tool for the run, plus `rejection_message`) and resumes. `RunState` serializes for long-lived approvals. Separately, input/output/tool **guardrails** with tripwires halt or replace calls automatically, with no human escalation path.
- **Overlap with AgentPause:** a per-call dynamic approval predicate, sticky per-run user decisions (a primitive form of "past user decisions"), and pause/resume.
- **What AgentPause would do differently:** the SDK supplies the hook, but the decision logic, signals, explanation, timing (DEFER) and evaluation are left to the developer. AgentPause would be a ready `needs_approval` policy plus a guardrail that can return CLARIFY or DEFER instead of only tripwire or pass.
- **Direct competitor?** Partial. Dynamic hook, no policy.
- **Type:** software artifact (MIT).

### 4. OpenAI Agent Builder (AgentKit) "Human approval" node
- **Year:** 2025 (AgentKit/Agent Builder launch; secondary sources date it to Oct 2025).
- **Authors / company:** OpenAI.
- **URL:** https://developers.openai.com/api/docs/guides/node-reference
- **What it does:** a visual workflow node that "defers to end-users for approval" (e.g., "Would you like me to send this email?") before continuing to an MCP/Gmail node. A separate Guardrails node runs pass/fail checks (PII, jailbreak, hallucination) and branches on failure.
- **Overlap with AgentPause:** an explicit approval step and a guardrail step in an agent workflow.
- **What AgentPause would do differently:** the node is placed statically by the workflow author. AgentPause decides dynamically at run time whether a given step warrants a stop.
- **Direct competitor?** No.
- **Type:** commercial product.

### 5. Microsoft AutoGen `human_input_mode` (v0.2) and AgentChat HITL (v0.4+)
- **Year:** 2023 (AutoGen 0.2; repo created Aug 2023). AgentChat 0.4 HITL in 2025.
- **Authors / company:** Microsoft Research.
- **URL:** https://microsoft.github.io/autogen/0.2/docs/tutorial/human-in-the-loop/ ; https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/human-in-the-loop.html
- **What it does:** v0.2 `human_input_mode`:
  - `NEVER`: the human is never asked.
  - `TERMINATE` (default): asked only when a termination condition fires or `max_consecutive_auto_reply` is hit, and the counter resets after human input.
  - `ALWAYS`: asked on every turn.

  v0.4 AgentChat offers a `UserProxyAgent` during a run (blocking), plus `max_turns`, `HandoffTermination` and `TextMentionTermination` to return control between runs. In `SelectorGroupChat`, an LLM selector or function decides when the user proxy speaks.
- **Overlap with AgentPause:** the canonical "full autonomy / always ask / ask at termination" baseline triad. A selector-driven user proxy is a crude learned "who speaks next" decision.
- **What AgentPause would do differently:** AutoGen's modes are exactly AgentPause's static baselines (NEVER ≈ full autonomy, ALWAYS ≈ always confirm). AgentPause adds per-action, signal-driven decisions and explanations, and treats AutoGen modes as comparison baselines.
- **Direct competitor?** No. Static modes; useful as baselines.
- **Type:** software artifact.

### 6. Microsoft Agent Framework tool approval (+ Semantic Kernel filters)
- **Year:** 2025 to 2026 (repo created Apr 2025; the docs page was updated Sep 2026). Semantic Kernel filters date from 2024 to 2026.
- **Authors / company:** Microsoft.
- **URL:** https://learn.microsoft.com/en-us/agent-framework/agents/tools/tool-approval ; SK filters: https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/filters
- **What it does:**
  - **.NET:** `ApprovalRequiredAIFunction` wraps a tool.
  - **Python:** `@tool(approval_mode="always_require" | "never_require")`.
  - **Run flow:** the run returns `ToolApprovalRequestContent` / `user_input_requests`, and the caller replies with approve/reject. Approval responses are bound to the pending request in the session (anti-replay).
  - **Harness Agent:** adds `ToolApprovalMiddleware`, which queues requests, applies **standing "always approve" rules from earlier user responses**, and evaluates developer-supplied heuristic **`auto_approval_rules`** before returning a request to the human.
  - **Semantic Kernel:** function-invocation and auto-function-invocation filters let code inspect a call (with chat history and iteration counters) and block or terminate it. This is a generic hook for approval logic.
- **Overlap with AgentPause:** per-tool flags plus a middleware stage that can auto-approve from heuristics and from past user decisions. This is the "user history" signal in its simplest form.
- **What AgentPause would do differently:** the rules here are developer heuristics plus remembered "always approve" decisions, with no probabilistic model, no timing, no CLARIFY/DEFER, and no explanation. AgentPause would generalize "standing approvals" into learned user-preference signals and would plug in as an `auto_approval_rules` callback or SK filter.
- **Direct competitor?** Partial.
- **Type:** software artifact (MIT).

### 7. Magentic-UI action guards / approval policies (Microsoft Research)
- **Year:** 2025. Repo created May 2025; MSR blog 19 May 2025; arXiv 2507.22358 submitted 30 Jul 2025.
- **Authors / company:** Microsoft Research (Hussein Mozannar, Gagan Bansal, Cheng Tan, Adam Fourney, et al.; 20 authors).
- **URL:** https://github.com/microsoft/magentic-ui ; paper https://arxiv.org/abs/2507.22358 ; blog https://www.microsoft.com/en-us/research/blog/magentic-ui-an-experimental-human-centered-web-agent/ ; guard code https://github.com/microsoft/magentic-ui/blob/magentic-ui-0.1/src/magentic_ui/approval_guard.py
- **What it does:**
  - **Interaction mechanisms:** an open-source human-centred web/coding agent with co-planning, co-tasking, multi-tasking, action guards and long-term memory.
  - **Action Guard (v0.1, verified in code):** each action type carries a developer-set irreversibility **baseline** (`always` / `maybe` / `never`). The agent also emits an `llm_guess`. A global **`approval_policy`** takes one of `always`, `never`, `auto-conservative` (default), or `auto-permissive`:
    - `always` / `never`: ask on every action / never ask.
    - Both auto policies: follow the baseline when it is `always` or `never`.
    - `auto-permissive`: for a `maybe` action, trusts the agent's guess.
    - `auto-conservative`: for a `maybe` action, calls an **LLM ActionGuard judge** whose prompt asks about real-world consequences, irreversibility or difficulty of undoing, data integrity/privacy, and effects on others. The judge sees the last ~5 context messages and returns YES/NO, erring toward approval when unsure.
  - **Current main branch:** `require_approval_untrusted` (default), `auto_approve`, or `require_approval_all`. Approval decisions are `APPROVE / DENY / ALTERNATIVE`. Statuses include `AUTO_SESSION` (session-level user preference), `AUTO_POLICY`, and `AUTO_SAFE` ("classifier determined this is a safe action").
  - **Paper evaluation:** simulated-user experiments measuring help-request frequency (e.g., ~10% of GAIA tasks with a side-info simulated user), a qualitative user study (participants found some approvals unnecessary, such as add-to-cart and approving a plan change right after requesting it, and **asked for a third option** beyond approve/deny), and adversarial safety tests.
- **Overlap with AgentPause:** high.
  - Reversibility is a first-class signal.
  - The policies are essentially AgentPause's baselines: always confirm, full autonomy, and two "smart" policies.
  - An LLM judge provides consequence/reversibility assessment.
  - Session-level user preferences are respected.
  - A research platform with simulated users and user studies on approval burden.
- **What AgentPause would do differently:**
  - Decides from many more signals: model uncertainty, intent ambiguity, task progress, interruption cost, and learned user history, not just irreversibility.
  - Returns five outcomes (CLARIFY/DEFER timing, not just binary approve/deny).
  - Produces explanations, including counterfactual "why now, not earlier or later". Magentic-UI's judge returns only YES/NO.
  - Offers a dedicated, framework-agnostic experiment harness that measures both missed-critical-confirmation and unnecessary-interruption cost across policies. Magentic-UI reports help-request rates but does not systematically compare approval policies.
- **Direct competitor?** **Partial, and one of the closest.** It has reversibility-driven multi-policy approval in a research HITL platform, but not multi-signal, timing-aware, or explanatory.
- **Type:** both (academic paper + MIT-licensed artifact).

### 8. Microsoft Copilot Studio: multistage and AI approvals in agent flows
- **Year:** 2025 (doc `ms.date` 4 Sep 2025; preview). The "Request for information" HITL action was in public preview around Aug 2025 (per a Microsoft message-center notice surfaced in search).
- **Authors / company:** Microsoft.
- **URL:** https://learn.microsoft.com/en-us/microsoft-copilot-studio/flows-advanced-approvals
- **What it does:** a "Run a multistage approval" action (Human review connector) composes manual stages, AI stages and conditions:
  - **Manual stages:** human approvers.
  - **AI stages:** an LLM applies written criteria to documents, images and text and returns **Approve/Reject with a rationale**, or "Analysis failed" when unsure.
  - **Conditions:** route between stages, e.g., amount > $5,000 → manager approval, otherwise auto-approve if the AI approved.
  - **Auditability:** rationale is visible in the approvals history and prompt-builder activity.
- **Overlap with AgentPause:** an AI decides whether a human is needed, with an explicit **rationale**, and with threshold conditions (fixed-risk-threshold style routing). "Analysis failed" is a crude uncertainty-to-human fallback.
- **What AgentPause would do differently:** this is business-process approval, not step-level agent interruption timing. Routing is static rules plus LLM verdict. There is no interruption-cost or progress model, no DEFER/CLARIFY, and no counterfactual explanation.
- **Direct competitor?** Partial (enterprise approval routing with AI rationale).
- **Type:** commercial product.

### 9. CrewAI human input / HITL
- **Year:** 2023+ (repo Oct 2023). The `@human_feedback` flow decorator arrived in v1.8.0. Enterprise HITL webhooks are also offered.
- **Authors / company:** CrewAI Inc.
- **URL:** https://docs.crewai.com/en/learn/human-in-the-loop ; https://docs.crewai.com/en/concepts/tasks
- **What it does:** `Task.human_input` (default False) has a human review the agent's final answer for that task. Enterprise webhooks set "Pending Human Input", notify, and resume with feedback. Negative feedback reruns the task with the feedback as context.
- **Overlap with AgentPause:** review checkpoints and resume-with-feedback.
- **What AgentPause would do differently:** CrewAI's checkpoint is statically attached to tasks (post-hoc review). AgentPause decides per action, pre-execution, and adaptively.
- **Direct competitor?** No.
- **Type:** software artifact + commercial (Enterprise).

### 10. Pydantic AI deferred tools
- **Year:** 2025 (deferred tool results in the codebase by Sep 2025).
- **Authors / company:** Pydantic.
- **URL:** https://pydantic.dev/docs/ai/tools-toolsets/deferred-tools/ (redirect from https://ai.pydantic.dev/deferred-tools/)
- **What it does:** `requires_approval=True` on a tool, or raise **`ApprovalRequired`** inside the tool or arg validator for *conditional* approval ("when approval depends on the tool call's arguments or the agent run context"), with optional metadata. Runs end with `DeferredToolRequests`, and the caller answers with `DeferredToolResults` (`ToolApproved` with `override_args`, or `ToolDenied` with a message). Can be handled inline (`HandleDeferredToolCalls`) or stop-the-world. Conversations persist for later resumption.
- **Overlap with AgentPause:** conditional approval with metadata, plus the idea of *deferring* a tool call for out-of-band resolution, which is close to AgentPause's DEFER semantics.
- **What AgentPause would do differently:** Pydantic AI's "deferred" means "awaiting an external result", not a timing decision ("ask later, at a better moment"). The approval condition is developer code. AgentPause provides the decision policy, explanation and evaluation.
- **Direct competitor?** No.
- **Type:** software artifact (MIT).

### 11. Vercel AI SDK tool execution approval
- **Year:** 2025. AI SDK 6 blog dated 22 Dec 2025 (authors Gregor Martynus, Lars Grammel, Aayush Kapoor, Josh Singh, Nico Albanese).
- **Authors / company:** Vercel.
- **URL:** https://vercel.com/blog/ai-sdk-6 ; https://ai-sdk.dev/docs/ai-sdk-core/tools-and-tool-calling
- **What it does:** `needsApproval` is boolean or an async function of the input (e.g., only when a command contains `rm -rf`). Current docs deprecate it in favour of a `toolApproval` config per call (`'not-applicable' | 'approved' | 'denied' | 'user-approval'`, or a function such as `amount > 1000 ? 'user-approval' : undefined`). Results include `tool-approval-request` parts (`approvalId`, `toolCall`, **`reason`**). The UI answers via `tool-approval-response` / `addToolApprovalResponse`.
- **Overlap with AgentPause:** a tri-state per-call decision (approved / denied / ask user) with a reason field: essentially a CONTINUE / BLOCK / ASK_HUMAN interface.
- **What AgentPause would do differently:** the decision function is a developer-written rule over arguments. AgentPause offers the multi-signal policy, CLARIFY/DEFER, counterfactual explanations, and evaluation. AgentPause could be packaged as a `toolApproval` function.
- **Direct competitor?** No (an interface AgentPause could implement).
- **Type:** software artifact.

### 12. Mastra agent tool approval
- **Year:** 2025 to 2026 (approve/decline for `Agent.generate()` added Jan 2026).
- **Authors / company:** Mastra.
- **URL:** https://mastra.ai/docs/agents/agent-approval
- **What it does:** `requireToolApproval` (per request) and `requireApproval` (per tool), OR-combined. The run suspends with a `tool-call-approval` chunk and the developer calls `approveToolCall()` or `declineToolCall(reason)`. `requireToolApproval` can be a **function** of `toolName`, `args`, `requestContext` and `workspace`. The docs explicitly show a **classifier-based example that requires approval when a classifier probability ≥ 0.7**. The function fails safe to "require approval" on error. Tools can also `suspend()` mid-run for more input. A suggested **argument fingerprinting** step binds an approval to the exact reviewed arguments.
- **Overlap with AgentPause:** a documented "fixed risk-threshold" policy (classifier score ≥ τ). This matches AgentPause's fixed-threshold baseline.
- **What AgentPause would do differently:** Mastra's single classifier threshold ignores reversibility, progress, interruption cost and user history, and gives no explanation. AgentPause evaluates exactly this kind of threshold policy against adaptive EV-of-asking.
- **Direct competitor?** Partial (provides the fixed-threshold baseline pattern).
- **Type:** software artifact.

### 13. LlamaIndex Workflows human-in-the-loop
- **Year:** 2024+ (Workflows).
- **Authors / company:** LlamaIndex.
- **URL:** https://developers.llamaindex.ai/python/llamaagents/workflows/human_in_the_loop/
- **What it does:** a step emits `InputRequiredEvent`, and the caller replies with `HumanResponseEvent` (or uses `ctx.wait_for_event()`). Context can be serialized and resumed across processes.
- **Overlap with AgentPause:** a pause/resume primitive.
- **What AgentPause would do differently:** LlamaIndex has no policy for when to emit the event. AgentPause supplies it.
- **Direct competitor?** No.
- **Type:** software artifact (MIT).

### 14. Google Agent Development Kit (ADK) tool confirmation
- **Year:** 2025 (Python ADK v1.14.0; experimental).
- **Authors / company:** Google.
- **URL:** https://adk.dev/tools-custom/confirmation/
- **What it does:** "Boolean confirmation" via `require_confirmation=True`, or a function of the tool's arguments (Python and Go), e.g., an amount threshold. "Advanced confirmation" calls `tool_context.request_confirmation(hint, payload)` to ask for structured data and resumes with `tool_confirmation.payload`.
- **Overlap with AgentPause:** a conditional confirmation hook, plus a structured "clarify" variant (hint + payload schema).
- **What AgentPause would do differently:** ADK leaves the policy to the developer. AgentPause adds signal fusion, timing and explanations.
- **Direct competitor?** No.
- **Type:** software artifact (Apache-2.0).

### 15. n8n Human review for AI agent tools
- **Year:** 2025 to 2026 (the introduction date is not stated on the docs page).
- **Authors / company:** n8n GmbH.
- **URL:** https://docs.n8n.io/advanced-ai/human-in-the-loop-tools/
- **What it does:** in the AI Agent's Tools panel, a "Human review" step is connected in front of selected tools. Calls to them pause and send an approval request over Chat, Slack, Teams, Telegram, Gmail, Outlook and similar channels. Approve runs the tool with the AI's inputs; deny cancels it and tells the AI. No conditional logic is described.
- **Overlap with AgentPause:** per-tool approval gating with multi-channel delivery.
- **What AgentPause would do differently:** n8n's gating is static per tool. AgentPause chooses dynamically and could pick the channel and timing based on interruption cost.
- **Direct competitor?** No.
- **Type:** software (fair-code) + commercial.

---

## 2. HITL / approval services, authorization, protocols

### 16. HumanLayer
- **Year:** 2024 (repo created Aug 2024; v0.7.0 README dated Jan 2025). The repo README now says the original SDK code is "pretty much all deprecated", and the company has pivoted to coding-agent tooling.
- **Authors / company:** HumanLayer (GitHub org `humanlayer`).
- **URL:** https://github.com/humanlayer/humanlayer (original SDK README at tag v0.7.0: https://github.com/humanlayer/humanlayer/tree/v0.7.0)
- **What it does:** the `@hl.require_approval()` decorator wraps a tool function so a human must approve before it runs, "baked into the tool/function itself". `hl.human_as_tool()` lets the agent consult a human for advice. Approvals are routed asynchronously to humans (the v0.7.0 README shows a Slack approval screenshot). Integrations include LangChain, CrewAI, ControlFlow and the raw OpenAI client.
- **Overlap with AgentPause:** a framework-agnostic approval layer around tools, plus "ask a human" as a tool (≈ CLARIFY).
- **What AgentPause would do differently:** HumanLayer gates are static per function. AgentPause decides per call and explains.
- **Direct competitor?** No (static gating; now deprecated).
- **Type:** software artifact + commercial service.

### 17. gotoHuman
- **Year:** 2024 to 2025 (exact launch year not stated on the homepage).
- **Authors / company:** gotoHuman.
- **URL:** https://www.gotohuman.com/
- **What it does:** a hosted human review inbox for AI workflows. The developer defines review forms, then workflows request reviews via SDK, HTTP, LangGraph, n8n/Make or an MCP server. Reviewers approve or edit in an "Agent Inbox" (email/Slack notifications), results return by webhook, and reviewer feedback can be stored as agent memory. No risk-based routing or auto-approval is described.
- **Overlap with AgentPause:** the human-side delivery and feedback capture (a possible source of "past user decisions").
- **What AgentPause would do differently:** gotoHuman is a review UI/infrastructure and does not decide when to ask. AgentPause is the decision layer and could use gotoHuman as a channel.
- **Direct competitor?** No.
- **Type:** commercial product.

### 18. Permit.io Access Request MCP
- **Year:** 2025 (repo created Feb 2025).
- **Authors / company:** Permit.io.
- **URL:** https://docs.permit.io/ai-security/access-request-mcp/overview (code: https://github.com/permitio/permit-mcp)
- **What it does:** an MCP server exposing tools for access requests (`create_access_request`, approve/deny) and one-time **operation approvals** (`create_operation_approval`, list/approve/deny). The trigger is a **policy decision**: the tool calls `permit.check()`, and a deny leads the agent to request access or approval. Reviewers act in embedded UI elements or the API. Approval grants a role that should be revoked after the one-time action. Tutorials pause via LangGraph `interrupt()`.
- **Overlap with AgentPause:** policy-based escalation to a human, with audit.
- **What AgentPause would do differently:** Permit's trigger is authorization policy (ReBAC/ABAC-style allow/deny), not contextual timing or uncertainty. AgentPause could consume a Permit decision as one "consequence/permission" signal.
- **Direct competitor?** No.
- **Type:** software artifact (MIT) + commercial.

### 19. Auth0 for AI Agents: Asynchronous Authorization (CIBA)
- **Year:** 2025 (developer preview Apr 2025; GA blog 19 Nov 2025).
- **Authors / company:** Auth0 (Okta).
- **URL:** https://auth0.com/blog/auth0-for-ai-agents-generally-available/ ; https://auth0.com/docs/get-started/authentication-and-authorization-flow/client-initiated-backchannel-authentication-flow/user-authorization-with-ciba
- **What it does:** an agent working in the background starts a CIBA request (`/bc-authorize`) with a 64-char **binding message** and optional **Rich Authorization Request** details (e.g., amount and accounts). The user approves via a Guardian push notification, or email for longer expiries. The agent polls and receives a token only after approval. Every request needs fresh consent.
- **Overlap with AgentPause:** asynchronous, out-of-band ASK_HUMAN that lets the agent keep working while waiting. This is relevant to DEFER and interruption-cost choices (push vs. email).
- **What AgentPause would do differently:** Auth0 provides the secure consent channel and token binding, but the decision to ask is entirely the app's. AgentPause would decide when CIBA is warranted and what explanation goes into the binding message/RAR.
- **Direct competitor?** No (complementary infrastructure).
- **Type:** commercial product.

### 20. MCP elicitation
- **Year:** 2025. Introduced in spec 2025-06-18 (form mode); **URL mode** added in 2025-11-25.
- **Authors / company:** Model Context Protocol project (open specification).
- **URL:** https://modelcontextprotocol.io/specification/2025-06-18/client/elicitation ; https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation
- **What it does:** a server sends `elicitation/create` with a human-readable `message` ("explaining why the interaction is needed") and a flat JSON `requestedSchema` (form), or a URL for out-of-band sensitive flows (credentials, OAuth, payments). The user responds `accept`, `decline` or `cancel`. Clients SHOULD show which server is asking, allow decline, rate-limit, and make clear what is requested and why. `URLElicitationRequiredError` (-32042) blocks a call until a URL elicitation is done.
- **Overlap with AgentPause:** the standard wire protocol for CLARIFY/ASK_HUMAN from tools, including a "why" message and a three-way response (accept/decline/cancel, where cancel ≈ "ask again later").
- **What AgentPause would do differently:** the spec defines *how* to ask, never *when*. Rate limiting is the only hint at interruption cost. AgentPause can sit in an MCP client or proxy and decide when an elicitation (or a self-initiated ask) is worth its cost.
- **Direct competitor?** No (protocol AgentPause should speak).
- **Type:** open specification.

### 21. Long tail of OSS "agent action firewall / approval gateway" projects
All verified on GitHub (stars as of Oct 2026). They share a pattern: intercept the tool call, apply policy or risk rules, hold for human approval, audit.
- **Phantasm** (2024; https://github.com/edwinkys/phantasm, ~200★): an approval server, dashboard and client library. Agents send approval requests, approvers can edit parameters, and requests are load-balanced across approvers.
- **Cordum** (2026; https://github.com/cordum-io/cordum, ~500★): a source-available "Agent Control Plane" and "action firewall". It enforces policy and human approval before risky tool calls, shell commands and production changes, and includes "Cordum Edge" for Claude Code.
- **AEGIS** (2026; https://github.com/Justin0504/Aegis, ~540★; paper arXiv 2603.12621, "AEGIS: No Tool Call Left Unchecked", Yuan, Su, Zhao, 13 Mar 2026): a pre-execution firewall with argument extraction, content-based risk scanning, composable policies, high-risk calls **held for human approval**, and a tamper-evident audit trail. It reports blocking 48/48 attacks with a 1.2% false-positive rate on 500 benign calls.
- **AgentSafe / Decionis** (2026; https://github.com/decionis/agent-safe-pipeline, ~690★): an HTTP gateway that asks the Decionis control plane for **`ALLOW` / `ESCALATE` / `BLOCK`**. ESCALATE goes to "Presence", described as an "adaptive human verification layer", and every decision carries a signed "Decision Dossier" recording what was proposed, decided and **why**.
- **Overlap with AgentPause:** a mediation point between agent and environment, tri-state decisions (AgentSafe's ALLOW/ESCALATE/BLOCK is very close to CONTINUE/ASK_HUMAN/BLOCK), and recorded rationales.
- **What AgentPause would do differently:** these gateways are security and compliance oriented (policy and attack detection). None models uncertainty, intent ambiguity, task progress or interruption cost, none has CLARIFY/DEFER or counterfactual timing explanations, and none ships a policy-comparison experiment harness.
- **Direct competitor?** Partial: same architectural position and vocabulary, different objective (security enforcement vs. well-timed human involvement).
- **Type:** software artifacts. AEGIS is both (paper + code). Decionis is commercial behind an open-core gateway.

---

## 3. Coding agents

### 22. Claude Code permission modes, rules, and auto mode (classifier)
- **Year:** 2025 for permission modes/rules. Auto mode launched as a research preview in March 2026; the Anthropic Engineering post is dated 25 Mar 2026. Docs now say auto mode is the built-in starting mode for interactive sessions from v2.1.283.
- **Authors / company:** Anthropic.
- **URL:** https://code.claude.com/docs/en/permission-modes ; https://www.anthropic.com/engineering/claude-code-auto-mode
- **What it does:**
  - **Modes:**
    - `default` (Manual): reads only run without asking.
    - `acceptEdits`
    - `plan`
    - **`auto`**: everything runs, with background safety checks.
    - `dontAsk`: anything that would prompt is denied.
    - `bypassPermissions`
  - **Rules:** permission rules (`allow` / `ask` / `deny`) layer on top. Some actions are never auto-approved (explicit ask rules, org-gated connector tools, `AskUserQuestion`, protected paths).
  - **Auto mode tiers:** (1) allowlist and narrow user rules; (2) in-project file edits are allowed without a classifier, since they are reviewable via version control; (3) everything else goes to a **transcript classifier** (Sonnet-class model) that stands in for the human approver:
    - **Input:** sees user messages, tool calls and CLAUDE.md. It is "reasoning-blind": assistant prose and tool outputs are stripped.
    - **Two stages:** a fast filter that errs toward blocking, then chain-of-thought on flagged items.
    - **Judgement:** real-world effect, conservative **user intent** (agent-chosen actions are unauthorized until the user says otherwise; vague requests don't authorize destructive batch actions), a **trust boundary** (repo and configured remotes), and 20+ block rules (destruction/exfiltration, security degradation, crossing trust boundaries, bypassing review). Claude Code runs `git status` before destructive commands so the classifier knows whether uncommitted work would be lost (a **reversibility** signal).
    - **Conversation boundaries:** user-stated boundaries ("don't push", "wait until I review") act as block signals, and user approval in conversation can clear blocks.
  - **When a human is involved:** a block goes back to the agent (reason names the matched rule, e.g., `[Data Exfiltration]`) to try a safer path. After **3 consecutive or 20 total blocks**, auto mode pauses and reverts to prompting the human; these thresholds are not configurable.
  - **Published error rates** (eng. post): FPR 0.4% on 10k real actions; FNR 17% on 52 real overeager actions; FNR 5.7% on synthetic exfiltration.
- **Overlap with AgentPause:** substantial. A model-based per-action decision that uses user intent/authorization, scope or trust boundary, irreversibility cues, and conversation-stated user preferences. It reports precision/recall-style trade-offs (false positives = unnecessary friction).
- **What AgentPause would do differently:**
  - **Outcomes and signals:** auto mode's output is effectively allow / block (+ escalate after a fixed count). It does not choose *between* asking now, clarifying intent, or deferring, and it ignores model uncertainty, task progress and interruption cost.
  - **History:** user history is limited to what is in the transcript and static rules.
  - **Explanations:** go to the agent (rule label), not counterfactual explanations to the user.
  - **Fallback:** the 3/20 thresholds are a fixed heuristic, which AgentPause would replace with an expected-value-of-asking decision.
  - **Evaluation:** auto mode was evaluated internally, not via an open harness comparing policies.
- **Direct competitor?** **Partial, and the closest commercial analogue for "smart, context-aware permissioning".** It decides *whether to allow*, not *when to involve the human*.
- **Type:** commercial product.

### 23. Claude Code hooks (PreToolUse `permissionDecision`)
- **Year:** 2025 to 2026.
- **Authors / company:** Anthropic.
- **URL:** https://code.claude.com/docs/en/hooks
- **What it does:** a PreToolUse hook (external program) returns `permissionDecision` ∈ {`allow`, `deny`, `ask`, `defer`} plus `permissionDecisionReason`:
  - `ask`: prompts the user, and the **reason is shown to the user in the permission prompt**.
  - `deny`: the reason is shown to Claude.
  - **`defer`**: "exits gracefully so the tool can be resumed later" (only for non-interactive `claude -p` runs).

  A PostToolUse `classifierContext` field can annotate results for the auto-mode classifier.
- **Overlap with AgentPause:** the decision vocabulary maps almost one-to-one: allow ≈ CONTINUE, deny ≈ BLOCK, ask ≈ ASK_HUMAN (with a user-visible reason), defer ≈ DEFER.
- **What AgentPause would do differently:** hooks are an extension point with no built-in policy. **AgentPause could be deployed directly as a Claude Code PreToolUse hook.** This is a strong integration and evaluation path, not a competitor.
- **Direct competitor?** No (integration target).
- **Type:** commercial product (extension API).

### 24. OpenAI Codex (CLI / IDE / app): approval policies, auto-review, smart approvals
- **Year:** 2025 (Codex CLI repo created Apr 2025). Auto-review / "guardian" reviewer and granular policies arrived in 2026.
- **Authors / company:** OpenAI.
- **URL:** https://learn.chatgpt.com/codex/agent-approvals-security (canonical developers.openai.com/codex/agent-approvals-security redirects there) ; rules: https://learn.chatgpt.com/codex/rules ; repo: https://github.com/openai/codex
- **What it does:**
  - **Approval policies and sandbox:**
    - `approval_policy`: `on-request` (asks before leaving the sandbox or using network), `never`, or `granular` (per category: sandbox approvals, execpolicy rules, MCP prompts, `request_permissions`, skill scripts). `untrusted` is retired.
    - Sandbox modes: `read-only`, `workspace-write`, `danger-full-access`.
    - MCP/app tools that advertise side effects prompt; tools annotated destructive always prompt.
  - **Auto-review** (`approvals_reviewer = "auto_review"`): a reviewer agent evaluates actions that already need approval.
    - **Concerns:** exfiltration, credential probing, persistent security weakening, destructive actions, plus a **user-authorization assessment**.
    - **Outcomes:** a **risk level** (low/medium → proceed; high → needs sufficient user authorization; critical → deny).
    - **UI:** statuses Reviewing / Approved / Denied / Aborted / Timed out, with risk level and authorization assessment.
    - **Failures:** fail closed.
    - **Admin:** admins can replace the policy text (`guardian_policy_config`).
  - **Rules and smart approvals:** execpolicy `prefix_rule(pattern, decision=allow|prompt|forbidden, justification=...)`. **Smart approvals** (on by default) "may propose a `prefix_rule`" during escalations, and approving "don't ask again" writes rules to `~/.codex/rules/default.rules`. This is a mechanism for **learning from past user decisions**.
- **Overlap with AgentPause:**
  - A risk-level + user-authorization assessment per escalation, shown to the user.
  - Rules distilled from prior approvals.
  - Granular per-category interactivity: something like a user-customized policy.
- **What AgentPause would do differently:**
  - Signals and outcomes: auto-review only rates actions that already crossed a sandbox boundary. It does not consider uncertainty, progress or interruption cost, and has no CLARIFY/DEFER.
  - Learning: rule learning is literal command-prefix memoization, not a preference model.
  - Explanations and evaluation: no counterfactual explanations and no policy-comparison framework.
- **Direct competitor?** **Partial (close)**: risk-tiered automated reviewer + history-derived rules.
- **Type:** software artifact (Apache-2.0 CLI) + commercial product.

### 25. Cline auto-approve
- **Year:** 2024+ (repo Jul 2024).
- **Authors / company:** Cline Bot Inc.
- **URL:** https://docs.cline.bot/features/auto-approve
- **What it does:** per-category toggles: read project or all files, edit project or all files, execute **safe** commands, execute all commands, browser, MCP, and notifications. "Safe" is not an allowlist: **the model sets a `requires_approval` flag per command** based on command and arguments. YOLO mode auto-approves everything. OS notifications fire when approval is required.
- **Overlap with AgentPause:** a per-category user-customized policy, plus the agent self-assessing risk per action.
- **What AgentPause would do differently:** the agent's self-reported flag is a single uncalibrated signal from the same model that proposes the action. AgentPause uses an independent, multi-signal decision with explanations and timing.
- **Direct competitor?** Partial.
- **Type:** software artifact (Apache-2.0).

### 26. Roo Code auto-approve
- **Year:** 2024+ (repo Oct 2024).
- **Authors / company:** Roo Code Inc.
- **URL:** https://roocodeinc.github.io/Roo-Code/features/auto-approving-actions (redirect from docs.roocode.com)
- **What it does:**
  - **Categories with documented risk labels:** read (Medium), write (High, with a post-write delay), browser (Medium), MCP (Medium-High, per tool), mode switch (Low), subtasks (Low), execute (High; allowlist/denylist with longest-prefix matching, deny wins, dangerous substitutions never auto-approved).
  - **"Answer follow-up questions" (Low):** **auto-selects the first suggested answer after a 1 to 300 s timeout (default 60 s)**, cancelled by any user action.
- **Overlap with AgentPause:** a user-customized per-category policy, and a **timeout-based fallback for clarification questions**. This is a primitive answer to "what if the human doesn't respond", relevant to DEFER and interruption-cost reasoning.
- **What AgentPause would do differently:** Roo's risk labels are static documentation, not inputs to a decision. AgentPause would decide per instance, and could pick the timeout/default dynamically from consequence and reversibility.
- **Direct competitor?** Partial.
- **Type:** software artifact (Apache-2.0).

### 27. Cursor agent run modes and Auto-review classifier
- **Year:** 2026. Auto-review shipped in Cursor 3.6 (29 May 2026). "Ask Every Time" was deprecated in 3.5 (22 May 2026). A Workspace read-approval policy came in 3.23 (1 Oct 2026).
- **Authors / company:** Anysphere (Cursor).
- **URL:** https://cursor.com/docs/agent/security/run-modes ; https://cursor.com/docs/agent/security
- **What it does:**
  - **Modes:** Auto-review (recommended default), Allowlist, Run Everything (formerly "YOLO"-style).
  - **Auto-review order:** allowlisted calls run; other shell commands run in a sandbox if possible; everything else (and sandbox-escaping reruns) goes to a **classifier** (Gemini 3.5 Flash Lite, Claude 4.5 Haiku fallback).
  - **Classifier inputs:** can read local files read-only (e.g., the script a command would run) and uses plain-English **`allow_instructions` / `block_instructions`** from `permissions.json` (user, project or team).
  - **Outcomes:** auto-run or block. "If the agent still believes the action is justified", **Cursor shows an approval prompt**.
  - **Approval cards** (outside-workspace reads) show path and reason. Separate protections exist for browser, file deletion and external files.
- **Overlap with AgentPause:** a model-based decision per call with user-written natural-language preferences (≈ "user preferences" signal) and an escalate-to-human path.
- **What AgentPause would do differently:** Cursor's goal is safe auto-execution (block vs. run). The ask path is agent-initiated after a block. There are no uncertainty, progress or interruption-cost signals, no DEFER, and no counterfactual explanations.
- **Direct competitor?** Partial.
- **Type:** commercial product.

### 28. VS Code / GitHub Copilot agent approvals and Assisted permissions
- **Year:** 2025 to 2026.
- **Authors / company:** Microsoft / GitHub.
- **URL:** https://code.visualstudio.com/docs/agents/approvals
- **What it does:**
  - **Permission levels (`chat.permissions.default`):**
    - **Manual permissions:** tool, URL and terminal approval settings apply.
    - **Assisted permissions (experimental):** **an LLM judge assesses each tool call, and calls it doesn't approve need confirmation.** Requires `chat.assistedPermissions.enabled` and folder isolation; the docs warn it "can make mistakes".
    - **Allow all.**
    - **Autopilot:** auto-approves tools, retries errors, and **answers questions that would otherwise block progress**. "Advanced Autopilot" uses a small model to decide whether the request is complete.
  - **Approval scopes:** once, session, workspace, or always. `chat.tools.eligibleForAutoApproval` can force manual approval for a tool.
  - **Terminal rules:** per-subcommand regex true/false, where `false` means "require approval".
  - **URL approvals:** two steps (request vs. response).
- **Overlap with AgentPause:** an LLM-judged per-call approval plus user-scoped remembered approvals (history), and a mode that auto-answers clarifications (the anti-CLARIFY extreme).
- **What AgentPause would do differently:** Assisted permissions is binary (approve vs. ask) with an opaque judge. AgentPause would add explicit signals, DEFER/CLARIFY, explanations, and evaluation of when Autopilot-style auto-answering is acceptable.
- **Direct competitor?** Partial.
- **Type:** software (VS Code OSS) + commercial (Copilot).

### 29. Gemini CLI policy engine
- **Year:** 2025 (policy engine commits Sep to Oct 2025).
- **Authors / company:** Google.
- **URL:** https://geminicli.com/docs/reference/policy-engine/
- **What it does:** TOML rules matching `toolName`, `argsPattern` (regex over JSON args), `commandPrefix`/`commandRegex`, MCP server, subagent and approval mode (`default`, `autoEdit`, `plan`, `yolo`). Rules return `allow`, `deny` or `ask_user`; the highest priority wins, with tiers Default < Extension < User < Admin. `ask_user` becomes deny in non-interactive mode. Shell redirection triggers ask by default. No dynamic or risk-based logic.
- **Overlap with AgentPause:** an allow/deny/ask decision vocabulary with layered user/admin customization (≈ the user-customized policy baseline).
- **What AgentPause would do differently:** Gemini CLI uses purely static pattern rules. AgentPause is contextual and adaptive.
- **Direct competitor?** No.
- **Type:** software artifact (Apache-2.0).

### 30. Devin Desktop (formerly Windsurf) terminal auto-execution levels
- **Year:** 2025 to 2026 (windsurf docs now redirect to docs.devin.ai).
- **Authors / company:** Cognition.
- **URL:** https://docs.devin.ai/desktop/terminal
- **What it does:** four levels: Disabled, Allowlist Only, **Auto** ("the agent uses its judgment" about whether a command is safe; risky ones need approval; premium models only), and Turbo (everything except denylist). Denylist beats allowlist.
- **Overlap with AgentPause:** agent self-judged risk gating per command.
- **What AgentPause would do differently:** Devin's "judgment" is undocumented and single-signal. AgentPause would make it explicit, multi-signal, explainable and evaluable.
- **Direct competitor?** Partial.
- **Type:** commercial product.

### 31. Warp agent permissions ("Agent decides")
- **Year:** 2025 to 2026.
- **Authors / company:** Warp.
- **URL:** https://docs.warp.dev/agents/using-agents/agent-profiles-permissions
- **What it does:** per permission type (apply diffs, read files, create plans, execute commands, interact with running commands, **ask clarifying questions**), choose **Agent decides** ("act autonomously when it's confident, but prompt for approval when uncertain"), Always ask, Always allow, or Never. Command allowlist/denylist; the denylist overrides.
- **Overlap with AgentPause:** an explicitly **uncertainty-based ask/act decision** per category, and clarifying questions as a separately governed action type.
- **What AgentPause would do differently:** Warp relies on the agent's own (uncalibrated) confidence only, with no reversibility, progress, cost or history modelling and no explanation. AgentPause separates the decider from the actor and fuses signals.
- **Direct competitor?** Partial.
- **Type:** commercial product.

### 32. goose permission modes (Smart Approval)
- **Year:** 2025 (repo Aug 2024; now under aaif-goose).
- **Authors / company:** Block (now Agentic AI Foundation project).
- **URL:** https://goose-docs.ai/docs/guides/managing-tools/goose-permissions
- **What it does:** Completely Autonomous, Manual Approval, **Smart Approval** (auto-approves low-risk actions and flags others, based on "the action's impact"; read/write classification is best-effort and interpreted by the LLM provider), and Chat Only. Per-tool Always Allow / Ask Before / Never Allow.
- **Overlap with AgentPause:** an LLM-judged risk gate + per-tool user customization.
- **What AgentPause would do differently:** goose classifies essentially read vs. write. AgentPause uses richer signals, timing and explanations.
- **Direct competitor?** Partial.
- **Type:** software artifact (Apache-2.0).

### 33. OpenHands confirmation mode + security analyzer (`ConfirmRisky`)
- **Year:** 2024. Confirmation mode commit 11 Jul 2024; Security Analyzer 13 Aug 2024. The SDK (repo Aug 2025) formalizes the policies.
- **Authors / company:** All Hands AI / OpenHands community.
- **URL:** https://docs.openhands.dev/sdk/guides/security
- **What it does:** a **security analyzer** assigns each action a risk of LOW / MEDIUM / HIGH / UNKNOWN. The default is the **LLM analyzer, where the agent annotates its own action with a `security_risk`**; ensemble analyzers take the max. A **confirmation policy** decides whether to ask: `AlwaysConfirm`, `NeverConfirm`, or **`ConfirmRisky(threshold)`** (docs recommend HIGH, MEDIUM for stricter use).
- **Overlap with AgentPause:** this is literally three of AgentPause's comparison baselines (full autonomy, always confirm, fixed risk threshold) as pluggable policy objects, with a separable risk-scoring component.
- **What AgentPause would do differently:**
  - **Signals:** risk is a single ordinal label (self-reported by default).
  - **Decision:** no uncertainty / reversibility / progress / interruption-cost fusion, no EV-of-asking, and no CLARIFY/DEFER.
  - **Explanations:** none.
  - **Evaluation:** no harness to compare the policies on outcomes and burden.

  AgentPause's adaptive policy could be implemented as a new OpenHands confirmation policy and benchmarked against `ConfirmRisky`.
- **Direct competitor?** **Partial**: the cleanest existing OSS implementation of the "fixed risk threshold" baseline.
- **Type:** software artifact (MIT).

---

## 4. Computer-use / browser agents and enterprise agent platforms

### 34. OpenAI Operator (Computer-Using Agent)
- **Year:** 2025 (Operator System Card dated 23 Jan 2025, updated 11 Mar 2025).
- **Authors / company:** OpenAI.
- **URL:** https://cdn.openai.com/operator_system_card.pdf (launch post https://openai.com/index/introducing-operator/ returned HTTP 403 to automated fetch)
- **What it does:**
  - **Risk policy and confirmations:** a risky-action policy requires human oversight and explicit confirmation for financial transactions, sending email, deleting calendar events and similar actions, and proactive refusal for stock trading and banking. The **model is trained to ask for confirmation before finalizing state-changing actions**. On 607 tasks across 20 risky-action categories, confirmation **recall was 92%**. Confirmations reduced the risk of model mistakes by "approximately 90%". Baseline: 13/100 tasks had errors, of which 5 were hard to reverse.
  - **Proactive refusals:** 94% recall.
  - **Watch mode:** on sensitive sites, execution pauses when the user is inactive or navigates away.
  - **Takeover:** for logins and payment details.
  - **Prompt-injection monitor.**
- **Overlap with AgentPause:** explicit reasoning about reversibility and severity (the card distinguishes errors reversible "within a few minutes" from irreversible ones), an ask-before-final-commit timing heuristic, and user-attention-aware pausing (watch mode ≈ an interruption/attention signal).
- **What AgentPause would do differently:**
  - **Where the policy lives:** the confirmation policy is baked into model weights. It is not configurable, inspectable or explainable, and it is evaluated only by **recall**; the card reports no unnecessary-confirmation rate.
  - **What AgentPause adds:**
    - An external, model-agnostic policy.
    - Explicit trade-off of both error types (missed confirmations vs. interruption cost).
    - User-customizable thresholds.
    - Explanations of timing ("asked now because the next step is irreversible").
- **Direct competitor?** Partial (product behaviour, not a reusable component).
- **Type:** commercial product.

### 35. ChatGPT agent
- **Year:** 2025 (System Card dated 17 Jul 2025).
- **Authors / company:** OpenAI.
- **URL:** https://cdn.openai.com/pdf/839e66fc-602c-48bf-81d3-b21eacc3459d/chatgpt_agent_system_card.pdf (help article https://help.openai.com/en/articles/11752874-chatgpt-agent returned 403 to automated fetch)
- **What it does:** "trained ChatGPT agent to ask the user for confirmations before finalizing actions that affect the state of the world" (purchases, sending email).
  - **Confirmation recall:** 91.0% (Operator 4o 90.8%, Operator o3 92.1%).
  - **Critical confirmation recall:** 100% for editing permissions, 99.9% for high-stakes communications, 100% for financial transactions.
  - **Sensitive-data tests:** 8/8 mistaken-sharing tests passed.
  - **Watch mode** for the rest of a trajectory once in a sensitive context (logged into email or banking). Users can take over or interrupt.
- **Overlap with AgentPause:** same as Operator. Severity-tiered confirmation behaviour with category-level recall evaluation.
- **What AgentPause would do differently:** same as Operator. OpenAI reports recall only (no precision or interruption burden), the behaviour is implicit in the model, and there is no explanation or user-tunable policy.
- **Direct competitor?** Partial.
- **Type:** commercial product.

### 36. Claude for Chrome / Claude in Chrome
- **Year:** 2025 (launch post 25 Aug 2025; updates 24 Nov and 18 Dec 2025).
- **Authors / company:** Anthropic.
- **URL:** https://claude.com/blog/claude-for-chrome ; https://support.claude.com/en/articles/12902428-using-claude-in-chrome-safely
- **What it does:**
  - **Site permissions:** grant or revoke per site.
  - **Action confirmations** before high-risk actions (publishing, purchasing, sharing personal data; later docs add downloading files and entering sensitive information). Asks before accessing financial sites.
  - **Modes:** "Automatically approve" (default in the Cowork side panel), where Claude **screens each of its own actions for risk and hidden malicious instructions**, runs lower-risk ones, and **blocks or pauses for approval** when a safety classifier flags risk; or "Manually approve" every action.
  - **Prompt-injection results:** attack success fell from 23.6% to 11.2% in autonomous mode after mitigations.
- **Overlap with AgentPause:** classifier-driven per-action risk screening that chooses between continue, pause-for-approval and block.
- **What AgentPause would do differently:** Claude in Chrome is focused on safety and injection. It has no signals for progress, intent ambiguity or interruption cost, no DEFER/CLARIFY distinction, no user-facing counterfactual explanation, and is not a reusable component.
- **Direct competitor?** Partial.
- **Type:** commercial product.

### 37. Gemini in Chrome agentic browsing security (User Alignment Critic + confirmations)
- **Year:** 2025 (Google Security blog, 8 Dec 2025, by Nathan Parker).
- **Authors / company:** Google (Chrome security).
- **URL:** https://blog.google/security/architecting-security-for-agentic/
- **What it does:**
  - **User Alignment Critic:** a separate Gemini model that sees only action metadata (not web content) and checks whether each planned action serves the user's stated goal. It vetoes misaligned actions back to the planner, and **repeated failures return control to the user**.
  - **Confirmations:** required before navigating to sensitive sites (deterministic list), signing in via Password Manager, and purchases, payments, sending messages and other consequential actions (**model-based checks**). The agent pauses to ask permission or asks the user to complete the step.
  - **Work log** for transparency; the user can take over or stop at any time.
- **Overlap with AgentPause:**
  - A hybrid of deterministic and model-based triggers for asking.
  - Intent alignment as a decision signal.
  - Escalation to the user after repeated vetoes, similar to Claude Code's 3/20 rule.
  - A transparent work log.
- **What AgentPause would do differently:** Chrome's design is fixed and security-oriented. AgentPause adds uncertainty, progress and interruption-cost reasoning, DEFER/CLARIFY, counterfactual explanations, and an evaluation harness.
- **Direct competitor?** Partial.
- **Type:** commercial product.

### 38. Gemini Computer Use `safety_decision`
- **Year:** 2025 (Gemini 2.5 Computer Use model; month not confirmed from a primary source).
- **Authors / company:** Google DeepMind / Google.
- **URL:** https://ai.google.dev/gemini-api/docs/computer-use
- **What it does:** an internal **per-action safety system** labels each proposed action as regular/allowed, **`require_confirmation`**, or blocked. The function call carries `safety_decision` with a **`decision` and an `explanation`**. Developers must show the explanation to the end user and set `safety_acknowledgement` if the user confirms. System-instruction overrides express only a preference, and the model may still require confirmation.
- **Overlap with AgentPause:** a per-step continue / ask / block classification **with a natural-language explanation passed to the user**. This is the closest commercial API to AgentPause's output contract.
- **What AgentPause would do differently:** Google's classifier is opaque and provider-controlled. Its explanation is a safety rationale, not a timing/counterfactual one. It has no CLARIFY or DEFER, no user-history or interruption-cost modelling, and no policy comparison. AgentPause could wrap this signal as one input.
- **Direct competitor?** Partial.
- **Type:** commercial API.

### 39. Amazon Bedrock Agents: user confirmation and return of control
- **Year:** 2024 to 2025 (AWS ML blog on HITL confirmation, 9 Apr 2025, by Clement Perrot, Maira Ladeira Tanke, Mark Roy, Ryan Sachs).
- **Authors / company:** AWS.
- **URL:** https://docs.aws.amazon.com/bedrock/latest/userguide/agents-userconfirmation.html ; https://aws.amazon.com/blogs/machine-learning/implement-human-in-the-loop-confirmation-with-amazon-bedrock-agents/
- **What it does:** **user confirmation** is enabled per action by the developer. When the agent decides to call it, `InvokeAgent` returns `returnControl` with the invocation inputs, and the app presents CONFIRM/DENY (`confirmationState`). **Return of control** (`customControl = RETURN_CONTROL`) hands the whole execution to the application, which can edit parameters.
- **Overlap with AgentPause:** a confirm/deny gate and a hand-back-control mechanism.
- **What AgentPause would do differently:** Bedrock's gates are static per action. AgentPause chooses dynamically and explains.
- **Direct competitor?** No.
- **Type:** commercial product.

### 40. Amazon Nova Act human-in-the-loop
- **Year:** 2025.
- **Authors / company:** AWS (Amazon AGI Labs).
- **URL:** https://docs.aws.amazon.com/nova-act/latest/userguide/hitl.html
- **What it does:** two patterns, both implemented as developer **callbacks** at chosen points:
  - **Human approval:** an asynchronous decision with a screenshot, sent to a reviewer via a browser UI.
  - **UI takeover:** live remote browser control for CAPTCHA and login/MFA.

  An optional managed Human Intervention Service (CDK) adds Slack/email notifications and a supervisor dashboard. Best practices include **timeouts set by session age**.
- **Overlap with AgentPause:** an ask-vs-takeover distinction and attention to timeouts.
- **What AgentPause would do differently:** in Nova Act, the developer decides intervention points. AgentPause decides them at runtime.
- **Direct competitor?** No.
- **Type:** software (SDK) + commercial.

### 41. Salesforce Agentforce (escalation and guardrails)
- **Year:** 2024 to 2025.
- **Authors / company:** Salesforce.
- **URL:** https://trailhead.salesforce.com/content/learn/modules/trusted-agentic-ai/explore-agentforce-guardrails-and-trust-patterns
- **What it does:** escalation to a human representative is governed by admin-written **topic instructions** ("Always…", "Never…", "If x, then y…"). Trust patterns include AI-human handoffs and oversight dashboards, with the Einstein Trust Layer for masking and audit. The verified material does not describe per-action confirmation settings.
- **Overlap with AgentPause:** rule-based handoff to humans.
- **What AgentPause would do differently:** Agentforce's escalation is instruction-based and static. AgentPause is per-action, adaptive, explained and evaluated.
- **Direct competitor?** No.
- **Type:** commercial product.

---

## 5. Guardrail systems

### 42. NVIDIA NeMo Guardrails
- **Year:** 2023 (repo Apr 2023).
- **Authors / company:** NVIDIA.
- **URL:** https://docs.nvidia.com/nemo/guardrails/latest/index.html
- **What it does:** programmable rails: input, retrieval, dialog (Colang), **execution** (validate tool inputs/outputs), and output. Rails block, alter or validate automatically. The docs describe no human approval or escalation.
- **Overlap with AgentPause:** an interception layer around tool execution.
- **What AgentPause would do differently:** NeMo targets automated policy enforcement. AgentPause targets the human-involvement decision.
- **Direct competitor?** No.
- **Type:** software artifact.

### 43. Guardrails AI
- **Year:** 2023 (repo Jan 2023).
- **Authors / company:** Guardrails AI.
- **URL:** https://guardrailsai.com/docs/concepts/error_remediation
- **What it does:** input/output validators (Guardrails Hub) with `OnFailAction` ∈ {NOOP, EXCEPTION, REASK, FIX, FILTER, REFRAIN, FIX_REASK} or custom actions. No human escalation.
- **Overlap with AgentPause:** the idea of a menu of remediation actions on a detected issue.
- **What AgentPause would do differently:** Guardrails AI remediates LLM outputs automatically. AgentPause's actions involve the human and timing.
- **Direct competitor?** No.
- **Type:** software artifact (Apache-2.0).

### 44. Invariant Guardrails (Invariant Labs)
- **Year:** 2024 to 2025 (repo May 2024).
- **Authors / company:** Invariant Labs.
- **URL:** https://github.com/invariantlabs-ai/invariant
- **What it does:** rule-based guardrails written in a Python-inspired language (`raise "msg" if: ...`) over messages and **tool-call flows** (e.g., data from tool A flowing into tool B). Deployed via a Gateway in front of LLM/MCP. Violations error out the request. No HITL is described.
- **Overlap with AgentPause:** trace-aware policies over the agent's trajectory.
- **What AgentPause would do differently:** Invariant enforces hard blocks only. AgentPause adds graded human involvement and timing, and could consume Invariant rule hits as a "severity" signal.
- **Direct competitor?** No.
- **Type:** software artifact (Apache-2.0).

### 45. Meta LlamaFirewall
- **Year:** 2025 (arXiv 2505.03574, submitted 6 May 2025; Sahana Chennabasappa, Joshua Saxe, et al.).
- **Authors / company:** Meta.
- **URL:** https://github.com/meta-llama/PurpleLlama/tree/main/LlamaFirewall ; paper https://arxiv.org/abs/2505.03574
- **What it does:** a layered agent guardrail with three scanners plus regex/custom scanners:
  - **PromptGuard 2:** jailbreak/injection classifier.
  - **AlignmentCheck:** chain-of-thought auditor for goal hijacking / drift from user intent.
  - **CodeShield:** insecure-code static analysis.

  **The source code defines `ScanDecision` ∈ {`ALLOW`, `HUMAN_IN_THE_LOOP_REQUIRED`, `BLOCK`}**, with reason and score per result.
- **Overlap with AgentPause:** a tri-state output that includes an explicit "human required" decision, plus an intent-alignment signal.
- **What AgentPause would do differently:** LlamaFirewall triggers on security findings, not usefulness or timing. It has no uncertainty, progress or interruption-cost signals, no CLARIFY/DEFER, and no counterfactual explanations. AgentPause could treat AlignmentCheck as an input signal.
- **Direct competitor?** Partial (shares the decision vocabulary).
- **Type:** both (paper + code).

---

## 6. Long-tail OSS / research repos on *adaptive* asking (low adoption, 2026)

These are small GitHub repos (mostly under 30 stars, unreviewed). I include them because they are conceptually the nearest to AgentPause's "adaptive when-to-ask" idea. All were checked by reading their READMEs.

| Repo | What it is | Relation to AgentPause |
|---|---|---|
| **TELEMACHUS**: https://github.com/gdtsitlauri/telemachus | "When should an AI agent look, think, ask or act?" A gate decides act vs. acquire information vs. escalate to a human. A single threshold is calibrated with Learn-then-Test for a certified error rate, with online updates under shift. Evaluated in 4 domains. | Formal risk-controlled escalation gate. Single threshold, no reversibility, progress or interruption-cost model, no explanations. **Conceptual competitor for the "calibrated threshold" baseline.** |
| **ask-or-act / Kiri**: https://github.com/aryan597/ask-or-act (rule library: https://github.com/aryan597/kiri-gate) | A 120-action benchmark of whether models know when to ask. Reports models' AUROC 0.95 to 0.996 at spotting should-ask actions, yet 4 to 6 unrecoverable "slips" when the model decides alone. The Kiri rule is READ → act; UNDOABLE → act if confident else ask; IRREVERSIBLE/EXTERNAL → always ask. It costs about 21 extra questions per 120 actions. | **Two-signal (reversibility × confidence) policy plus a small benchmark.** Very close in spirit to AgentPause's adaptive policy and evaluation, but far narrower in signals, outcomes and explanation. |
| **xtid / when-to-ask**: https://github.com/ahmd-mohsin/when-to-ask | A de-risk experiment testing whether internal hidden-state divergence across parallel trajectories identifies the best moments for `ask_human()` in coding agents. It builds on HiL-Bench and ClarifyGPT baselines. | Directly about *timing* of asks (lead time). A research prototype, an uncertainty signal only. |
| **Learning When to Intervene**: https://github.com/Davuri124/Human_Intervention_Points | A PPO policy over model uncertainty (entropy, MC-dropout) to decide human intervention points in ML pipelines. It beats always/never/threshold/contextual-bandit baselines and uses SHAP explanations. | Learned adaptive intervention policy compared against AgentPause-like baselines, but for tabular ML pipelines, not LLM agents. |
| **Autonomy Learning Loop**: https://github.com/SuganyaNagarajan85/adaptive-autonomy | Dynamically expands or contracts the automation boundary from operational feedback, in simulations vs. a static threshold. | Adaptive autonomy at the fleet level, not per action. |
| **AEGIS (adaptive autonomy)**: https://github.com/RishiM19/AEGIS | Specs plus a TypeScript implementation that combine competence, risk, novelty and uncertainty (min-combined) per action from the agent's track record, with a runtime sentinel. | **Multi-signal, history-based autonomy decisions.** Conceptually close, with no evidence of adoption or evaluation beyond demos. |
| **Curiosity After Competence**: https://github.com/kalyanar/curiosity-after-competence | Experiment code for a Georgia Tech paper (under submission) on keeping trusted agents *interruptible*. | Related to interruption, from the agent-receptiveness side. |

---

## 7. Cross-cutting answers to the three key questions

### Q1. Does anything decide WHEN to ask adaptively from multiple contextual signals?
**No shipping system does what AgentPause proposes.** That would mean a decision-theoretic choice among continue / clarify / ask / defer / block, fusing uncertainty, consequence severity, reversibility, intent ambiguity, task progress, interruption cost, preferences and past decisions. What exists, from most to least adaptive:

1. **Model-based "is this action OK to run unattended?" classifiers:**
   - **Claude Code auto mode:** user intent and authorization, trust boundary, irreversibility cues such as `git status`, conversation-stated boundaries.
   - **Codex auto-review:** risk level + user-authorization assessment.
   - **Cursor Auto-review:** reads local context plus natural-language allow/block instructions.
   - **VS Code Assisted permissions.**
   - **Claude in Chrome** automatic action screening.
   - **Gemini in Chrome:** User Alignment Critic + model-based confirmation checks.
   - **Gemini Computer Use** `safety_decision`.
   - **Magentic-UI ActionGuard judge:** consequences, irreversibility, privacy, effects on others.

   All are essentially **binary safety gates (run vs. block/ask)**. None weigh interruption cost, task progress or model uncertainty, or choose *when* (now vs. later) to involve the user.
2. **Trained-in confirmation behaviour.** OpenAI Operator and ChatGPT agent are trained to confirm before finalizing state-changing actions. They are evaluated by recall only (91 to 92% overall, ~100% for critical categories), with no published false-positive or interruption burden.
3. **Agent self-assessed risk or confidence:** Cline `requires_approval`, OpenHands LLM `security_risk` + `ConfirmRisky`, Warp "Agent decides" (confident → act, uncertain → ask), Devin Desktop "Auto", goose Smart Approval, Kiri (reversibility class × confidence).
4. **Conditional hooks with developer rules:** LangChain `when`, OpenAI `needs_approval` callable, Pydantic `ApprovalRequired`, Vercel `toolApproval`, ADK `require_confirmation` callable, Mastra function (with a documented classifier-probability ≥ 0.7 example), MS Agent Framework `auto_approval_rules`.
5. **Static per-tool flags or modes:** AutoGen, CrewAI, Bedrock, n8n, HumanLayer, Gemini CLI, Roo/Cline categories.

**User history** appears only as memoized approvals: Codex smart approvals proposing `prefix_rule`s, VS Code session/workspace/always scopes, MS Agent Framework standing approvals, Magentic-UI `AUTO_SESSION`, OpenAI Agents SDK `always_approve`, and Claude Code allow rules. Nobody learns a preference model from past decisions.

**Interruption cost / attention** appears only as:
- OpenAI watch mode (pause when the user is inactive or away).
- Roo Code's timeout auto-answer for follow-up questions.
- Nova Act's timeout guidance.
- Claude Code auto mode's 3-consecutive / 20-total escalation thresholds.
- MCP's "clients SHOULD rate-limit".

**Task progress** is not used as a signal by any system I found.

### Q2. Does anything explain why it asked, or give counterfactual timing explanations?
- **"Why" explanations exist in several places, usually as a one-line reason:**
  - Gemini Computer Use `safety_decision.explanation`, which must be shown to the user.
  - Claude Code hook `permissionDecisionReason`, shown in the prompt for `ask`.
  - Codex auto-review risk level + authorization assessment.
  - Copilot Studio AI-stage decision + rationale.
  - Vercel `tool-approval-request.reason`.
  - LangChain `description` callable.
  - MCP elicitation `message`.
  - Auth0 binding message / RAR details.
  - Cursor approval cards (path + reason).
  - AgentSafe/Decionis signed "Decision Dossier".
  - Claude Code auto mode block labels (shown to the agent, not the user).
- **Counterfactual or timing explanations** ("why now and not earlier/later", "what would have had to differ for me to continue"): **none found** in any framework or product.

### Q3. Does anything offer an experiment framework to compare intervention policies?
- **No general-purpose, reusable framework was found.** The nearest:
  - **OpenHands** exposes `AlwaysConfirm` / `NeverConfirm` / `ConfirmRisky(threshold)` as swappable policy objects, but provides no evaluation harness for them.
  - **Magentic-UI** exposes `always` / `never` / `auto-conservative` / `auto-permissive` and has simulated-user infrastructure, but its paper measures help-request rates and user perceptions, not a systematic approval-policy comparison.
  - **AutoGen** `NEVER` / `TERMINATE` / `ALWAYS` are ready-made baselines.
  - Vendors publish internal evaluations: Claude Code auto-mode FPR/FNR, OpenAI confirmation recall, Anthropic and OpenAI prompt-injection rates.
  - Long-tail research repos (ask-or-act, TELEMACHUS, Human_Intervention_Points) compare a few policies in narrow settings.

  An open, framework-agnostic harness that scores policies on both harm avoided and interruption burden would be novel.

---

## Closest competitors and key takeaways

### Closest items (ranked by overlap with AgentPause)
1. **Magentic-UI action guards** (Microsoft Research, 2025; both). Reversibility-tiered baseline + agent guess + LLM judge, with four approval policies (always / never / auto-conservative / auto-permissive), session-level preferences, an APPROVE/DENY/ALTERNATIVE decision set, simulated users and a user study on approval burden. Closest *research platform*; binary, reversibility-centric, no timing or explanations.
2. **Claude Code auto mode + hooks** (Anthropic, 2026; commercial). Most sophisticated contextual permission classifier: intent and authorization, trust boundary, irreversibility, conversation-stated boundaries, published FPR/FNR. Hooks already expose **allow/deny/ask/defer + user-visible reason**, nearly AgentPause's output vocabulary. Missing: uncertainty, progress, interruption cost, CLARIFY, EV-based escalation (it uses fixed 3/20 block counts), and counterfactual explanations.
3. **OpenAI Codex auto-review + smart approvals** (OpenAI, 2026). Risk-level reviewer with user-authorization assessment shown in the UI, plus rules learned from user approvals. Only reviews sandbox escalations; no timing or CLARIFY/DEFER.
4. **OpenHands `ConfirmRisky`** (2024). The cleanest OSS implementation of AgentPause's "fixed risk threshold", "always confirm" and "full autonomy" baselines as pluggable policies. A natural host for AgentPause's adaptive policy plus a head-to-head benchmark.
5. **Gemini Computer Use `safety_decision`** and **Gemini in Chrome User Alignment Critic** (Google, 2025). Per-step continue / require_confirmation / block with an explanation shown to users; intent-alignment critic that escalates after repeated vetoes.
6. **OpenAI Operator / ChatGPT agent** (2025). Trained-in, severity-aware confirmation behaviour with category-level recall metrics, plus watch mode (an attention signal). Not configurable or explainable; precision and burden not measured.
7. **Cursor Auto-review**, **VS Code Assisted permissions**, **Claude in Chrome action screening** (2025 to 2026). LLM-judged per-call gating with user-written natural-language preferences (Cursor).
8. **Warp "Agent decides"**, **Cline `requires_approval`**, **goose Smart Approval**, **Devin Desktop "Auto"**. Agent self-assessed confidence or risk gating; Warp is the only one that states an explicit *uncertainty-based* ask rule.
9. **LlamaFirewall** (`ALLOW / HUMAN_IN_THE_LOOP_REQUIRED / BLOCK`) and **AgentSafe/Decionis** (`ALLOW / ESCALATE / BLOCK` + Decision Dossier). Share AgentPause's decision vocabulary and rationale logging, but are security-driven.
10. **Mastra** (classifier probability ≥ 0.7 example) and **Copilot Studio AI approval stages** (decision + rationale + threshold conditions). Concrete fixed-threshold and AI-rationale patterns.

Conceptual near-neighbours in the long tail: **ask-or-act/Kiri** (reversibility × confidence + benchmark), **TELEMACHUS** (calibrated escalation gate), **RishiM19/AEGIS** (competence/risk/novelty/uncertainty min-fusion). All are low-adoption, unreviewed 2026 repos.

### Key takeaways for positioning AgentPause
- **The plumbing is commoditized; the policy is not.** Every major framework (LangGraph, LangChain, OpenAI Agents SDK, Pydantic AI, Vercel, Mastra, ADK, MS Agent Framework, Bedrock, MCP elicitation) has pause/approve/resume and most accept a per-call predicate. None ships a principled *decision model* for that predicate. AgentPause should be framed as **the policy layer that plugs into these hooks**:
  - LangChain `when`
  - OpenAI `needs_approval`
  - Vercel `toolApproval`
  - Claude Code PreToolUse hook
  - OpenHands confirmation policy
  - MCP proxy
- **Industry gates are binary safety classifiers.** Coding and browser agents have moved to LLM classifiers (Claude Code, Codex, Cursor, VS Code, Chrome agents) that decide run vs. block, with humans as a fallback after blocks. AgentPause's novelty is treating human involvement as a **decision with costs and timing**: interruption cost, task progress, the value of asking now vs. later (DEFER), and clarifying intent (CLARIFY) instead of approving an action.
- **Evaluation gap.** Vendors report *recall* of confirmations (OpenAI 91 to 92%) or classifier FPR/FNR (Claude Code), and user studies find unnecessary approvals annoying (Magentic-UI participants on add-to-cart and redundant plan approval). No one offers an open harness that trades off missed critical confirmations against interruption burden across policies. **AgentPause's policy-comparison framework is a clear contribution**, and OpenHands, Magentic-UI and AutoGen provide ready baselines to plug in.
- **Explanations exist only as one-line "why" reasons.** Counterfactual timing explanations ("I didn't ask two steps ago because that step was reversible; I'm asking now because the next action sends an email") appear nowhere. This is an open niche.
- **History is used only as memoized "always allow" rules** (Codex prefix rules, VS Code scopes, MS Agent Framework standing approvals, Magentic-UI session auto-approve). Learning a calibrated preference model from past decisions, and using it to decide asking vs. continuing, is unclaimed.
- **Design cues worth adopting:**
  - Magentic-UI's ALTERNATIVE (third option) response.
  - Claude Code's "user-stated boundaries" signal.
  - OpenAI's watch-mode attention signal.
  - Roo Code's timeout fallback for clarifications.
  - Gemini's explanation-must-be-shown contract.
  - Mastra/Microsoft argument-binding so approvals cover exactly the reviewed action.
  - The hooks' `defer` semantics for headless or asynchronous resumption.

---

## Could not verify (excluded from the main catalogue or only partially verified)
- **Google Project Mariner:** confirmation and takeover behaviour was seen only in search snippets and secondary coverage. The Google Labs help page (https://support.google.com/labs/answer/16270604) returned only navigation chrome to the fetcher, and the DeepMind page had no Mariner content. Not catalogued. The verified Google equivalent is #37 (Gemini in Chrome).
- **OpenAI Operator / ChatGPT agent launch pages and help center:** openai.com and help.openai.com returned HTTP 403. The system-card PDFs on cdn.openai.com *were* downloaded and read, and all claims above come from them.
- **Salesforce Agentforce per-action "require confirmation" setting:** not verified (search budget exhausted). Only the Trailhead trust-patterns module (escalation via topic instructions) was verified.
- **Invariant Labs "Invariant Explorer"** and any acquisition of Invariant Labs: not verified. Only the Invariant Guardrails repo was checked.
- **HumanLayer's Slack/email channel details** are from the old README/docs context. The v0.7.0 README confirms `require_approval` and `human_as_tool`; the PyPI page did not render for the fetcher.
- **Exact first-release dates** for several features (n8n Human review, VS Code Assisted permissions, gotoHuman, Cline auto-approve, Copilot Studio RFI). Where a date wasn't stated in a primary source, I gave the repo creation year or an approximate range.
- **Third-party claims not used:** e.g., a Substack claim about Operator "92% of critical actions" (the system card actually reports 92% average confirmation recall on 607 tasks), and blog descriptions of Codex "guardian" key names (the official docs use `approvals_reviewer = "auto_review"`).
- **Long-tail GitHub repos (section 6 and #21):** existence and README content verified; their claims (results, metrics) are self-reported and unreviewed.

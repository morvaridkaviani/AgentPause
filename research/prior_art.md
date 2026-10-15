# Prior Art Review

**Review date:** 2026-10-14. **Scope:** 2023–2026 work first, plus foundational older work.
**Coverage:** about 250 papers, products, specifications and repositories across HCI (CHI, UIST,
IUI, CSCW, HRI, TOCHI), ML/NLP (NeurIPS, ICML, ICLR, ACL, EMNLP, CoRL), software engineering and
security venues, arXiv, GitHub, and vendor documentation.

## How this review was done

- **Five parallel search threads:**
  - (A) open-source frameworks and commercial systems;
  - (B) ML/NLP/robotics work on asking, deferring, and escalating;
  - (C) HCI work on interruption, automation, and agent oversight;
  - (D) explanations, plus questionnaire licensing;
  - (E) an adversarial "red-team" search for the closest competitors.
- **Verification rule:** an item is listed only if its page was actually fetched, whether that page was an arXiv/ACL/ACM DOI/proceedings page, a repository, vendor documentation or a system card.
- Where the *bibliographic metadata* was verified but the *content* summary comes from knowledge of the paper (for example, the ACM DL returned HTTP 403), the entry is marked **†**.
- Items seen only in search snippets are listed under [Not verified](#not-verified-excluded) and are not used as evidence.

**Known limitations of the review:**

- The shared web-search budget ran out near the end, so some threads stopped early.
- openai.com and help.openai.com returned HTTP 403, so OpenAI claims come from system-card PDFs only.
- Google Project Mariner could not be verified.
- The field changes monthly; see [novelty_audit.md](novelty_audit.md) for the re-check.

The working notes from each thread, with the full per-item verification remarks, are kept
in [`literature_notes/`](literature_notes/).

## Key findings

1. **The decision-theoretic core is not new.**
   - Horvitz (CHI 1999) chose between act, dialog and no-action by expected utility, with user-settable thresholds and deferral to less distracting moments.
   - Dong et al. (ACL 2026) apply net value-of-information minus user cost to LLM agents and compare against never-ask, fixed-rounds and confidence-threshold baselines.
2. **Timing within agent trajectories is now being studied, but no policy has been released.**
   - Zhou et al. (CHI 2026) place confirmation checkpoints by dynamic programming.
   - Gulati et al. (2026) measure how much a clarification is worth at each point in a trajectory.
   - Chen et al. (2026) find a timing mismatch in 56% of oversight failures.
   - None of these releases a policy that defers or batches questions under reversibility deadlines.
3. **Industry has standardized the *plumbing*, not the *policy*.** LangGraph, the OpenAI Agents SDK, Vercel, Pydantic AI, ADK, Mastra, MCP elicitation and Claude Code hooks all expose a pause/approve hook. Their deciders are of three kinds:
   - developer rules;
   - per-tool flags;
   - binary safety classifiers (Claude Code auto mode, Codex auto-review, Cursor, VS Code, Chrome agents).
4. **Explanations are one-line reasons.** No reviewed system explains the *timing* of an intervention.
5. **Evaluation is fragmented.** Vendors report confirmation recall or classifier error rates. Small repositories (hitloop, Headroom) compare a few policies. A Stanford SPAR benchmark of when to apply oversight is in progress.

---

## Part 1: Closest work (detailed)

The fields follow the project brief:

1. Name
2. Year
3. Authors/company
4. URL
5. What it does
6. Overlap with AgentPause
7. What AgentPause does differently
8. Direct competitor?
9. Type

### 1.1 Value of Information: A Framework for Human–Agent Communication
1. **Name:** Value of Information: A Framework for Human–Agent Communication
2. **Year:** 2026 (ACL 2026, long paper)
3. **Authors:** Y. R. Dong, T. Hu, Z. Hui, C. Zhang, I. Vulić, N. Collier (Cambridge); A. Bobu (MIT)
4. **URL:** https://arxiv.org/abs/2601.06407 · https://aclanthology.org/2026.acl-long.1987/ · code announced at https://github.com/dong-river/VOI_communication
5. **What it does:** Computes NetVoI(q) = VoI(q) − c for candidate questions. It asks the best question while the net value is positive, and otherwise commits. Stakes enter through the terminal utility, and c is a per-turn user-effort cost. It is myopic (one step ahead). Domains are 20 Questions (animal or medical), flight recommendation and ambiguous WebShop. Baselines: no question, fixed rounds, adaptive prompting and confidence threshold.
6. **Overlap:** This is exactly the "expected benefit of asking minus cost of interrupting" rule, applied to LLM agents and compared against AgentPause's fixed baselines.
7. **AgentPause differs:** It gates *side-effecting actions in an executing multi-step trajectory*, not pre-commit question loops. It adds:
   - reversibility and recoverability in the error cost;
   - interruption cost that depends on breakpoints, load and habituation;
   - DEFER and batching;
   - BLOCK;
   - explanations.

   AgentPause's `myopic_voi` baseline is a simplified per-step analogue. It is *not* a reimplementation of Dong et al.'s belief-state method.
8. **Direct competitor:** Partial, close to yes on the decision rule. It is a must-cite.
9. **Type:** Both

### 1.2 When Should Users Check? Modeling Confirmation Frequency in Multi-Step Agentic AI Tasks
1. **Name:** When Should Users Check? Modeling Confirmation Frequency in Multi-Step Agentic AI Tasks
2. **Year:** 2026 (CHI '26; arXiv 2025)
3. **Authors:** J. Zhou, A. Roy, S. Gupta, D. Weitekamp, C. J. MacLellan (Georgia Tech)
4. **URL:** https://doi.org/10.1145/3772318.3790655 · https://arxiv.org/abs/2510.05307
5. **What it does:** Treats checkpoint placement in an N-step agent plan as minimum-time scheduling. It models per-step success probability and confirmation, diagnosis and redo costs, and solves the placement by dynamic programming, re-planning after errors. A within-subjects study (n = 48; shopping, image editing, Overcooked; simulated agents) found 13.5% less time than confirm-at-end, and 81% of participants preferred it.
6. **Overlap:** It is the closest academic precedent for deciding *when* in a trajectory to involve the user.
7. **AgentPause differs:** Zhou et al. optimize time only. They explicitly exclude money, safety, irreversibility, ambiguity and personalization (left as future work), and they release no code. AgentPause adds:
   - severity and reversibility deadlines;
   - intent assumptions;
   - CLARIFY, DEFER and BLOCK;
   - load- and habituation-dependent cost;
   - always-ask and never-ask baselines;
   - explanations;
   - an open simulator.
8. **Direct competitor:** Yes, for intervention placement.
9. **Type:** Academic

### 1.3 Modeling Distinct Human Interaction in Web Agents (CowCorpus / PlowPilot)
1. **Name:** Modeling Distinct Human Interaction in Web Agents
2. **Year:** 2026 (arXiv, v4 Jul 2026)
3. **Authors:** F. Huq, Z. Z. Wang, Z. Guo, V. A. Arangarajan, T. Ou, F. Xu, S. Zhou, G. Neubig, J. P. Bigham (CMU; Duke)
4. **URL:** https://arxiv.org/abs/2602.17588 · https://github.com/oaishi/PlowPilot
5. **What it does:** CowCorpus contains 400 real-user web trajectories and identifies four interaction styles. A fine-tuned model predicts `<ask_user>` vs `<agent_continue>` for each proposed action from the screenshot, the accessibility tree and the history of human actions. It is deployed in PlowPilot, a Chrome extension, which asks only when an intervention is likely. The usefulness study is preliminary (n = 4 returning users).
6. **Overlap:** A per-step learned gate conditioned on user history, deployed live.
7. **AgentPause differs:** PlowPilot is *descriptive*: it predicts where users *would* intervene. AgentPause is *normative*: it estimates where intervening is *worth it* from severity and reversibility. This matters because users miss risky steps (Chen et al. 2026). AgentPause also has DEFER/CLARIFY/BLOCK, explanations, interpretable terms and a policy-comparison testbed.
8. **Direct competitor:** Yes
9. **Type:** Both

### 1.4 Comparing Human Oversight Strategies for Computer-Use Agents
1. **Name:** Comparing Human Oversight Strategies for Computer-Use Agents
2. **Year:** 2026 (arXiv, v2 Sep 2026)
3. **Authors:** C. Chen, Z. Zhang, Z. Chen, E. Xu, Y. Yang, I. Khalilov, S. A. Gebreegziabher, Y. Ye, Z. Xiao, Y. Yao, T. Li, T. J.-J. Li
4. **URL:** https://arxiv.org/abs/2604.04918
5. **What it does:** 48 participants ran 192 live sessions, each with an embedded problematic action. Four strategies were compared: per-action confirmation, risk-gated, plan plus step approval, and a structurally enriched variant.
   - Users blocked only 21% of problematic actions that reached execution.
   - 56% of failures showed a *timing mismatch* between when risk emerged and when the UI asked.
   - Users checked procedure rather than appropriateness.
   - The authors call for adaptive oversight and for asking judgement *before* consequential state changes.
6. **Overlap:** It occupies the same evaluation space and has the same thesis.
7. **AgentPause differs:** It supplies the adaptive policy this paper calls for, and it adopts the paper's protocol (embedded problematic actions, block rate, timing mismatch) for its study mode.
8. **Direct competitor:** Partial (empirical study, not a system)
9. **Type:** Academic

### 1.5 Ask Early, Ask Late, Ask Right: When Does Clarification Timing Matter for Long-Horizon Agents?
1. **Name:** Ask Early, Ask Late, Ask Right: When Does Clarification Timing Matter for Long-Horizon Agents?
2. **Year:** 2026 (arXiv, May 2026)
3. **Authors:** A. Gulati, H. Gupta, E. Lumer, S. Sen, V. K. Subbiah (PwC US)
4. **URL:** https://arxiv.org/abs/2605.07937
5. **What it does:** Forced injection of ground-truth clarifications at controlled points in more than 6,000 runs.
   - Goal clarifications lose almost all value after about 10% of execution.
   - Input clarifications stay useful to about 50%.
   - Asking after mid-trajectory is worse than never asking.
   - No frontier model asks within the optimal window.
   - No policy is proposed; the authors call for timing-aware policies.
6. **Overlap:** Direct empirical evidence that timing matters, by information type.
7. **AgentPause differs:** It provides a policy. Its DEFER mechanism is **bounded by information type**, informed by this paper: goal and constraint assumptions are not deferred by default.
8. **Direct competitor:** Partial (evidence, no system)
9. **Type:** Academic

### 1.6 Magentic-UI (action guards)
1. **Name:** Magentic-UI: Towards Human-in-the-loop Agentic Systems
2. **Year:** 2025
3. **Authors:** H. Mozannar, G. Bansal, C. Tan, A. Fourney, … E. Kamar, S. Amershi (Microsoft Research)
4. **URL:** https://arxiv.org/abs/2507.22358 · https://github.com/microsoft/magentic-ui (MIT)
5. **What it does:** An open-source web/code/file agent with co-planning, co-tasking and action guards.
   - Each action type carries an irreversibility label (always / maybe / never).
   - An LLM judge decides "maybe" cases.
   - Policies are always, never, auto-conservative and auto-permissive.
   - Users can answer APPROVE / DENY / ALTERNATIVE.
   - In the user study, participants found some approvals excessive (add to cart, plan change) and asked for bundled questions and a third option.
6. **Overlap:** Reversibility-based gating, multiple approval policies, simulated users. It is the closest open research platform.
7. **AgentPause differs:**
   - Its decision is multi-signal and continuous rather than a binary YES/NO judge.
   - It has timing (DEFER and batching, which Magentic-UI's own participants requested).
   - It gives explanations.
   - It compares policies systematically.

   AgentPause's `rule_based` baseline is inspired by this reversibility-labelled design.
8. **Direct competitor:** Partial, and among the closest.
9. **Type:** Both

### 1.7 Claude Code auto mode and hooks
1. **Name:** Claude Code permission modes, auto mode classifier, and PreToolUse hooks
2. **Year:** 2025–2026 (auto mode: March 2026)
3. **Authors:** Anthropic
4. **URL:** https://www.anthropic.com/engineering/claude-code-auto-mode · https://code.claude.com/docs/en/hooks · https://www.anthropic.com/research/measuring-agent-autonomy
5. **What it does:**
   - **Motivation:** users approve 93% of permission prompts.
   - **Tiers:**
     - an allowlist;
     - in-project edits;
     - a two-stage transcript classifier judging user-intent authorization, trust boundary and irreversibility signals (it runs `git status` before destructive commands).
   - **Fallback:** the human is involved after 3 consecutive or 20 total blocks.
   - **Reported error rates:** 0.4% false positives and 17% false negatives on real overeager actions.
   - **Hooks:** return `allow` / `deny` / `ask` / `defer` with a user-visible reason.
6. **Overlap:** A production per-action middleware whose hook vocabulary nearly matches AgentPause's outputs.
7. **AgentPause differs:**
   - The classifier decides *whether to allow*. It does not decide *when to involve the human*.
   - Its signals do not include agent uncertainty, task progress or interruption cost.
   - Its explanations are rule labels shown to the agent.
   - It is closed source and was evaluated internally.

   AgentPause can run *as* a PreToolUse hook (see `examples/`).
8. **Direct competitor:** Partial (the closest commercial analogue)
9. **Type:** Commercial product

### 1.8 OpenAI Codex auto-review and smart approvals
1. **Name:** Codex approval policies, auto-review, and smart approvals
2. **Year:** 2025–2026
3. **Authors:** OpenAI
4. **URL:** https://learn.chatgpt.com/codex/agent-approvals-security · https://github.com/openai/codex
5. **What it does:**
   - A reviewer agent assigns a risk level (low/medium proceed; high needs user authorization; critical is denied) and a user-authorization assessment, both shown in the UI.
   - "Smart approvals" propose `prefix_rule`s from the user's past approvals.
6. **Overlap:** A risk-tiered automatic reviewer, plus rules derived from history.
7. **AgentPause differs:**
   - Codex only reviews actions that try to leave the sandbox.
   - It has no uncertainty, progress or interruption-cost signals and no CLARIFY/DEFER.
   - Its history is literal memoization of command prefixes, with no preference model.
8. **Direct competitor:** Partial
9. **Type:** Software (Apache-2.0 CLI) + commercial product

### 1.9 OpenHands confirmation policies
1. **Name:** OpenHands confirmation mode and security analyzer
2. **Year:** 2024
3. **Authors:** All Hands AI / OpenHands community
4. **URL:** https://docs.openhands.dev/sdk/guides/security
5. **What it does:** A security analyzer labels each action LOW / MEDIUM / HIGH / UNKNOWN; by default the agent self-reports this. The confirmation policy is pluggable: `AlwaysConfirm`, `NeverConfirm` or `ConfirmRisky(threshold)`.
6. **Overlap:** These are literally three of AgentPause's baselines, as swappable policy objects.
7. **AgentPause differs:**
   - It decides from multiple signals rather than one ordinal label.
   - It has CLARIFY, DEFER and BLOCK, and explanations.
   - It includes a harness for comparing the policies.

   AgentPause's `always_confirm`, `full_autonomy` and `fixed_threshold` baselines follow this design.
8. **Direct competitor:** Partial
9. **Type:** Software artifact (MIT)

### 1.10 Principles of Mixed-Initiative User Interfaces (LookOut)
1. **Name:** Principles of Mixed-Initiative User Interfaces
2. **Year:** 1999 (CHI '99)
3. **Authors:** E. Horvitz (Microsoft Research)
4. **URL:** https://doi.org/10.1145/302979.303030 · https://www.erichorvitz.com/chi99horvitz.pdf
5. **What it does:** Sets out 12 principles, including:
   - considering uncertainty about goals;
   - "the costs and benefits of deferring action to a time when action will be less distracting";
   - expected value of action;
   - dialog to resolve uncertainty while weighing the cost of bothering the user;
   - minimizing the cost of poor guesses about action and timing.

   LookOut derives thresholds p\*(no-action → dialog) and p\*(dialog → action) from utilities that users can set, and learns a per-user timing model.
6. **Overlap:** The conceptual ancestor of AgentPause's expected-value core, its CONTINUE/CLARIFY/ASK space, DEFER, and its user-customized thresholds.
7. **AgentPause differs:** It targets multi-step LLM agents with consequential tool actions. It adds reversibility deadlines, batching, habituation, counterfactual timing explanations and a reproducible testbed.
8. **Direct competitor:** No. It is the conceptual ancestor and must be cited.
9. **Type:** Academic (research prototype)

### 1.11 Attention-sensitive alerting and the cost of interruption (Horvitz et al.)
1. **Name:** Models of Attention in Computing and Communication (CACM); Learning and Reasoning about Interruption (ICMI); BusyBody (CSCW)
2. **Year:** 2003, 2003, 2004
3. **Authors:** E. Horvitz, C. Kadie, T. Paek, D. Hovel; E. Horvitz, J. Apacible; E. Horvitz, P. Koch, J. Apacible (Microsoft Research)
4. **URL:** https://doi.org/10.1145/636772.636798 · https://doi.org/10.1145/958432.958440 · https://doi.org/10.1145/1031607.1031690
5. **What it does:** † Alerts are delivered by comparing the expected cost of interrupting now with the expected cost of delayed review, which makes deferral a decision in its own right. Per-user interruptibility models are learned from desktop activity, calendar and sensors.
6. **Overlap:** AgentPause's interruption-cost and DEFER signals restate this trade-off.
7. **AgentPause differs:** It gates *agent actions*, where continuing can cause irreversible harm. It does not deliver messages.
8. **Direct competitor:** No (foundational)
9. **Type:** Academic (plus fielded prototypes)

### 1.12 Breakpoint research and OASIS (Bailey, Iqbal, Adamczyk)
1. **Name:**
   - *If not now, when?* (Adamczyk & Bailey);
   - workload and task structure as predictors of interruption cost (Iqbal & Bailey);
   - OASIS (Iqbal & Bailey).
2. **Year:** 2004; 2005/2006; 2008/2010
3. **Authors:** P. D. Adamczyk, B. P. Bailey, S. T. Iqbal (UIUC)
4. **URL:** https://doi.org/10.1145/985692.985727 · https://doi.org/10.1145/1056808.1056948 · https://doi.org/10.1145/1124772.1124882 · https://doi.org/10.1145/1879831.1879833
5. **What it does:**
   - Interrupting at task breakpoints, especially coarse ones, reduces resumption lag, annoyance and frustration.
   - OASIS detects breakpoints and holds notifications until one occurs.
6. **Overlap:** The empirical basis for AgentPause's breakpoint signal and for DEFER.
7. **AgentPause differs:**
   - It applies breakpoints to an *agent's* plan structure.
   - Deferral must end before the next irreversible dependent action.
8. **Direct competitor:** No (conceptual ancestor of DEFER)
9. **Type:** Both

### 1.13 Towards Adjustable Autonomy for the Real World
1. **Name:** Towards Adjustable Autonomy for the Real World
2. **Year:** 2002 (JAIR 17)
3. **Authors:** P. Scerri, D. V. Pynadath, M. Tambe (USC/ISI)
4. **URL:** https://jair.org/index.php/jair/article/view/10312 · https://arxiv.org/abs/1106.4573
5. **What it does:** Proposes transfer-of-control *strategies*, chosen by an MDP: whom to ask, how long to wait, and when to delay a team commitment to buy time. Deployed in Electric Elves.
6. **Overlap:** Treats the timing of transfers of control as an explicit decision, including deadlines.
7. **AgentPause differs:** It addresses a single user with an LLM agent making side-effecting tool calls, with rich per-action signals, explanations and an open testbed.
8. **Direct competitor:** Partial (foundational for timing)
9. **Type:** Academic

### 1.14 Ask4Help: Learning to Leverage an Expert for Embodied Tasks
1. **Name:** Ask4Help: Learning to Leverage an Expert for Embodied Tasks
2. **Year:** 2022 (NeurIPS)
3. **Authors:** K. P. Singh, L. Weihs, A. Herrasti, J. Choi, A. Kembhavi, R. Mottaghi (AI2)
4. **URL:** https://arxiv.org/abs/2211.09960 · https://github.com/allenai/ask4help
5. **What it does:** A separate learned policy decides when to ask an expert on top of a frozen agent. It is conditioned on an embedding of the **user's preferred costs** of asking and failing, so its asking rate can be adjusted at inference time.
6. **Overlap:** Middleware-style asking with user-customized cost.
7. **AgentPause differs:** It uses interpretable signals (reversibility, severity, load) rather than an opaque policy. It adds DEFER, BLOCK and explanations, and targets LLM tool agents.
8. **Direct competitor:** Partial
9. **Type:** Both

### 1.15 Self-Regulation and Requesting Interventions; ReHAC
1. **Name:** Self-Regulation and Requesting Interventions (Min et al.); Large Language Model-based Human-Agent Collaboration for Complex Task Solving (ReHAC; Feng et al.)
2. **Year:** 2025; 2024
3. **Authors:** S. Y. Min, Y. Wu, J. Sun, M. Kaufmann, F. Tajwar, Y. Bisk, R. Salakhutdinov (CMU); X. Feng, Z.-Y. Chen, Y. Qin, Y. Lin, X. Chen, Z. Liu, J.-R. Wen
4. **URL:** https://arxiv.org/abs/2502.04576 · https://arxiv.org/abs/2402.12914 · https://github.com/XueyangFeng/ReHAC
5. **What it does:**
   - Min et al. intervene iff the per-intervention cost r < Δsuccess/Δusage, with r tuned to a budget. Their interveners are stronger models, not humans. They report that naive thresholds "toggle".
   - ReHAC learns a per-step human-or-agent policy with reward = task score − λ·#interventions.
6. **Overlap:** Learned, budgeted intervention timing within trajectories.
7. **AgentPause differs:** The human is the intervener. The cost depends on load and preferences. It adds reversibility, explanations, and DEFER to breakpoints.
8. **Direct competitor:** Partial
9. **Type:** Academic (ReHAC: both)

### 1.16 SAGE-Agent / ClarifyBench
1. **Name:** Structured Uncertainty guided Clarification for LLM Agents
2. **Year:** 2025 (arXiv); ACL Findings 2026
3. **Authors:** M. Suri, P. Mathur, N. Lipka, F. Dernoncourt, R. A. Rossi, D. Manocha (UMD; Adobe)
4. **URL:** https://arxiv.org/abs/2511.08798
5. **What it does:** Scores questions about tool parameters by EVPI minus a cost that penalizes repeated questions, and separates specification uncertainty from model uncertainty.
6. **Overlap:** The CLARIFY branch, and the split between intent ambiguity and agent uncertainty.
7. **AgentPause differs:** It covers action approval as well as parameter questions. It adds severity, reversibility, timing and DEFER.
8. **Direct competitor:** Partial
9. **Type:** Academic

### 1.17 KnowNo and Introspective Planning
1. **Name:** Robots That Ask For Help (KnowNo); Introspective Planning
2. **Year:** 2023 (CoRL); 2024 (NeurIPS)
3. **Authors:** A. Z. Ren, A. Dixit, … D. Sadigh, A. Zeng, A. Majumdar; K. Liang, Z. Zhang, J. F. Fisac
4. **URL:** https://arxiv.org/abs/2307.01928 · https://arxiv.org/abs/2402.06529
5. **What it does:** Builds conformal prediction sets over LLM plan options and asks when the set holds more than one option, which gives a statistical success guarantee with minimal help.
6. **Overlap:** A principled uncertainty-triggered ask.
7. **AgentPause differs:** Uncertainty is one signal among many. AgentPause's `confidence_threshold` baseline is a *non-conformal* simplification in the same spirit.
8. **Direct competitor:** Partial
9. **Type:** Both

### 1.18 Oversight Has a Capacity (Headroom)
1. **Name:** Oversight Has a Capacity: Calibrating Agent Guards to a Subjective, Fatiguing Human
2. **Year:** 2026
3. **Authors:** E. Turan
4. **URL:** https://arxiv.org/abs/2606.08919 · https://github.com/turangenesis/headroom
5. **What it does:** An LLM risk score from 0 to 100 drives a user-tunable escalation threshold. It models reviewer fatigue and finds realized safety is an inverted U in escalation rate. It reports missed-danger vs false-alarm curves and inter-rater κ = 0.52 on "risky".
6. **Overlap:** Fatigue-aware escalation and missed/false-alarm metrics.
7. **AgentPause differs:** It adds timing, DEFER, CLARIFY, reversibility deadlines and explanations, and models fatigue as lowering the human's *catch probability* inside the expected value.
8. **Direct competitor:** Partial
9. **Type:** Both

### 1.19 hitloop
1. **Name:** hitloop
2. **Year:** 2025/26
3. **Authors:** GitHub user `ebaenamar`
4. **URL:** https://github.com/ebaenamar/hitloop
5. **What it does:**
   - **Policies:** AlwaysApprove, RiskBased, Audit+Escalate and Telemetry (LangGraph).
   - **Experiment tooling:** an `ExperimentRunner` with "4 policies × scenarios" and an `ErrorInjector`.
   - **Metrics:** error_catch_rate and false_reject_rate.
   - **Scenarios:** an email scenario.
6. **Overlap:** The closest existing match for AgentPause's evaluation framework, at toy scale.
7. **AgentPause differs:**
   - It has an adaptive timing policy and CLARIFY/DEFER.
   - It provides explanations.
   - It has six scenarios with scripted assumptions and commitment points.
   - It includes a habituating simulated user and a user-study mode.
8. **Direct competitor:** Partial
9. **Type:** Software

### 1.20 SPAR "Benchmarking When to Apply Oversight for Agentic AI" + The Oversight Game
1. **Name:** SPAR Fall 2026 project; The Oversight Game: Learning to Cooperatively Balance an AI Agent's Safety and Autonomy
2. **Year:** 2026 (project in progress); ICML 2026 (paper)
3. **Authors:** W. Overman (mentor), M. Bayati (Stanford)
4. **URL:** https://www.sparai.org/projects/f26/recjmG0Nfo4Ijp61q · https://arxiv.org/abs/2510.26752
5. **What it does:** Plans an open benchmark of when to act versus defer. It would label every decision point counterfactually (act-would-violate vs deferral-unnecessary) and include always-ask, never-ask, threshold, LLM-monitor and learned baselines.
6. **Overlap:** Nearly identical evaluation goals.
7. **AgentPause differs:** Its focus is UX timing (DEFER/batching), clarification versus approval, explanations, user preferences and a study mode. It is released now; the SPAR benchmark is not.
8. **Direct competitor:** Yes for the evaluation framework, once released.
9. **Type:** Academic (benchmark in progress)

### 1.21 Do User-Authored Permission Policies Improve Protection Against AI Agent Overreach?
1. **Name:** Do User-Authored Permission Policies Improve Protection Against AI Agent Overreach?
2. **Year:** 2026
3. **Authors:** T. Yan
4. **URL:** https://arxiv.org/abs/2608.27443
5. **What it does:** With N = 113 users, compares per-action human approval, automated per-action review, and user-written allow/ask/never rules. User policies cut prompts (18.0 → 10.9) but blocked less overreach (−20.1 pp). Of 140 rules, 114 were "ask", which the author calls a preference–commitment gap.
6. **Overlap:** Mirrors AgentPause's user-customized condition and study mode.
7. **AgentPause differs:** It adds an adaptive policy, timing and explanations. AgentPause treats this paper's negative result as a hypothesis to replicate (H6).
8. **Direct competitor:** Partial
9. **Type:** Academic

### 1.22 Conleash: Options, Not Clicks
1. **Name:** Options, Not Clicks: Lattice Refinement for Consent-Driven MCP Authorization
2. **Year:** 2026
3. **Authors:** Y. Li, Y. Chen, P. Wang, I. Khabra, F. H. Shezan, Y. Feng, Y. Tian
4. **URL:** https://arxiv.org/abs/2605.11360
5. **What it does:** Client-side MCP middleware. A risk lattice auto-permits calls within known-safe boundaries and escalates risky ones, and user decisions are refined into reusable scoped rules. In pre-screening, 13 of 16 participants used "Always Allow" just to dismiss prompts.
6. **Overlap:** The same middleware architecture, learning from user decisions.
7. **AgentPause differs:** It adds interruption timing, cognitive load, CLARIFY and agent uncertainty, and evaluates agency. Conleash is framed as a security/authorization system.
8. **Direct competitor:** Yes (architecture level)
9. **Type:** Both

### 1.23 InferAct
1. **Name:** Preemptive Detection and Correction of Misaligned Actions in LLM Agents
2. **Year:** 2024 (arXiv); EMNLP 2025
3. **Authors:** H. Fang, X. Zhu, I. Gurevych
4. **URL:** https://arxiv.org/abs/2407.11843 · https://github.com/UKPLab/emnlp2025-inferact
5. **What it does:** Before expert-listed critical (irreversible) actions, it infers the agent's apparent intent and alerts a human if the intent looks misaligned. Human review is capped by a budget.
6. **Overlap:** Pre-commit checks of irreversible actions with an intent signal.
7. **AgentPause differs:** It discovers commitment points from metadata rather than expert lists, and adds interruption cost, timing, preferences and explanations.
8. **Direct competitor:** Partial
9. **Type:** Both

### 1.24 AgentSpec and ProbGuard
1. **Name:** AgentSpec: Customizable Runtime Enforcement; ProbGuard: Proactive Runtime Monitoring via Probabilistic Prediction
2. **Year:** 2025 (arXiv); ICSE 2026 / ASE 2026
3. **Authors:** H. Wang, C. M. Poskitt, (J. Wei), J. Sun (Singapore Management University)
4. **URL:** https://arxiv.org/abs/2503.18666 · https://arxiv.org/abs/2508.00500
5. **What it does:**
   - AgentSpec is a rule DSL whose enforcements include `user_inspection` (pause for confirmation) and `stop`.
   - ProbGuard forecasts the probability of a safety violation and intervenes early.
6. **Overlap:** Middleware with ASK and BLOCK outcomes; ProbGuard adds forecast-driven timing.
7. **AgentPause differs:** Its decisions weigh the human's cost against expected harm rather than following rules or forecasts alone. It adds CLARIFY/DEFER, user adaptation and explanations.
8. **Direct competitor:** Partial
9. **Type:** Both / Academic

### 1.25 Gemini Computer Use `safety_decision`
1. **Name:** Gemini Computer Use safety decisions
2. **Year:** 2025
3. **Authors:** Google
4. **URL:** https://ai.google.dev/gemini-api/docs/computer-use
5. **What it does:** Labels each proposed action allowed / `require_confirmation` / blocked, with an explanation that developers must show to the user.
6. **Overlap:** The closest commercial *output contract*: continue / ask / block plus an explanation.
7. **AgentPause differs:** Its explanations cover timing and counterfactuals, it is inspectable and user-tunable, and it has CLARIFY and DEFER.
8. **Direct competitor:** Partial
9. **Type:** Commercial API

### 1.26 Sequential Learning-to-Defer (SLTD)
1. **Name:** Learning-to-defer for sequential medical decision-making under uncertainty
2. **Year:** 2021
3. **Authors:** S. Joshi, S. Parbhoo, F. Doshi-Velez (Harvard)
4. **URL:** https://arxiv.org/abs/2109.06312
5. **What it does:** Estimates whether deferring to an expert *now* beats waiting another step, using model-based RL over long-term outcomes.
6. **Overlap:** A formal precedent for "ask now vs later".
7. **AgentPause differs:** It works in the LLM-agent action space, with interruption cost, batching, preferences and user-facing explanations.
8. **Direct competitor:** No (formal ancestor of DEFER)
9. **Type:** Academic

### 1.27 Autonomy Reshapes How Personalization Affects Privacy Concerns and Trust in LLM Agents
1. **Name:** Autonomy Reshapes How Personalization Affects Privacy Concerns and Trust in LLM Agents
2. **Year:** 2026 (COLM 2026)
3. **Authors:** Z. Zhang, Y. E. Zhang, F. Shi, T. Li
4. **URL:** https://arxiv.org/abs/2510.04465
5. **What it does:** A 3×3 experiment with N = 450. Risk-contingent autonomy, where the agent hands control back when it detects possible privacy leakage, raised perceived control.
6. **Overlap:** Direct evidence for the "agency" half of AgentPause's hypothesis, for a single signal.
7. **AgentPause differs:** It uses multiple signals plus timing, and measures objective oversight effectiveness as well as perceived control.
8. **Direct competitor:** Partial
9. **Type:** Academic

### 1.28 Levels of Autonomy for AI Agents
1. **Name:** Levels of Autonomy for AI Agents
2. **Year:** 2025
3. **Authors:** K. J. K. Feng, D. W. McDonald, A. X. Zhang (University of Washington)
4. **URL:** https://arxiv.org/abs/2506.12469
5. **What it does:** Defines five levels by the user's role: operator, collaborator, consultant, approver, observer. It warns of "meaningless rubber stamping" at the approver level. Autonomy is fixed per deployment.
6. **Overlap:** The same design space.
7. **AgentPause differs:** It moves between the approver and observer levels *per action*, at run time.
8. **Direct competitor:** No (conceptual framework)
9. **Type:** Academic

### 1.29 ask-or-act / Kiri
1. **Name:** ask-or-act benchmark and Kiri gate
2. **Year:** 2026
3. **Authors:** GitHub user `aryan597`
4. **URL:** https://github.com/aryan597/ask-or-act · https://github.com/aryan597/kiri-gate
5. **What it does:** A 120-action benchmark of whether models know when to ask, plus a rule:
   - read → act;
   - undoable → act if confident, otherwise ask;
   - irreversible or external → always ask.
6. **Overlap:** A two-signal (reversibility × confidence) policy plus a benchmark.
7. **AgentPause differs:** It has a broader set of signals and outcomes, timing and explanations. Its `rule_based` baseline follows a similar reversibility × confidence structure.
8. **Direct competitor:** Partial (small, unreviewed)
9. **Type:** Software

---

## Part 2: Extended catalogue

Columns follow the nine required fields. "Comp." means direct competitor: **Y** (yes), **P** (partial) or **N** (no). Type is **A** (academic), **S** (software), **B** (both) or **C** (commercial). **†** means the metadata was verified and the content was summarized from knowledge of the work.

### 2.1 Agent frameworks and human-in-the-loop plumbing

| Name | Year | Authors/Org | URL | What it does | Overlap | AgentPause differs | Comp. | Type |
|---|---|---|---|---|---|---|---|---|
| LangGraph `interrupt()` | 2024 | LangChain | https://docs.langchain.com/oss/python/langgraph/interrupts | Durable pause/resume with a checkpointed state | Pause substrate | Decides *whether/when* to call `interrupt()` | N | S |
| LangChain `HumanInTheLoopMiddleware` | 2025 | LangChain | https://docs.langchain.com/oss/python/langchain/human-in-the-loop | Per-tool `interrupt_on`, a `when` predicate, batched interrupts | Same interception slot | Supplies the policy behind `when` | P | S |
| OpenAI Agents SDK `needs_approval` | 2025–26 | OpenAI | https://openai.github.io/openai-agents-python/human_in_the_loop/ | Per-call boolean or callable approval; sticky approve/reject | Dynamic hook | Ready-made decision model, CLARIFY/DEFER | P | S |
| OpenAI Agent Builder approval node | 2025 | OpenAI | https://developers.openai.com/api/docs/guides/node-reference | Static approval node in a visual workflow | Approval step | Placed at run time | N | C |
| AutoGen `human_input_mode` | 2023 | Microsoft | https://microsoft.github.io/autogen/0.2/docs/tutorial/human-in-the-loop/ | NEVER / TERMINATE / ALWAYS | Canonical fixed baselines | Per-action, signal-driven | N | S |
| Microsoft Agent Framework tool approval + SK filters | 2025–26 | Microsoft | https://learn.microsoft.com/en-us/agent-framework/agents/tools/tool-approval | Approval middleware, standing "always approve" rules, `auto_approval_rules` | History as memoized approvals | Weighted history and expected-value decisions | P | S |
| Copilot Studio multistage/AI approvals | 2025 | Microsoft | https://learn.microsoft.com/en-us/microsoft-copilot-studio/flows-advanced-approvals | AI approval stages with rationale + threshold conditions | AI decides when a human is needed | Step-level agent timing, counterfactuals | P | C |
| CrewAI human input | 2023+ | CrewAI | https://docs.crewai.com/en/learn/human-in-the-loop | Post-task human review | Review checkpoint | Pre-execution, adaptive | N | S/C |
| Pydantic AI deferred tools | 2025 | Pydantic | https://pydantic.dev/docs/ai/tools-toolsets/deferred-tools/ | `requires_approval`, `ApprovalRequired` | Conditional approval; "deferred" = awaiting external result | DEFER as a *timing* decision | N | S |
| Vercel AI SDK tool approval | 2025 | Vercel | https://ai-sdk.dev/docs/ai-sdk-core/tools-and-tool-calling | `needsApproval`/`toolApproval` with `reason` | Tri-state interface | Supplies the decision + explanation | N | S |
| Mastra tool approval | 2026 | Mastra | https://mastra.ai/docs/agents/agent-approval | Function-based approval; documented classifier ≥ 0.7 example | Fixed-threshold pattern | Multi-signal adaptive | P | S |
| LlamaIndex Workflows HITL | 2024 | LlamaIndex | https://developers.llamaindex.ai/python/llamaagents/workflows/human_in_the_loop/ | `InputRequiredEvent` / `HumanResponseEvent` | Pause primitive | Policy | N | S |
| Google ADK tool confirmation | 2025 | Google | https://adk.dev/tools-custom/confirmation/ | `require_confirmation` (bool or function), structured confirmation | Conditional hook | Signal fusion, timing | N | S |
| n8n Human review for AI tools | 2025–26 | n8n | https://docs.n8n.io/advanced-ai/human-in-the-loop-tools/ | Static per-tool approval over chat channels | Gating | Dynamic | N | S/C |
| HumanLayer | 2024 | HumanLayer | https://github.com/humanlayer/humanlayer | `require_approval`, `human_as_tool` (now deprecated) | Approval layer | Per-call decision | N | S/C |
| gotoHuman | 2024–25 | gotoHuman | https://www.gotohuman.com/ | Hosted review inbox | Human-side channel | Decision layer | N | C |
| Permit.io Access Request MCP | 2025 | Permit.io | https://docs.permit.io/ai-security/access-request-mcp/overview | Authorization-policy-triggered approvals | Escalation | Context/timing, not authorization | N | S/C |
| Auth0 Async Authorization (CIBA) | 2025 | Auth0/Okta | https://auth0.com/blog/auth0-for-ai-agents-generally-available/ | Out-of-band consent with a binding message | Asynchronous ASK | Decides when CIBA is worth it | N | C |
| MCP elicitation | 2025 | MCP project | https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation | Form/URL elicitation with accept/decline/cancel | Wire protocol for CLARIFY/ASK | Decides *when* to elicit | N | Spec |
| Phantasm / Cordum / AEGIS / AgentSafe | 2024–26 | various | https://github.com/edwinkys/phantasm · https://github.com/cordum-io/cordum · https://github.com/Justin0504/Aegis · https://github.com/decionis/agent-safe-pipeline | Approval gateways / action firewalls (ALLOW/ESCALATE/BLOCK) | Same position and vocabulary | Uncertainty, timing, interruption cost | P | S |

### 2.2 Coding, browser and computer-use agent products

| Name | Year | Authors/Org | URL | What it does | Overlap | AgentPause differs | Comp. | Type |
|---|---|---|---|---|---|---|---|---|
| Cline auto-approve | 2024+ | Cline | https://docs.cline.bot/features/auto-approve | Per-category toggles; model-set `requires_approval` | User-customized + self-assessed risk | Independent multi-signal decider | P | S |
| Roo Code auto-approve | 2024+ | Roo Code | https://roocodeinc.github.io/Roo-Code/features/auto-approving-actions | Category risk labels; follow-up auto-answer timeout (60 s) | Customization; timeout fallback | Per-instance decisions | P | S |
| Cursor run modes + Auto-review | 2026 | Anysphere | https://cursor.com/docs/agent/security/run-modes | Classifier with natural-language allow/block instructions | Model-based gate + user preferences | Timing, CLARIFY/DEFER | P | C |
| VS Code Assisted permissions | 2025–26 | Microsoft/GitHub | https://code.visualstudio.com/docs/agents/approvals | LLM judge per tool call; scoped approvals; Autopilot | Judge + remembered approvals | Explicit signals, explanations | P | S/C |
| Gemini CLI policy engine | 2025 | Google | https://geminicli.com/docs/reference/policy-engine/ | TOML allow/deny/ask_user rules | Vocabulary + layered rules | Contextual | N | S |
| Devin Desktop auto-execution | 2025–26 | Cognition | https://docs.devin.ai/desktop/terminal | "Auto" level: the agent judges command safety | Self-judged gating | Explicit, evaluable | P | C |
| Warp "Agent decides" | 2025–26 | Warp | https://docs.warp.dev/agents/using-agents/agent-profiles-permissions | Act when confident, ask when uncertain | Uncertainty rule | Multi-signal | P | C |
| goose Smart Approval | 2025 | Block/AAIF | https://goose-docs.ai/docs/guides/managing-tools/goose-permissions | LLM-judged risk, per-tool overrides | Risk gate | Richer signals | P | S |
| OpenAI Operator | 2025 | OpenAI | https://cdn.openai.com/operator_system_card.pdf | Trained confirmations (92% recall); watch mode | Severity-aware confirmations | External, inspectable, both error types measured | P | C |
| ChatGPT agent | 2025 | OpenAI | https://cdn.openai.com/pdf/839e66fc-602c-48bf-81d3-b21eacc3459d/chatgpt_agent_system_card.pdf | Confirmation recall 91% (≈100% for critical categories) | Same | Same | P | C |
| Claude in Chrome | 2025 | Anthropic | https://support.claude.com/en/articles/12902428-using-claude-in-chrome-safely | Per-site permissions; classifier screens own actions | Risk screening | Timing, explanations | P | C |
| Gemini in Chrome agentic security | 2025 | Google | https://blog.google/security/architecting-security-for-agentic/ | User Alignment Critic; confirmations; hand back after vetoes | Intent alignment signal | Timing, counterfactuals | P | C |
| Amazon Bedrock Agents confirmation | 2024–25 | AWS | https://docs.aws.amazon.com/bedrock/latest/userguide/agents-userconfirmation.html | Static per-action confirm/return of control | Gate | Dynamic | N | C |
| Amazon Nova Act HITL | 2025 | AWS | https://docs.aws.amazon.com/nova-act/latest/userguide/hitl.html | Developer callbacks for approval/takeover | Ask vs takeover | Run-time decision | N | S/C |
| Salesforce Agentforce escalation | 2024–25 | Salesforce | https://trailhead.salesforce.com/content/learn/modules/trusted-agentic-ai/explore-agentforce-guardrails-and-trust-patterns | Instruction-based handoff to humans | Handoff | Per-action adaptive | N | C |

### 2.3 Guardrails

| Name | Year | Authors/Org | URL | What it does | Overlap | AgentPause differs | Comp. | Type |
|---|---|---|---|---|---|---|---|---|
| NeMo Guardrails | 2023 | NVIDIA | https://docs.nvidia.com/nemo/guardrails/latest/index.html | Programmable rails incl. execution rails | Interception layer | Human involvement | N | S |
| Guardrails AI | 2023 | Guardrails AI | https://guardrailsai.com/docs/concepts/error_remediation | Validators with on-fail actions | Remediation menu | Human + timing | N | S |
| Invariant Guardrails | 2024–25 | Invariant Labs | https://github.com/invariantlabs-ai/invariant | Trace-aware rule language | Trajectory policies | Graded human involvement | N | S |
| LlamaFirewall | 2025 | Meta | https://arxiv.org/abs/2505.03574 | ALLOW / HUMAN_IN_THE_LOOP_REQUIRED / BLOCK scanners | Vocabulary, intent alignment | Usefulness and timing rather than security | P | B |
| GateArena | 2026 | L. Jiang, F. Quinzan, U. Bhatt | https://neurips.cc/virtual/2026/168290 | Parameter-bound warrants for irreversible tools; prompt-only "ask first" is unreliable | Enforcement outside the model | Decides *when* a warrant is needed | P | B |

### 2.4 ML/NLP: asking, clarification, value of information

| Name | Year | Authors/Org | URL | What it does | Overlap | AgentPause differs | Comp. | Type |
|---|---|---|---|---|---|---|---|---|
| Rao & Daumé, EVPI clarification ranking | 2018 | UMD | https://aclanthology.org/P18-1255/ | Neural EVPI ranks clarification questions | EVPI for questions | Whether/when, cost | N | A |
| Uncertainty of Thoughts | 2024 | Hu et al. (NUS et al.) | https://arxiv.org/abs/2402.03271 | Information-gain question selection with lookahead | IG asking | Cost, risk, timing | N | B |
| Active Task Disambiguation | 2025 | Kobalczyk et al. (Cambridge) | https://arxiv.org/abs/2502.04485 | Bayesian experimental design for clarification | Principled asking | Same | N | A |
| GATE | 2023 | Li, Tamkin, Goodman, Andreas | https://arxiv.org/abs/2310.11589 | LM elicits preferences | Preference elicitation | Run-time gating | N | A |
| Uncertainty-Aware Clarification with Information Gain | 2026 | Deng et al. | https://arxiv.org/abs/2606.03135 | IG-rewarded clarifier on τ-bench | CLARIFY | Cost, risk, timing | P | A |
| CIGAsk | 2026 | Li, Wu, Meng (CUHK) | https://arxiv.org/abs/2609.24290 | RL "when and how to clarify" | Learned CLARIFY | Same | P | A |
| Modeling Future Conversation Turns | 2024/25 | Zhang, Knox, Choi | https://arxiv.org/abs/2410.13788 | Lookahead-labelled clarification preference | Downstream value | Action gating | N | A |
| CLARA | 2023 | Park et al. | https://arxiv.org/abs/2306.10376 | Certain / ambiguous / infeasible command classification | 3-way outcome | Mid-trajectory, timing | P | A |
| UALA | 2024 | Han, Buntine, Shareghi | https://arxiv.org/abs/2401.14016 | Calibrated uncertainty → tool → human cascade | Escalation cascade | Consequence, cost | P | B |
| SAUP | 2024 | Zhao et al. (NEC Labs et al.) | https://arxiv.org/abs/2412.01033 | Step-level uncertainty propagation | Signal provider | Consumer of signals | N | A |
| MediQ | 2024 | Li et al. (UW et al.) | https://arxiv.org/abs/2406.00922 | Confidence-gated ask-vs-answer | Gating | Same | N | A |
| Learning When and What to Ask | 2021/22 | Nguyen, Bisk, Daumé | https://arxiv.org/abs/2110.08258 | Hierarchical RL for request type and timing | Request types | Cost/risk model | P | A |
| VNLA; Help, Anna! | 2019 | Nguyen et al. | https://arxiv.org/abs/1812.04155 · https://arxiv.org/abs/1909.01871 | Learned help requests in navigation | Learned asking, progress | LLM tools, cost | N | B |
| Asking Before Acting (ABA) | 2023 | Chen et al. | https://arxiv.org/abs/2305.15695 | Ask before acting in embodied settings | Ask-first | Cost/timing | N | A |
| CLAM | 2022 | Kuhn, Gal, Farquhar | https://arxiv.org/abs/2212.07769 | Selective clarification | Selective asking | Actions | N | A |
| Clarify When Necessary (intent-sim) | 2023 | Zhang, Choi | https://arxiv.org/abs/2311.09469 | Entropy over simulated intents | Intent-ambiguity signal | Combined with risk/timing | P | A |
| STaR-GATE | 2024 | Andukuri et al. | https://arxiv.org/abs/2403.19154 | Training to ask preference questions | Elicitation | When to interrupt | N | A |
| CLAMBER | 2024 | Zhang et al. | https://arxiv.org/abs/2405.12063 | Ambiguity benchmark | Evaluation | n/a | N | A |
| IN3 / Mistral-Interact | 2024 | Qian et al. | https://arxiv.org/abs/2402.09205 | Upfront vagueness detection | Upfront CLARIFY | Mid-trajectory | P | B |
| Ask-before-Plan | 2024 | Zhang et al. (NUS) | https://arxiv.org/abs/2406.12639 | Clarify before planning (travel) | Batch-up-front precedent | Timing-aware | P | A |
| AskToAct | 2025 | Zhang et al. (ZJU) | https://arxiv.org/abs/2503.01940 | Clarification for missing tool parameters | CLARIFY | Cost/risk | N | A |
| Ask-when-Needed (NoisyToolBench) | 2024/25 | Wang et al. (CUHK) | https://arxiv.org/abs/2409.00557 | Prompted asking for unclear instructions | CLARIFY | External policy | N | A |
| When2Call | 2025 | Ross et al. (NVIDIA) | https://arxiv.org/abs/2504.18851 | Tool call vs follow-up vs abstain benchmark | Decision subset | Approval, DEFER | P | B |
| AskBench | 2026 | Zhao, Fang, Cheng | https://arxiv.org/abs/2602.11199 | Rubric-guided RLVR for clarification | Learned asking | Actions | N | A |
| Ambig-SWE | 2025/26 | Vijayvargiya et al. (CMU) | https://arxiv.org/abs/2502.13069 | Underspecification detection is the bottleneck | Motivation | Policy | N | A |
| Ask or Assume? | 2026 | Edwards, Schuster | https://arxiv.org/abs/2603.26233 | Separate underspecification detector for coding agents | Detector beside executor | Consequence, timing | P | A |
| τ-bench / τ²-bench | 2024/25 | Yao et al.; Barres et al. (Sierra) | https://arxiv.org/abs/2406.12045 · https://arxiv.org/abs/2506.07982 | Simulated-user tool benchmarks | Possible substrate | n/a | N | B |
| PPP / UserVille | 2025/26 | Sun et al. (CMU) | https://arxiv.org/abs/2511.02208 | RL with question-effort cost + preferences | Effort-costed asking | Middleware, risk, timing | P | A |
| Ask Now, Use Later (ATRBench) | 2026 | Wu et al. | https://arxiv.org/abs/2605.28108 | Ask now for preferences needed later | Cross-session timing | Within-trajectory gating | P | A |
| HiL-Bench | 2026 | Trinh et al. (Scale AI) | https://arxiv.org/abs/2604.09408 | Ask-F1: over-asking vs silent guessing | Unnecessary/missed analogue | Policies, timing | P | A |
| AppWorld-UL | 2026 | Chen et al. | https://arxiv.org/abs/2607.20536 | User-in-the-loop benchmark: clarify/confirm/infeasible | Simulated users | Policies, timing | P | A |
| SteerBench-Work | 2026 | Serdar, Mertayak | https://arxiv.org/abs/2608.12654 | Proceed vs hold; over-hold 28.1% vs unsafe allow 1.0% | Unnecessary/missed analogue | Timing, DEFER | P | A |
| UnderSpecBench (Coding Agents Are Guessing) | 2026 | Ji et al. | https://arxiv.org/abs/2607.02294 | 55.8–67.8% of runs violate action boundaries | Motivation | Policy | N | A |
| Ask, Relax, or Act? | 2026 | Li et al. | https://arxiv.org/abs/2610.03102 | Act when an action is shared across admissible preferences | Don't-ask-unnecessarily principle | Timing | N | A |
| RegretBench | 2026 | Ta et al. | https://arxiv.org/abs/2607.21143 | Regret-based clarification evaluation | Interaction cost | Action gating | N | A |
| When to Ask a Question (GenAI tools) | 2026 | Park, Donahue, Raghavan | https://arxiv.org/abs/2605.11240 | Theory: user burden vs preference representation | Cost of asking | System | N | A |

### 2.5 Robotics, interactive imitation learning, assistance games

| Name | Year | Authors/Org | URL | What it does | Overlap | AgentPause differs | Comp. | Type |
|---|---|---|---|---|---|---|---|---|
| Off-Switch Game | 2016/17 | Hadfield-Menell et al. | https://arxiv.org/abs/1611.08219 | Uncertainty about utility → incentive to defer | Theory of deferring | Operational | N | A |
| CIRL | 2016 | Hadfield-Menell et al. | https://arxiv.org/abs/1606.03137 | Assistance-game framing | Query when informative | Explicit costed interventions | N | A |
| Should Robots be Obedient? | 2017 | Milli et al. | https://arxiv.org/abs/1705.09990 | Obey vs infer preferences | Deference | System | N | A |
| Sliding autonomy for assembly | 2006 | Sellner et al. (CMU) | https://publications.ri.cmu.edu/coordinated-multi-agent-teams-and-sliding-autonomy-for-large-scale-assembly | Request operator help from performance models; re-entry cost | Asking + switching cost | LLM agents, reversibility | N | A |
| SafeDAgger | 2016/17 | Zhang, Cho | https://arxiv.org/abs/1605.06450 | Learned safety classifier hands control to the expert | Learned gate | Multi-signal, explanations | N | A |
| EnsembleDAgger | 2018/19 | Menda et al. | https://arxiv.org/abs/1807.08364 | Ensemble-variance-gated handover | Uncertainty gate | Same | N | A |
| LazyDAgger | 2021 | Hoque et al. | https://arxiv.org/abs/2104.00053 | Fewer context switches | Switch cost as an objective | Batching/DEFER | P | A |
| ThriftyDAgger | 2021 | Hoque et al. | https://arxiv.org/abs/2109.08273 | Novelty + risk gating under an intervention budget | Multi-signal gating with budget | LLM agents, timing | P | A |
| Fleet-DAgger | 2022 | Hoque et al. | https://arxiv.org/abs/2206.14349 | Allocating scarce human attention across robots | Attention as a resource | Single user | P | A |
| Explore until Confident | 2024 | Ren et al. | https://arxiv.org/abs/2403.15941 | Calibrated stopping | Timing | Human-facing | N | A |
| Collaborative control (Robot, asker of questions) | 2003 | Fong, Thorpe, Baur | https://doi.org/10.1016/S0921-8890(02)00378-0 | Robot asks a human, adapting to availability † | Asking architecture | Risk-aware timing | N | A |
| Interruptibility-aware robot | 2018 | Banerjee, Silva, Chernova | https://doi.org/10.1145/3277902 | Robot times help requests to human interruptibility | Timing by interruptibility | Action risk, reversibility | P | A |

### 2.6 Learning to defer, abstention, irreversibility, risk benchmarks

| Name | Year | Authors/Org | URL | What it does | Overlap | AgentPause differs | Comp. | Type |
|---|---|---|---|---|---|---|---|---|
| Predict Responsibly (learning to defer) | 2018 | Madras, Pitassi, Zemel | https://arxiv.org/abs/1711.06664 | Defer, accounting for the human decision-maker | Deferral | Sequential, timing | N | A |
| Consistent estimators for L2D | 2020 | Mozannar, Sontag | https://arxiv.org/abs/2006.01862 | Surrogate loss for deferral | Learned deferral | Same | N | A |
| DeCCaF | 2024 | Alves et al. (Feedzai) | https://arxiv.org/abs/2403.06906 | Deferral under reviewer capacity | Capacity constraint | Same | N | A |
| Know Your Limits (abstention survey) | 2024 | Wen et al. (UW) | https://arxiv.org/abs/2407.18418 | Abstention taxonomy | BLOCK background | n/a | N | A |
| AbstentionBench | 2025 | Kirichenko et al. (Meta) | https://arxiv.org/abs/2506.09038 | Reasoning LLMs abstain less | Motivates an external gate | n/a | N | A |
| AgentAbstain | 2026 | Liu et al. | https://arxiv.org/abs/2607.10059 | Agents act irreversibly before recognizing the trigger | Motivation, evaluation | System | N | B |
| Leave No Trace | 2017/18 | Eysenbach et al. | https://arxiv.org/abs/1711.06782 | Abort before irreversible states | Reversibility trigger | Ask a human | N | A |
| Relative reachability | 2018 | Krakovna et al. | https://arxiv.org/abs/1806.01186 | Side-effect penalty | Reversibility measure | Decision use | N | A |
| No Turning Back | 2021 | Grinsztajn et al. | https://arxiv.org/abs/2106.04480 | Learned reversibility estimator | Signal provider | Decision use | N | A |
| PAINT | 2022 | Xie et al. (Stanford) | https://arxiv.org/abs/2210.10765 | Ask for help on entering irreversible states | Reversibility → ask | Ask *before* commit | P | B |
| Avoiding Catastrophe by Asking for Help | 2024/25 | Plaut, Zhu, Russell | https://arxiv.org/abs/2402.08062 | Theory: asking enables safe learning under irreversibility | Theory | Practical system | N | A |
| Safe Learning Under Irreversible Dynamics | 2025 | Plaut et al. | https://arxiv.org/abs/2502.14043 | Novelty + irreversibility asking | Same | Same | N | A |
| GoEX | 2024 | Patil et al. (Berkeley) | https://arxiv.org/abs/2404.06921 | Undo, damage confinement, post-facto validation | Reversibility makes asking unnecessary | Complementary | P | B |
| Revisable by Design | 2026 | Zhai, Li, Wang | https://arxiv.org/abs/2604.23283 | "Flexibility is bounded by reversibility" | Theory of reversibility | Pre-commit gating | P | A |
| Causal Delta World Models (CDWM) | 2026 | Yue et al. | https://neurips.cc/virtual/2026/poster/154820 | Predicts reversibility, irreversible cost and confidence; abstains | Signal provider | Brings in the human | P | A |
| Path-Based Authorization | 2026 | Baek | https://icml.cc/virtual/2026/77995 | Causal-chain check for irreversible actions | Provenance signal | Cost/timing | N | A |
| ToolEmu | 2023/24 | Ruan et al. | https://arxiv.org/abs/2309.15817 | LM-emulated sandbox + severity evaluator | Severity signal | Decision layer | N | B |
| R-Judge | 2024 | Yuan et al. | https://arxiv.org/abs/2401.10019 | LLM risk-awareness benchmark | Signal reliability | n/a | N | B |
| Agent-SafetyBench | 2024 | Zhang et al. | https://arxiv.org/abs/2412.14470 | Agent safety benchmark | Evaluation | n/a | N | B |
| AgentHarm | 2024/25 | Andriushchenko et al. | https://arxiv.org/abs/2410.09024 | Harmful-task benchmark | BLOCK | n/a | N | A |
| AgentDojo | 2024 | Debenedetti et al. | https://arxiv.org/abs/2406.13352 | Prompt-injection environment | Off-intent detection | n/a | N | B |
| ST-WebAgentBench | 2024/26 | Levy et al. (IBM) | https://arxiv.org/abs/2410.06703 | User-consent policy dimension | Measures asking for consent | n/a | N | B |
| WebGuard | 2025 | Zheng et al. | https://arxiv.org/abs/2507.14293 | Risk-labelled state-changing web actions | Severity predictor | Combined decision | P | B |
| Progent | 2025 | Shi et al. | https://arxiv.org/abs/2504.11703 | Privilege policies; expansions need approval | BLOCK by policy | Cost/timing | P | A |
| Conseca | 2025 | Tsai, Bagdasarian | https://arxiv.org/abs/2501.17070 | Just-in-time contextual policies; confirmations don't scale | Shared critique | Calibrates confirmations | P | A |
| GuardAgent / ShieldAgent | 2024/25 | Xiang et al.; Chen et al. | https://arxiv.org/abs/2406.09187 · https://arxiv.org/abs/2503.22738 | Guard agents with verifiable rules | External monitor | Human, cost, timing | N | B/A |
| No Action Without a NOD | 2026 | Yang et al. | https://arxiv.org/abs/2605.12240 | Agent overseer before critical actions | Selective gating | Human overseer | P | A |
| HULA | 2024/25 | Takerngsaksiri et al. | https://arxiv.org/abs/2411.12924 | Fixed plan/code review stages | Fixed-stage baseline | Adaptive placement | P | A |
| AHCE | 2026 | Wang, He, Lu | https://arxiv.org/abs/2602.22546 | Learned requests for expert reasoning | Learned human query | Same | P | A |
| Proactive Agent (ProactiveBench) | 2024 | Lu et al. | https://arxiv.org/abs/2410.12361 | Reward model on accept/reject of proactive offers | Learns welcomeness | Action gating | P | A |
| Collaborative Gym | 2024/26 | Shao et al. (Stanford) | https://arxiv.org/abs/2412.15701 | Asynchronous human-agent collaboration framework | Testbed | Decision policy | P | B |
| Reframing Agent Security as Agent–Human Interaction | 2026 | Wang, Li, Tian | https://arxiv.org/abs/2605.24309 | Approval fatigue vs uncontrolled autonomy survey | Problem statement | Solution | N | A |
| The Saturation Trap | 2026 | Modgil | https://arxiv.org/abs/2606.04296 | Annotators agree on intervention timing at α = 0.047 | **Threat to label validity** | Scripted ground truth (with caveats) | N | B |
| Oversight-related position papers | 2025–26 | Mitchell et al. (×2) | https://arxiv.org/abs/2502.02649 · https://arxiv.org/abs/2608.23642 | Fully autonomous agents should not be developed; agents push humans out of the loop | Normative motivation | n/a | N | A |
| Optimizing Agent Planning for Security and Autonomy | 2026 | Kolluri et al. (Microsoft) | https://arxiv.org/abs/2602.11416 | Autonomy = share of consequential actions without HITL | Metric idea | n/a | N | A |
| How Agents Ask for Permission | 2026 | Michael, Roesner | https://neurips.cc/virtual/2026/168232 | Taxonomy of permission systems | Background | n/a | N | A |
| Safety Decisions Behind LLM Agents (census) | 2026 | de Oliveira et al. | https://neurips.cc/virtual/2026/168217 | "None of the 18 works compares a gate against no gate on a safety outcome" | Evaluation gap | Fills it in simulation | N | A |
| Towards Automating Data Access Permissions in AI Agents | 2025/26 | Wu et al. | https://arxiv.org/abs/2511.17959 | Predicts permission decisions from history (85.1%) | History signal | Timing, EV, reversibility | P | A |
| TELEMACHUS / AEGIS (RishiM19) / when-to-ask (xtid) | 2026 | individuals | https://github.com/gdtsitlauri/telemachus · https://github.com/RishiM19/AEGIS · https://github.com/ahmd-mohsin/when-to-ask | Calibrated escalation gate; competence/risk/novelty/uncertainty fusion; hidden-state timing signal | Conceptual neighbours | Breadth, evaluation | P | S |

### 2.7 HCI: interruption, automation, trust, oversight interfaces

| Name | Year | Authors/Org | URL | What it does | Overlap | AgentPause differs | Comp. | Type |
|---|---|---|---|---|---|---|---|---|
| McFarlane: four coordination methods | 2002 | D. C. McFarlane | https://doi.org/10.1207/S15327051HCI1701_2 | Immediate / negotiated / mediated / scheduled; negotiated best overall † | Design space for ASK vs DEFER | Chooses the method per action | N | A |
| Diary study of task switching | 2004 | Czerwinski, Horvitz, Wilhite | https://doi.org/10.1145/985692.985715 | Interruptions and difficult re-entry † | Re-entry support | Automatic re-entry context | N | A |
| Cost of interrupted work | 2008 | Mark, Gudith, Klocke | https://doi.org/10.1145/1357054.1357072 | Interruptions → faster work but more stress | Cost is subjective | Measure workload + stress | N | A |
| Memory for goals; interruption lag | 2002–08 | Altmann, Trafton et al. | https://doi.org/10.1207/s15516709cog2601_2 | Pre-alerts speed resumption † | Pre-alert for DEFER | Applies to agent oversight | N | A |
| Attention-aware systems | 2006 | Bailey, Konstan | https://doi.org/10.1016/j.chb.2005.12.009 | Mid-task interruptions cost more than boundary interruptions † | Breakpoint evidence | Agent domain | N | A |
| Deferred task interruptions | 2010 | Salvucci, Bogunovich | https://doi.org/10.1145/1753326.1753340 | When users may defer, they switch at low workload 94% of the time | Supports DEFER | Predicts low-load moments | N | A |
| Predicting interruptibility with sensors | 2003/05 | Fogarty et al. (CMU) | https://doi.org/10.1145/1057237.1057243 | Simple sensors predict interruptibility † | Load proxy | Uses interaction telemetry | N | A |
| Beyond Interruptibility | 2017 | Pielot et al. | https://doi.org/10.1145/3130956 | Predicting engagement, not just attention | Meaningful responses | Detect rubber-stamping | N | A |
| Levels of automation | 1978 | Sheridan, Verplank | https://ntrl.ntis.gov/NTRL/dashboard/searchResults/titleDetail/ADA057655.xhtml | Origin of the LOA scale † | Outputs map to levels | Per-action selection | N | A |
| Types and levels of automation | 2000 | Parasuraman, Sheridan, Wickens | https://doi.org/10.1109/3468.844354 | Consequence cost as an automation criterion † | Severity/reversibility | Runtime policy | N | A |
| Adaptive automation & SA | 2004 | Kaber, Endsley | https://doi.org/10.1080/1463922021000054335 | LOA and adaptive allocation effects | Adaptive automation | Content-dependent triggers | N | A |
| Characterization of adaptive systems | 2012 | Feigh, Dorneich, Hayes | https://doi.org/10.1177/0018720812443983 | Trigger/adaptation taxonomy † | Vocabulary | Instantiation | N | A |
| Trust in Automation | 2004 | Lee, See | https://doi.org/10.1518/hfes.46.1.50_30392 | Calibrated trust; misuse/disuse † | Calibration | Uses history to detect over-reliance | N | A |
| Complacency and bias | 2010 | Parasuraman, Manzey | https://doi.org/10.1177/0018720810376055 | Complacency under multitasking † | Rubber-stamping | Defer under high load | N | A |
| Ironies of Automation | 1983 | Bainbridge | https://doi.org/10.1016/0005-1098(83)90046-8 | Residual human role becomes harder | Re-entry | Context in every ASK | N | A |
| SAT agent transparency | 2018 | Chen et al. (ARL) | https://doi.org/10.1080/1463922X.2017.1315750 | Three levels of transparency † | Explanation content | Scaled to decision | N | A |
| Maes; Shneiderman & Maes debate | 1994/97 | Maes; Shneiderman, Maes | https://doi.org/10.1145/176789.176792 · https://doi.org/10.1145/267505.267514 | Learning interface agents; control vs delegation † | History of user decisions | Risk gating | N | A |
| Mixed-Initiative Interaction | 1999 | Allen, Guinn, Horvitz | https://doi.org/10.1109/5254.796083 | Initiative shifts † | Policy for shifts | n/a | N | A |
| Guidelines for Human-AI Interaction | 2019 | Amershi et al. | https://doi.org/10.1145/3290605.3300233 | 18 guidelines, incl. G3 timing, G10 scope when in doubt, G11 explain why | Operationalized by AgentPause | Computational | N | A |
| Human-Centered AI | 2020 | Shneiderman | https://doi.org/10.1080/10447318.2020.1741118 | High control + high automation † | Hypothesis framing | Testable mechanism | N | A |
| Challenges in Human-Agent Communication | 2024 | Bansal et al. (Microsoft) | https://arxiv.org/abs/2412.10380 | A2 "what is it about to do", U1 goals, X3 level of detail | Problem statement | Policy | N | A |
| Levels of AGI | 2023/24 | Morris et al. (DeepMind) | https://arxiv.org/abs/2311.02462 | Autonomy levels and paradigms | Static taxonomy | Per-action | N | A |
| Task delegability | 2019 | Lubars, Tan | https://arxiv.org/abs/1902.03245 | Risk and trust shape delegation | Preferences/risk | Runtime | N | A |
| CowPilot | 2025 | Huq et al. (CMU) | https://arxiv.org/abs/2501.16609 | Human-initiated pause/override | Shared control | System-initiated | P | B |
| "Here, Let Me Help" | 2026 | Kim et al. | https://doi.org/10.1145/3772318.3791536 | Users intervene mostly over slowness † | User-initiated ≠ safety | Show progress/ETA | N | A |
| Overseeing Agents Without Constant Oversight | 2026 | Grunde-McLaughlin et al. | https://arxiv.org/abs/2602.16844 | Better traces cut error-finding time, not accuracy | Oversight burden | Focus attention | N | A |
| Cocoa | 2024/26 | Feng et al. | https://arxiv.org/abs/2412.10999 | Interactive plans with agent/user steps | Plan-step granularity | Automatic step selection | P | B |
| Plan-Then-Execute | 2025 | He, Demartini, Gadiraju | https://doi.org/10.1145/3706598.3713218 | Necessary user involvement matters; over/under-trust | Selective involvement | Risk-calibrated | N | A |
| AGDebugger | 2025 | Epperson et al. | https://arxiv.org/abs/2503.02068 | Pause, edit, reset multi-agent runs | Steering | Automatic pausing | N | B |
| WaitGPT | 2024 | Xie et al. | https://doi.org/10.1145/3654777.3676374 | Live code visualization for steering | Monitoring | Policy | N | B |
| Plover; Sidekick | 2026 | Venkatesan et al.; Chang et al. | https://arxiv.org/abs/2607.15193 · https://arxiv.org/abs/2607.17527 | Plan-centric steering; ambient cues + return summaries | DEFER presentation | Decision policy | N | B |
| Unintended Consequences of GUI Agents | 2026 | Zhang et al. | https://doi.org/10.1145/3772318.3790696 | Misreads, mis-plans, harms | Motivation | n/a | N | A |
| InterruptBench | 2026 | Zou et al. | https://arxiv.org/abs/2604.00892 | User-initiated mid-task intent changes | Reverse direction | Resume after CLARIFY | N | A |
| Value-Sensitive Delegation (OpenClaw) | 2026 | Ma et al. | https://arxiv.org/abs/2609.22067 | Supervision UX is the pain point | Motivation | n/a | N | A |
| Need Help? Proactive programming assistants | 2025 | Chen et al. | https://arxiv.org/abs/2410.04596 | Timing rules; persistent suggestions "annoying" | Breakpoint timing | Action gating | P | A |
| Assistance or Disruption? | 2025 | Pu et al. | https://doi.org/10.1145/3706598.3713357 | Proactivity disrupts; presence cues help | Disruption cost | Stage-aware timing | P | B |
| Inner Thoughts | 2025 | Liu et al. | https://doi.org/10.1145/3706598.3713760 | Motivation-to-speak scoring | "Worth interrupting now?" | Safety gating | N | B |
| ProMemAssist | 2025 | Pu et al. (Meta) | https://doi.org/10.1145/3746059.3747770 | Value vs disruption with a working-memory model | Load + interruption cost | Risk/reversibility override | P | B |
| When to Show a Suggestion? | 2024 | Mozannar et al. | https://doi.org/10.1609/aaai.v38i9.28878 | Learn from accept/reject; optimizing acceptance degrades quality | History signal caution | Don't treat approvals as ground truth | P | A |
| ProAgentBench | 2026 | Tang et al. | https://arxiv.org/abs/2602.04482 | When-to-intervene vs what-to-say | Timing data | Gating | N | B |
| Sensing What Surveys Miss | 2026 | Liu et al. | https://arxiv.org/abs/2602.00880 | Personalized classifiers time LLM help | Timing | Gating | N | A |
| Human-First Pacing / Initiative Auditing | 2026 | Zhu | https://neurips.cc/virtual/2026/162434 | Counterfactual waiting estimate | Closest to timing counterfactuals (not an explanation) | User-facing explanation | P | A |
| PRISM: Festina Lente Proactivity | 2026 | Fu et al. | https://arxiv.org/abs/2602.01532 | Asymmetric-cost gate with internal counterfactual checks | Decision-theoretic gate | User-facing timing explanations | P | B |

### 2.8 Warning and consent habituation; sense of agency

| Name | Year | Authors/Org | URL | What it does | Overlap | AgentPause differs | Comp. | Type |
|---|---|---|---|---|---|---|---|---|
| You've Been Warned | 2008 | Egelman, Cranor, Hong | https://doi.org/10.1145/1357054.1357219 | Active warnings beat passive ones † | Friction proportional to stakes | Adaptive | N | A |
| Trained to Accept? | 2010 | Böhme, Köpsell | https://doi.org/10.1145/1753326.1753689 | Habituated consent clicking † | Rubber-stamping | Rare, varied prompts | N | A |
| How to Ask for Permission | 2012 | Felt et al. | https://www.usenix.org/conference/hotsec12/workshop-program/presentation/felt | Choose a mechanism per permission | Action→intervention mapping | Context-dependent | N | A |
| Alice in Warningland | 2013 | Akhawe, Felt | https://www.usenix.org/conference/usenixsecurity13/technical-sessions/presentation/akhawe | 70.2% clickthrough on Chrome SSL warnings | False positives drive clickthrough | Precision matters | N | A |
| Your Attention Please; Harder to Ignore? | 2013/14 | Bravo-Lillo et al. | https://doi.org/10.1145/2501604.2501610 | Forcing interaction with the critical field defeats habituation | Dialog technique | Used in high-severity ASK | N | A |
| Polymorphic warnings; habituation | 2015–18 | Anderson, Vance et al. | https://doi.org/10.1145/2702123.2702322 | Habituation drops fast; polymorphism slows it † | Habituation model | Vary by risk | N | A |
| Design Space for Privacy Notices | 2015 | Schaub et al. | https://www.usenix.org/conference/soups2015/proceedings/presentation/schaub | Timing: setup / just-in-time / context-dependent / periodic / on demand | Timing vocabulary | Runtime choice | N | A |
| Dynamically Granted Permissions | 2017 | Wijesekera et al. | https://doi.org/10.1109/SP.2017.51 | Prompt only when uncertain about user preference (96.8% accuracy) | History + selective prompting | Agent actions, timing | P | A |
| Alert fatigue in CDSS | 2017 | Ancker et al. | https://doi.org/10.1186/s12911-017-0430-8 | Repeated alerts drive fatigue † | De-duplicate/batch | Agent domain | N | A |
| Cognitive forcing functions | 2021 | Buçinca, Malaya, Gajos | https://doi.org/10.1145/3449287 | Forcing reduces over-reliance, costs satisfaction † | Friction for high stakes | Selective use | N | A |
| "I'm Not Sure, But..." | 2024 | Kim et al. | https://doi.org/10.1145/3630106.3658941 | First-person uncertainty expressions reduce over-reliance † | Explanation phrasing | Applied to ASK | N | A |
| "I did that!" intentional binding | 2012 | Coyle et al. | https://doi.org/10.1145/2207676.2208350 | Implicit sense-of-agency measure † | Agency measurement | Study option | N | A |
| Experience of agency in HCI (review) | 2014 | Limerick, Coyle, Moore | https://doi.org/10.3389/fnhum.2014.00643 | Explicit vs implicit agency measures | Methodology | n/a | N | A |
| Automation and sense of control | 2012 | Berberian et al. | https://doi.org/10.1371/journal.pone.0034075 | Sense of agency decreases with automation level | Core tension | Selective involvement | N | A |
| Sense of Agency Scale | 2017 | Tapal et al. | https://doi.org/10.3389/fpsyg.2017.01552 | 13-item trait agency scale † | Candidate covariate | Needs state adaptation | N | A |
| How does HCI understand agency? | 2023 | Bennett et al. | https://doi.org/10.1145/3544548.3580651 | Self-causality vs self-determination † | Which agency to measure | Measure both | N | A |
| AI Ghostwriter Effect | 2024 | Draxler et al. | https://doi.org/10.1145/3637875 | Ownership vs authorship divergence † | Measure ownership | n/a | N | A |
| HumanAgencyBench | 2025/26 | Sturgeon et al. | https://arxiv.org/abs/2509.08494 | "Ask clarifying questions", "defer important decisions" dimensions | CLARIFY/ASK behaviours | External enforcement | N | B |
| User Autonomy in Human-LLM Interaction (review) | 2026 | Wang, Wang | https://doi.org/10.1145/3772363.3798855 | Steerability theme † | Positioning | n/a | N | A |

### 2.9 Explanations (with emphasis on explaining *timing*)

The closest explanation work is ranked in [research_gap.md, Gap 2](research_gap.md). In short,
the temporal contrastive *question form* exists (Krarup et al. FQ7; Fox et al. Q5/Q6). We found
no user-facing timing explanations for an agent's *human-intervention* decisions.

| Name | Year | Authors/Org | URL | What it does | Overlap | AgentPause differs | Comp. | Type |
|---|---|---|---|---|---|---|---|---|
| **Contrastive Explanations of Plans through Model Restrictions** | 2021 | Krarup, Krivic, Magazzeni, Long, Cashmore, Smith | https://www.jair.org/index.php/jair/article/view/12813 | Taxonomy of contrastive plan questions, including **FQ7 "Why is action A used at time T rather than at least T′ after/before T?"**; answered by restricting the planner and comparing plans | **Same question form** (temporal foil) | Explains *human-intervention* decisions, not planner actions. No PDDL model needed (replays the gating policy). Models human attention cost | P | A |
| Explainable Planning (roadmap) | 2017 | Fox, Long, Magazzeni | https://arxiv.org/abs/1709.10256 | Lists "Why do I (not) need to replan at this point?" | Why-now for an execution-time trigger | Generator + user study; human hand-off, not replanning | P | A |
| **Why Do I Have to Drive Now? Post Hoc Explanations of Takeover Requests** | 2018 | Körber, Prasch, Bengler | https://doi.org/10.1177/0018720817747730 | Explaining the *reason* for an automated vehicle's takeover request raised understanding, not trust | Same decision type (automation → human) | Adds earlier/later counterfactuals; multi-step LLM agents | P | A |
| Explaining an Increase in Predicted Risk for Clinical Alerts | 2020 | Hardt et al. (Google) | https://arxiv.org/abs/1907.04911 | Attributes a risk *increase* (why an alert fires now) to recent inputs | Mechanism for "why not one step earlier" | Contrast across steps; decision categories; agents | P | A |
| Time2Stop | 2024 | Orzikulova et al. | https://arxiv.org/abs/2403.05584 | ML-timed smartphone interventions with SHAP top-factor explanations; explanations improved accuracy and receptivity (N = 71, 8 weeks) | Factor explanations of timed interventions | Counterfactual timing; agent oversight | P | A |
| Why and Why Not Explanations | 2009 | Lim, Dey, Avrahami | https://doi.org/10.1145/1518701.1519023 | "Why" improved understanding and trust; **"why not" lowered understanding** | Our "why not earlier/later" are why-not questions | Lead with "why now"; test, don't assume (H4) | N | A |
| Assessing Demand for Intelligibility | 2009 | Lim, Dey | https://doi.org/10.1145/1620545.1620576 | Taxonomy: why, why not, how, what if, certainty, control… | Question types | Adds "when / why now" | N | A |
| Intelligibility Toolkit | 2010 | Lim, Dey | https://doi.org/10.1145/1864349.1864353 | Auto-generated why/why-not explanations † | Middleware-generated explanations | Timing counterfactuals for agent interventions | N | B |
| Explanation in AI: Insights from the Social Sciences | 2019 | Miller | https://arxiv.org/abs/1706.07269 | Explanations are contrastive, selected, social | Temporal foil = contrastive | Concrete implementation | N | A |
| Counterfactual Explanations without Opening the Black Box | 2017/18 | Wachter, Mittelstadt, Russell | https://arxiv.org/abs/1711.00399 | Minimal input change that flips a decision | Our feature counterfactuals | Also perturbs *time index* | N | A |
| Questioning the AI (XAI Question Bank) | 2020 | Liao, Gruen, Miller | https://arxiv.org/abs/2001.02478 | Prototypical user questions for XAI UX | Question-driven design | Timing-specific questions | N | A |
| Plan Explanations as Model Reconciliation | 2017 | Chakraborti, Sreedharan, Zhang, Kambhampati | https://www.ijcai.org/proceedings/2017/23 | Explanation as human-model update | "Why not earlier" as a model mismatch | Intervention timing | N | A |
| Contrastive Explanations for RL (expected consequences) | 2018 | van der Waa et al. | https://arxiv.org/abs/1807.08706 | Policy vs foil-policy consequences | "Why not later" via consequences | Foil is a *time*, not a policy | N | A |
| Explainable RL Through a Causal Lens | 2020 | Madumal, Miller, Sonenberg, Vetere | https://arxiv.org/abs/1905.10958 | Counterfactual causal explanations; evaluated with Explanation Satisfaction | Evaluation template | When to escalate, not which action | N | A |
| HIGHLIGHTS | 2018 | Amir, Amir | https://cris.bgu.ac.il/en/publications/highlights-summarizing-agent-behavior-to-people/ | Summaries from important states | Important moments | Local timing explanations | N | A |
| Establishing Appropriate Trust via Critical States | 2018 | Huang, Bhatia, Abbeel, Dragan | https://arxiv.org/abs/1810.08174 | Shows humans *when to take control* | Inverse of AgentPause | System decides and explains | P | A |
| Counterfactual Explanations in Sequential Decision Making | 2021 | Tsirtsis, De, Gomez-Rodriguez | https://arxiv.org/abs/2107.02776 | Counterfactual action sequences in MDPs | Machinery for "ask at j instead of k" | Human-intervention semantics | P | A |
| Redefining Counterfactual Explanations for RL (survey) | 2024 | Gajcin, Dusparic | https://arxiv.org/abs/2210.11846 | Counterfactuals for sequential settings | Positioning | n/a | N | A |
| Why did my car just do that? | 2015 | Koo et al. | https://www.wendyju.com/publications/WhyDidMyCarJustDoThat.pdf | "Why" messages improve driving | Reason-first | Timing counterfactuals | N | A |
| Look Who's Talking Now | 2019 | Du et al. | https://arxiv.org/abs/1905.08878 | Explaining *before* acting raises trust | When to explain | Why the intervention happened when it did | N | A |
| Explaining Before or After Acting? | 2021 | Stange, Kopp | https://doi.org/10.1007/978-3-030-90525-5_13 | Explaining before an undesirable act lowered control and trust | BLOCK/DEFER explanation placement | Measured outcome | N | A |
| Reactive or Proactive? How Robots Should Explain Failures | 2024 | LeMasurier et al. | https://doi.org/10.1145/3610977.3634963 | Proactive failure explanations enlist human help earlier | Close in spirit | Justifies the specific step | P | A |
| "Why This Avoidance Maneuver?" | 2026 | Jose et al. | https://arxiv.org/abs/2604.08032 | Contrastive explanations for supervised autonomy | Supervised agent | Timing foil | N | A |
| Why and When: System Initiative in Conversational Search | 2023 | Avula, Choi, Arguello | https://arxiv.org/abs/2303.13484 | How human wizards justify initiative timing | Reason-code design input | System-generated | N | A |
| Exploring the Cost of Interruptions in Human-Robot Teaming | 2023 | Mannem, Macke, Stone, Mirsky | https://arxiv.org/abs/2311.00785 | Interrupting robots seen as less helpful | Cost of asking | Explanations | N | A |
| Developer Interaction Patterns with Proactive AI | 2026 | Kuo et al. | https://arxiv.org/abs/2601.10253 | Interventions at workflow boundaries got 52% engagement | Breakpoints | Explanations | N | A |
| Anticipatory Human Oversight of Agentic AI | 2026 | Baum, Kiener, Langer, Laux | https://arxiv.org/abs/2609.24242 | Pre-specified escalation conditions | Normative framing | System | N | A |
| Does the Whole Exceed its Parts? | 2021 | Bansal et al. | https://doi.org/10.1145/3411764.3445717 | Explanations raise acceptance regardless of correctness | Over-reliance risk | Measure appropriate reliance | N | A |
| Explanations Can Reduce Overreliance | 2023 | Vasconcelos et al. | https://doi.org/10.1145/3579605 | Helps when explanations reduce verification cost | Design goal | Show what changed and what will happen | N | A |
| Effect of Confidence and Explanation on Trust Calibration | 2020 | Zhang, Liao, Bellamy | https://doi.org/10.1145/3351095.3372852 | Confidence helps calibration | Show calibrated scores | n/a | N | A |
| Appropriate Reliance on AI Advice (RAIR/RSR) | 2023 | Schemmer et al. | https://doi.org/10.1145/3581641.3584066 | Appropriateness-of-reliance metrics | Our reliance metrics | n/a | N | A |
| Are Explanations Helpful? | 2021 | Wang, Yin | https://doi.org/10.1145/3397481.3450650 | Counterfactual explanations underperformed | Caution | Test empirically | N | A |
| Manipulating and Measuring Model Interpretability | 2021 | Poursabzi-Sangdeh et al. | https://doi.org/10.1145/3411764.3445315 | More transparency reduced detection of large errors | Keep explanations short | Progressive disclosure | N | A |
| Placebic Explanations | 2019 | Eiband et al. | https://doi.org/10.1145/3290607.3312787 | Content-free reasons raise trust as much as real ones | **Placebic control in study design** | n/a | N | A |
| Interpreting Interpretability | 2020 | Kaur et al. | https://doi.org/10.1145/3313831.3376219 | Experts misuse interpretability tools | Developer over-trust in factors | n/a | N | A |
| Explainability Pitfalls | 2021 | Ehsan, Riedl | https://arxiv.org/abs/2109.12480 | Unwarranted trust from numeric explanations | Risk register | n/a | N | A |

### 2.10 Questionnaires (for the study mode)

The licensing verdicts below came from the explanations thread. They determine what the
repository ships (see `docs/experiments.md` and `instruments/`).

| Instrument | Citation | Terms stated by source | What AgentPause ships |
|---|---|---|---|
| NASA-TLX / Raw TLX | Hart & Staveland 1988; Hart 2006 | NASA: "open source", no permission needed to use or modify | Full definition (6 subscales) + Raw-TLX scoring |
| SUS | Brooke 1996 | "freely available… acknowledge the source"; © DEC 1986 | Scoring + structure; **item text not bundled** (the project brief asks us not to reproduce copyrighted questionnaires unnecessarily). Researchers load the official text locally |
| Körber Trust in Automation | Körber 2019 | CC BY-SA 4.0 (English version not validated) | Reference + loader slot (not bundled; ShareAlike licensing would need a separately licensed folder) |
| Hoffman et al. 2023 Explanation Satisfaction / XAI Trust | Frontiers in Computer Science 2023 | CC BY 4.0 | Reference + loader slot |
| Jian et al. 2000 trust; TOAST; Merritt 2011; UMUX(-LITE); UEQ(-S) | see notes | No reuse license found, or "All Rights Reserved" | Reference + placeholder only |
| Sense of Agency Scale | Tapal et al. 2017 | CC BY | Reference only: it measures *trait* agency, not control over an AI |
| AgentPause post-task probes | this project | MIT (our own items) | Bundled, **labelled non-validated** |

---

## Not verified (excluded)

These were seen only in search snippets or could not be fetched. They are **not** used as evidence:

- Google Project Mariner confirmation behaviour.
- OpenAI Operator launch and help pages (HTTP 403). The system cards were used instead.
- Salesforce per-action confirmation settings.
- Invariant Explorer.
- UserBench (arXiv 2507.22034).
- "Learning to Interrupt in Language-based Multi-agent Communication" (arXiv 2604.06452).
- FALCON (fatigue-aware deferral).
- irredux.
- "When2Speak" MIR/FIR metrics (arXiv 2605.05626).
- Rosenthal & Veloso CoBot asking work.
- GA-Rollback / WebRollback.
- Horvitz, Jacobs & Hovel "Attention-sensitive alerting" (UAI 1999).
- Maes's "tell-me / do-it" thresholds.

---

## Addendum: second search during the final audit (October 2026)

These items were found or checked after the toolkit was built. Their effect on the claims is
discussed in [novelty_audit.md](novelty_audit.md) §3.

| Work | Year | Venue | URL | Relation to AgentPause |
|---|---|---|---|---|
| Kiyani, Noorani, Pappas & Hassani, *Strategic Decision Support for AI Agents* | 2026 | arXiv:2606.12587 | https://arxiv.org/abs/2606.12587 | Help-seeking as a threshold on support value with online calibration. Same family as the myopic value-of-asking baseline; no timing or explanations |
| Zhang et al., *Calibration Is Not Control: Intervention Value for LLM-Agent Oversight* | 2026 | arXiv:2606.21399 | https://arxiv.org/abs/2606.21399 | Trains oversight on intervention utility instead of failure labels; hands off to a stronger model, not a human |
| Piatrashyn et al., *ReDAct: Uncertainty-Aware Deferral for LLM Agents* | 2026 | arXiv:2604.07036 | https://arxiv.org/abs/2604.07036 | Deferral of the current step to a larger model; not human-facing |
| Hamid, Li & Liang, *When2Talk: When Should a Proactive In-Car Agent Talk?* | 2026 | arXiv:2609.12503 | https://arxiv.org/abs/2609.12503 | Context-sensitive immediate / delayed / silent communication; VR study (n = 41) found better perceived appropriateness and less interruption, with no trust difference. Closest new work to DEFER, in a different domain |
| Love, Andriella & Alenyà, *Temporal Counterfactual Explanations of Behaviour Tree Decisions* | 2025/2026 | arXiv:2509.07674 | https://arxiv.org/abs/2509.07674 | Causal counterfactual answers to contrastive "why" questions about robot decisions; adjacent to timing explanations |
| *AgentAbstain: Do LLM Agents Know When Not to Act?* | 2026 | arXiv:2607.10059 | https://arxiv.org/abs/2607.10059 | Benchmark for abstention; related to testbeds |
| `agentpause` on PyPI (A. L. Ciampolillo) | 2026 | PyPI | https://pypi.org/project/agentpause/ | Unrelated project with the same name (rate-limit scheduling for LLM agents). Reason our distributions are named `agentpause-toolkit` etc. |


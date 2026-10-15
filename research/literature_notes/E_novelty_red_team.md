# E. Novelty Red-Team: AgentPause (Adaptive Human Intervention Timing for AI Agents)

Date of audit: 2026-10-14. Auditor role: adversarial ("find the closest work that undermines novelty").

## 0. Bottom line

**AgentPause cannot claim to be the first adaptive, decision-theoretic "when to ask" policy for LLM agents.** Since late 2025 several papers have shipped parts of it:

- **Value of Information: A Framework for Human-Agent Communication** (Dong et al., ACL 2026 Oral; code on GitHub). It uses exactly the "expected gain from asking − cost of interrupting" rule, in flight booking and e-commerce domains. Baselines include never-ask, a fixed number of questions, and a confidence threshold.
- **When Should Users Check?** (Zhou et al., CHI '26). It decides where in a multi-step agent task to place confirmation checkpoints, using a decision-theoretic dynamic-programming model. It compares against confirm-at-end and random checkpoint placement, and includes a 48-person user study. One of its domains is shopping.
- **Modeling Distinct Human Interaction in Web Agents** (Huq et al., CMU, 2026; code on GitHub). At each step it predicts whether to ask the user or continue, using the history of what that user did earlier. It is deployed in a Chrome extension and has a timing-aware metric.
- **Ask Early, Ask Late, Ask Right** (Gulati et al., PwC, May 2026). It measures empirically how much a clarification is worth depending on when in a long-horizon agent run it is asked.
- **Horvitz, CHI 1999 (LookOut).** It already had expected-utility thresholds that choose between inaction, dialog and action. Users could set the utilities, and the system deferred actions to a less distracting moment based on a model of the user's attention.

**What still looks defensible (as integration and specific mechanisms, not as a concept):**

1. **DEFER as an explicit action.** No verified LLM-agent work has a policy that holds a pending question and re-times or batches it to a natural breakpoint, such as just before the first irreversible step.
2. **Counterfactual timing explanations** ("why didn't you ask earlier / later"). Nothing found.
3. **All the signals in one model.** No verified work combines uncertainty, intent ambiguity, consequence severity, reversibility, interruption cost, cognitive load, user preferences and the user's past decisions in a single model.
4. **A deterministic, multi-scenario, open testbed for comparing policies.** It would compare never / always / threshold / adaptive / user-customized policies, with unnecessary-intervention and missed-intervention metrics plus a user-study mode. Only small, fragmentary versions exist, and one is being actively built now (SPAR, Fall 2026).

Caveats:
- My web-search budget ran out before I could check whether the name "AgentPause" is already taken. Do that before publishing.
- OpenAI's Operator pages returned 403, so Operator is excluded from the verified list.

---

## 1. Method

- About 70 distinct WebSearch queries and about 75 WebFetch verifications. Sources covered: arXiv, ACL Anthology, PMLR/ICML, NeurIPS/ICLR virtual sites, GitHub, Anthropic/Microsoft/Cursor/LangChain docs, and the original Horvitz CHI'99 PDF, whose text I extracted locally to check the quotes.
- **Only items whose page I actually fetched are in the main list.** Items I saw only in search snippets are listed in Section 6 as unverified leads and are not used as evidence.
- Threat level is judged against AgentPause's stated contributions: the adaptive multi-signal policy, the EV-of-asking model, DEFER/batching, counterfactual timing explanations, the simulator plus policy-comparison framework, and the metrics.

---

## 2. Summary table

| # | Item | Year | Type | Direct competitor? | Threat |
|---|---|---|---|---|---|
| H1 | Value of Information (VoI) framework for human-agent communication (Dong et al., Cambridge/MIT) | 2026 | both (paper + code) | Partial → close to yes on the decision rule | **HIGH** |
| H2 | When Should Users Check? Confirmation frequency in multi-step agentic tasks (Zhou et al., CHI'26) | 2025/26 | academic | Yes, on timing/placement | **HIGH** |
| H3 | Modeling Distinct Human Interaction in Web Agents (CowCorpus / PlowPilot, CMU) | 2026 | both | Yes, on per-step "ask vs continue" | **HIGH** |
| H4 | Ask Early, Ask Late, Ask Right: clarification timing for long-horizon agents (PwC) | 2026 | academic | Partial (empirical, no policy) | **HIGH** for the timing claim |
| H5 | Horvitz, Principles of Mixed-Initiative UIs (LookOut) | 1999 | academic | Conceptual ancestor | **HIGH** (conceptual) |
| M1 | Claude Code auto mode (Anthropic) | 2026 | software | Partial (production per-action gate) | MEDIUM |
| M2 | Magentic-UI (Microsoft Research) action guards + simulated user | 2025 | both | Partial | MEDIUM |
| M3 | Oversight Has a Capacity / Headroom (Turan) | 2026 | both | Partial (escalation policy + fatigue + missed/false-alarm metrics) | MEDIUM |
| M4 | hitloop (GitHub) | 2025/26 | software | Partial (policy-comparison runner) | MEDIUM |
| M5 | SPAR "Benchmarking When to Apply Oversight for Agentic AI" + The Oversight Game (ICML 2026) | 2026 | academic (benchmark in progress) | Yes for the evaluation framework, if released | MEDIUM (rising) |
| M6 | HiL-Bench (Scale AI) | 2026 | academic | Partial (over/under-asking metric) | MEDIUM |
| M7 | AppWorld-UL (ICML 2026) | 2026 | academic | Partial (user-in-the-loop benchmark: clarify/confirm) | MEDIUM |
| M8 | SteerBench-Work | 2026 | academic | Partial (proceed vs hold, over-hold rate) | MEDIUM |
| M9 | Do User-Authored Permission Policies Improve Protection Against AI Agent Overreach? (Yan) | 2026 | academic | Partial (HITL vs auto vs user rules) | MEDIUM |
| M10 | Iqbal & Bailey, Oasis (defer notifications to breakpoints) | 2010 | both | Conceptual ancestor of DEFER | MEDIUM (conceptual) |
| M11 | Sequential Learning-to-Defer (Joshi, Parbhoo, Doshi-Velez) | 2021 | academic | Conceptual ancestor of "defer now vs later" | MEDIUM (conceptual) |
| M12 | Ask4Help (AI2, NeurIPS 2022) | 2022 | both | Partial (learned when-to-ask, user-tunable cost) | MEDIUM-LOW |
| M13 | KnowNo: Robots That Ask for Help (CoRL 2023) | 2023 | both | Partial | MEDIUM-LOW |
| M14 | Towards Automating Data Access Permissions in AI Agents (IEEE S&P 2026) | 2025 | academic | Partial (learns from past decisions) | MEDIUM-LOW |
| M15 | SAGE-Agent / ClarifyBench (UMD/Adobe, ACL Findings 2026) | 2025 | academic | Partial (EVPI + question cost) | MEDIUM-LOW |
| M16 | Cursor 2.4 non-blocking clarifications; OpenAI Codex `send_user_message_async` | 2026 | software | Partial (asynchronous asks) | MEDIUM-LOW for DEFER |
| M17 | LangChain HumanInTheLoopMiddleware | 2025/26 | software | Partial (middleware, rule-based) | MEDIUM-LOW |
| L* | See Section 3.3 (about 25 low-threat items) | | | | LOW |

---

## 3. Detailed findings

### 3.1 HIGH threat

#### H1. Value of Information: A Framework for Human–Agent Communication
1. **Name:** "Value of Information: A Framework for Human–Agent Communication"
2. **Year:** 2026 (arXiv Jan 2026; ACL 2026 long paper, listed as an Oral in the repo README)
3. **Authors:** Yijiang River Dong, Tiancheng Hu, Zheng Hui, Caiqi Zhang, Ivan Vulić, Nigel Collier (Univ. of Cambridge); Andreea Bobu (MIT)
4. **URLs:** https://arxiv.org/abs/2601.06407 · https://arxiv.org/html/2601.06407v1 · code: https://github.com/dong-river/VOI_communication
5. **What it does:** The LLM keeps a belief over latent user intents. Per question it computes VoI(q) = E[value after the answer] − value of acting now, then NetVoI = VoI − c (the communication or cognitive cost). The agent asks the question with the highest positive NetVoI and commits when none is positive. Stakes enter through the terminal utility U(θ,a), for example 10 for medical vs 1 for animal guessing. The paper explicitly frames it as balancing "task risk, query ambiguity, and user effort". Domains: mixed-stakes 20 Questions (animal and medical), flight recommendation (FLIGHTPREF), and ambiguous WebShop. Baselines: No-Question (never ask), Fixed-Round, Adaptive Prompting, and Confidence Thresholding.
6. **Overlap with AgentPause:** This is almost exactly AgentPause's core rule (P(error)×cost(error) − cost(interruption)). It is adaptive vs threshold baselines, has a flight-booking/shopping flavour, and has code.
7. **What AgentPause would do differently:** It is per-action in an executing multi-step trajectory, not a pre-commit question loop. It adds reversibility/recoverability and consequence severity per action, a DEFER action and timing, explanations, and user history/preferences beyond belief priors. It also has a multi-action space (CONTINUE/CLARIFY/ASK_HUMAN/DEFER/BLOCK) and a deterministic simulator. VoI's cost is linear per turn and does not model timing, irreversibility or deferral (verified: "Deferral and irreversibility are not explicitly addressed"; explanations not discussed).
8. **Direct competitor?** **Partial, bordering on yes.** It owns the "EV of asking vs interruption cost for LLM agents" framing. AgentPause must cite it and position itself as an extension to multi-step action gating plus timing.
9. **Type / threat:** both / **HIGH**

#### H2. When Should Users Check? Modeling Confirmation Frequency in Multi-Step Agentic AI Tasks
1. **Name:** "When Should Users Check? Modeling Confirmation Frequency in Multi-Step Agentic AI Tasks"
2. **Year:** arXiv Oct 2025 (v4 Sep 2026); accepted to CHI '26
3. **Authors:** Jieyu Zhou, Aryan Roy, Sneh Gupta, Daniel Weitekamp, Christopher J. MacLellan
4. **URL:** https://arxiv.org/abs/2510.05307 (HTML: https://arxiv.org/html/2510.05307)
5. **What it does:** Treats confirmation as a minimum-time scheduling problem. Inputs are per-step success probability p_a,i (with a suggested Beta-Bernoulli update), t_confirm, t_diagnose and t_redo. Dynamic programming chooses which steps become checkpoints, and the plan is re-solved after an error (receding horizon). A formative study found a Confirmation-Diagnosis-Correction-Redo pattern. In a 48-person within-subjects study across shopping cart, image editing and Overcooked, 81% preferred intermediate confirmation and time fell 13.54%. An appendix compares against random checkpoint placement with probability p_check (a U-shaped curve).
6. **Overlap:** This is directly the "when, within a trajectory, should the human be asked" question. It is decision-theoretic and optimizes cost of interruption against cost of late error discovery (rollback). It includes a policy comparison and a user study, and shares the shopping scenario.
7. **What AgentPause would do differently:** The paper explicitly does not model irreversibility or high-stakes actions (proposed as future mandatory checkpoints), ambiguity, user preferences, or personalization (all listed as future work). It confirms results rather than asking clarification questions, and has no explanations. No code is released. AgentPause would add reversibility-aware DEFER/batching, multiple signals, explanations and an open simulator.
8. **Direct competitor?** **Yes, for the timing/placement contribution.** It is the closest academic precedent to "ask at a better step".
9. **Type / threat:** academic / **HIGH**

#### H3. Modeling Distinct Human Interaction in Web Agents (CowCorpus, PlowPilot)
1. **Name:** "Modeling Distinct Human Interaction in Web Agents"
2. **Year:** 2026 (arXiv Feb 2026, v4 Jul 2026)
3. **Authors:** Faria Huq, Zora Zhiruo Wang, Zhanqiu Guo, Venu Arvind Arangarajan, Tianyue Ou, Frank Xu, Shuyan Zhou, Graham Neubig, Jeffrey P. Bigham (CMU, Duke)
4. **URLs:** https://arxiv.org/abs/2602.17588 · code: https://github.com/oaishi/PlowPilot (MIT, 4 stars) · models: huggingface.co/CowCorpus
5. **What it does:** Introduces the task of modeling human intervention. CowCorpus has 400 real-user web trajectories with more than 4,200 interleaved human and agent actions, and identifies four interaction styles. At each proposed action it does step-wise binary classification p(intervene | observation, proposed action, history incl. human actions) and emits `<ask_user>` or `<agent_continue>`. Its Perfect Timing Score rewards predicting intervention at the true step and penalizes early false positives by temporal distance. Deployed in PlowPilot (Chrome extension), it asks only when intervention is likely; the user study reports a usefulness gain (preliminary, n=4 returning users). Its stated motivation: agents "may proceed past key decisions or ask for unnecessary confirmation."
6. **Overlap:** A learned per-action ask/continue gate, conditioned on the user's past behaviour (user history and style), with timing-aware evaluation and open code. This hits AgentPause's "adaptive" and "past decisions" claims.
7. **What AgentPause would do differently:** It would be explicit, interpretable EV modeling instead of an SFT classifier, with severity/reversibility signals, DEFER/batching, BLOCK, explanations, and a simulator for comparing policies. PlowPilot predicts where humans would intervene; AgentPause decides where they should be asked.
8. **Direct competitor?** **Yes,** on per-step "ask vs continue" for web agents.
9. **Type / threat:** both / **HIGH**

#### H4. Ask Early, Ask Late, Ask Right: When Does Clarification Timing Matter for Long-Horizon Agents?
1. **Name:** as titled
2. **Year:** 2026 (arXiv May 8, 2026)
3. **Authors:** Anmol Gulati, Hariom Gupta, Elias Lumer, Sahil Sen, Vamse Kumar Subbiah (PricewaterhouseCoopers U.S.)
4. **URL:** https://arxiv.org/abs/2605.07937 ("code and data will be publicly released")
5. **What it does:** A forced-injection framework delivers ground-truth clarifications at controlled points in an agent's run. It covers 4 information types (goal, input, constraint, context), 3 benchmarks, 4 frontier models and more than 6,000 runs, plus 300 unscripted sessions. Findings:
   - Goal clarification loses almost all its value after about 10% of execution; input clarification keeps value to about 50%.
   - Clarifying after mid-trajectory is worse than never asking.
   - Timing profiles are task-specific, not model-specific.
   - No frontier model asks inside the optimal window; 52% of sessions over-ask.
   - The authors frame the problem as value of information against interruption cost and explicitly call for "timing-aware clarification policies".
6. **Overlap:** It directly studies re-timing of questions within a trajectory, the empirical basis of AgentPause's DEFER claim. It also shows that "defer too long" is harmful, which constrains how AgentPause's DEFER should behave.
7. **What AgentPause would do differently:** Provide the policy the paper calls for, add irreversibility-anchored batching, and provide explanations. The paper has no policy, no reversibility and no batching.
8. **Direct competitor?** **Partial.** It is empirical and does not compete as a tool, but it pre-empts "nobody has studied timing of agent questions".
9. **Type / threat:** academic / **HIGH** (for the timing-novelty claim)

#### H5. Horvitz, "Principles of Mixed-Initiative User Interfaces" (CHI '99, LookOut)
1. **Name:** Principles of Mixed-Initiative User Interfaces
2. **Year:** 1999
3. **Authors:** Eric Horvitz (Microsoft Research)
4. **URLs:** https://erichorvitz.com/uiact.htm · https://www.erichorvitz.com/chi99horvitz.pdf (text extracted and quoted below)
5. **What it does:** Lists 12 critical factors, including:
   - (2) uncertainty about the user's goals;
   - (3) "consider the costs and benefits of deferring action to a time when action will be less distracting";
   - (4) expected value of action under uncertainty;
   - (5) "employing dialog to resolve key uncertainties … considering the costs of potentially bothering a user needlessly";
   - (7) minimizing the cost of poor guesses about action and timing;
   - (12) continuing to learn by observing.
   LookOut computes threshold probabilities p*(no-action→dialog) and p*(dialog→action) from utilities. Users can specify the utilities or the two thresholds directly, which is user-customized policy. It learns a per-user timing model, a sigmoid of message length, to defer service until the user is ready.
6. **Overlap:** The EV-of-asking idea, the "dialog vs act vs do nothing" action space, user-customized thresholds, deferral to a less distracting time, and learning from user behaviour are all present 27 years earlier.
7. **What AgentPause would do differently:** Multi-step LLM agents taking consequential tool actions; reversibility and severity; batching before irreversible steps; counterfactual explanations; reproducible simulator and metrics.
8. **Direct competitor?** **No (different era and domain), but it is the conceptual ancestor.** Reviewers in HCI will expect it to be cited, and it removes the "novel decision-theoretic formulation" claim.
9. **Type / threat:** academic / **HIGH (conceptual)**

### 3.2 MEDIUM threat

#### M1. Claude Code auto mode (Anthropic)
1. Name: "How we built Claude Code auto mode: a safer way to skip permissions"
2. Year: 2026 (Mar 25, 2026)
3. Authors/company: John Hughes et al., Anthropic
4. URL: https://anthropic.com/engineering/claude-code-auto-mode
5. What it does:
   - A three-tier gate: an allowlist, in-project file writes allowed (reviewable through version control), and everything else sent to a two-stage transcript classifier that decides allow or block.
   - Signals: whether the user actually authorized the action (user intent), real-world impact, and trust boundary / scope. Block rules cover destructive or irreversible actions, exfiltration and shared infrastructure.
   - A denial goes back to the agent so it can find a safer path; escalation to the human happens after 3 consecutive or 20 total denials.
   - Motivated by approval fatigue: users approve 93% of prompts.
   - Reports a false-positive rate of 0.4% and a false-negative rate of 17% on real "overeager" actions.
6. Overlap: A production per-action middleware with BLOCK / CONTINUE / escalate outcomes, reversibility-aware rules, a user-intent signal, and FPR/FNR, which are close to AgentPause's unnecessary-intervention and missed-intervention rates.
7. Difference: Binary classifier rather than EV; no CLARIFY or DEFER timing; no batching; no user-preference learning; no counterfactual timing explanations; closed-source; coding domain only.
8. Direct competitor? **Partial.** It pre-empts "middleware that decides per action" as a product idea, not the research contributions.
9. Type / threat: software (industrial) / **MEDIUM**

#### M2. Magentic-UI (Microsoft Research)
1. Name: "Magentic-UI: Towards Human-in-the-loop Agentic Systems"
2. Year: 2025 (arXiv Jul 30, 2025)
3. Authors: Hussein Mozannar, Gagan Bansal, … Ece Kamar, Saleema Amershi (Microsoft Research)
4. URLs: https://arxiv.org/abs/2507.22358 · https://github.com/microsoft/magentic-ui (MIT, about 10.1k stars)
5. What it does: An open-source human-in-the-loop web/code/file agent with co-planning, co-tasking and action guards. Each action carries a developer label of always, maybe or never irreversible. "Always" goes to the user, "never" auto-runs, and for "maybe" an LLM ActionGuard judge decides whether approval is needed. Users can set how often approvals are requested. Evaluated with an LLM simulated user on GAIA that the agent can ask for help; there is also a qualitative user study.
6. Overlap: Reversibility-based gating, an LLM judge for borderline cases, a user-configurable approval frequency, simulated-user evaluation, and open source with large adoption.
7. Difference: No EV model, no timing or deferral, no comparison of approval policies, no unnecessary/missed metrics (verified: "doesn't compare approval policies or report metrics on unnecessary approvals"), no explanations.
8. Direct competitor? **Partial.** It is the most-adopted open-source HITL agent and AgentPause should consider building on it.
9. Type / threat: both / **MEDIUM**

#### M3. "Oversight Has a Capacity: Calibrating Agent Guards to a Subjective, Fatiguing Human" + Headroom repo
1. Name: as titled; repo "Headroom"
2. Year: 2026 (arXiv Jun 8, 2026)
3. Author: Emre Turan
4. URLs: https://arxiv.org/abs/2606.08919 · https://github.com/turangenesis/headroom (MIT, 2 stars)
5. What it does:
   - A guardian combines rules with an LLM risk score from 0 to 100 and labels each action safe, approval-required or blocked. Risky actions pause via LangGraph `interrupt()`.
   - The escalation threshold is a user-adjustable "calibration dial", with asymmetric costs.
   - Models reviewer fatigue and finds an inverted-U: more escalation can be less safe. A load-aware policy resists flooding attacks.
   - Metrics: missed-danger vs false-alarm rate across thresholds, expected cost, and AURC, on 125 hand-labeled actions. Inter-rater agreement is low (κ = 0.52).
   - Explicitly claims no novel mechanisms; cites FALCON and DeCCaF for fatigue-aware deferral.
6. Overlap: Risk-scored per-action middleware, user-tunable threshold, interruption cost as fatigue, missed vs false-alarm metrics, open source.
7. Difference: No timing, DEFER or batching; no ambiguity/CLARIFY; no explanations; coding domain; tiny.
8. Direct competitor? **Partial**
9. Type / threat: both / **MEDIUM**

#### M4. hitloop
1. Name: hitloop
2. Year: 2025/26 (date not shown; 15 commits)
3. Author: GitHub user ebaenamar
4. URL: https://github.com/ebaenamar/hitloop (MIT, 2 stars)
5. What it does:
   - A HITL library for LangGraph that treats human approval as a measurable "control signal".
   - Policies: AlwaysApprovePolicy (no-oversight baseline), RiskBasedPolicy, AuditPlusEscalatePolicy, TelemetryEscalationPolicy (thresholds on failure, rejection and loop rates), CompositePolicy.
   - `ExperimentRunner` with `create_standard_conditions` ("4 policies × scenarios") and an `ErrorInjector` that supplies ground truth.
   - Metrics: success_rate, approval_rate, error_catch_rate, false_reject_rate, human_latency_ms, cost_proxy.
   - Scenarios: EmailDraftScenario and record_update. A `--simulate` mode runs without an API key.
6. Overlap: An open-source experiment framework that compares intervention policies with error injection and metrics close to missed and unnecessary intervention, including an email scenario. **This is the nearest existing match for AgentPause's evaluation framework (Q5), though it is very small.**
7. Difference: No adaptive EV policy, no clarification, no timing/DEFER, no explanations, few scenarios, no user-study mode.
8. Direct competitor? **Partial.** Same purpose, at toy scale.
9. Type / threat: software / **MEDIUM**

#### M5. SPAR project "Benchmarking When to Apply Oversight for Agentic AI" + "The Oversight Game"
1. Names: SPAR Fall 2026 project; "The Oversight Game: Learning to Cooperatively Balance an AI Agent's Safety and Autonomy"
2. Year: 2026 (project in progress); the paper is arXiv Oct 2025, ICML 2026
3. Authors: William Overman (Stanford) mentoring; paper by William Overman and Mohsen Bayati
4. URLs: https://www.sparai.org/projects/f26/recjmG0Nfo4Ijp61q · https://arxiv.org/abs/2510.26752 · https://proceedings.mlr.press/v306/overman26b.html
5. What it does:
   - The project plans an open-source benchmark asking "when should an agent act autonomously versus defer to a human or overseer?" over coding, tool-use, computer-use and web agents.
   - Every decision point gets a counterfactual safety label (act-would-violate vs deferral-unnecessary) and an oversight cost.
   - Evaluation is on a safety–reward–oversight-budget frontier.
   - Baselines: "always-ask, never-ask, confidence- or entropy-thresholding, LLM-monitor-as-overseer," plus a learned Oversight-Game policy.
   - The Oversight Game models the agent choosing act vs defer and the human choosing trust vs oversee as a Markov (potential) game, with tool-use experiments.
6. Overlap: Nearly identical to AgentPause's policy-comparison framework and its unnecessary/missed labels.
7. Difference: Safety and oversight-budget framing rather than UX timing. No DEFER-to-later or batching, no clarification of intent, no explanations, no user-preference modeling. Not yet released.
8. Direct competitor? **Yes for the evaluation framework, once released.** There is a real risk of being scooped on Q5 in late 2026 or 2027.
9. Type / threat: academic / **MEDIUM (rising)**

#### M6. HiL-Bench: Do Agents Know When to Ask for Help?
1. Name: "HiL-Bench (Human-in-Loop Benchmark): Do Agents Know When to Ask for Help?"
2. Year: 2026 (Apr 2026)
3. Authors: Tu Trinh, Mohamed Elfeki, … Bing Liu (Scale AI)
4. URL: https://arxiv.org/abs/2604.09408
5. What it does: Coding and text-to-SQL tasks with hidden blockers (missing, ambiguous or contradictory information) and an `ask_human()` tool. Ask-F1 is the harmonic mean of question precision and blocker recall, explicitly capturing "the tension between over-asking and silent guessing". RL on a shaped Ask-F1 reward improves a 32B model.
6. Overlap: Evaluation of over-asking vs under-asking (≈ unnecessary vs missed), with a simulated human.
7. Difference: Clarification blockers only; no consequence/reversibility; no timing or deferral; no policy comparison beyond models.
8. Direct competitor? Partial
9. Type / threat: academic / **MEDIUM**

#### M7. AppWorld-UL: Benchmarking Diverse Agent-User Interactions for Tool-Use
1. Name: as titled
2. Year: 2026 (ICML 2026)
3. Authors: Junzhi Chen, Harsh Trivedi, Jane Pan, Michael JQ Zhang, Tejas Srinivasan, Niranjan Balasubramanian, Ashish Sabharwal
4. URL: https://arxiv.org/abs/2607.20536
5. What it does: A user-in-the-loop benchmark of 516 tasks across 9 simulated apps (Amazon, Spotify, …). Tasks are modified to require clarification questions, confirmation requests, or infeasibility notices. The user simulator has defined knowledge boundaries.
6. Overlap: Simulated users plus clarify/confirm decisions in shopping-type tasks.
7. Difference: Benchmarks models rather than policies; no interruption-cost or timing metrics; no DEFER.
8. Direct competitor? Partial (it is a scenario substrate AgentPause could reuse).
9. Type / threat: academic / **MEDIUM**

#### M8. SteerBench-Work: A Benchmark for Agent Steering at Action Boundaries
1. Name: as titled
2. Year: 2026 (Aug 2026)
3. Authors: Oguz Serdar, Cuneyt Mertayak
4. URL: https://arxiv.org/abs/2608.12654 (leaderboard steerbench.com)
5. What it does: 106 incident-anchored scenarios where the agent must proceed or hold for human or policy review, with evidence-reversed pairs. The dominant failure is over-holding authorized work (28.1% of opportunities) vs unsafe allowing (1.0%). Higher capability tends to mean more over-refusal.
6. Overlap: Measures unnecessary-hold vs missed-hold at action boundaries.
7. Difference: No timing, DEFER, clarification, user model or EV; it evaluates models only.
8. Direct competitor? Partial
9. Type / threat: academic / **MEDIUM**

#### M9. Do User-Authored Permission Policies Improve Protection Against AI Agent Overreach?
1. Name: as titled
2. Year: 2026 (Aug 27, 2026)
3. Author: Ting Yan
4. URL: https://arxiv.org/abs/2608.27443
5. What it does: An LLM maps actions to plain-language consequence categories, and users write allow / ask / never rules per category. In a study with N = 113 non-programmers supervising an 18-action simulated day (7 overreach actions), it compares per-action human approval (HITL), automated per-action model review (AUTO) and user-authored policy (POLICY). POLICY reduced prompts (18.0 → 10.9) but blocked less overreach (−20.1 pp vs HITL). 114 of 140 rules were "ask", which the author calls a "preference–commitment gap".
6. Overlap: Compares always-confirm, automated review and user-customized policies in a simulated multi-action scenario with a user study. This closely mirrors AgentPause's "user-customized" condition and user-study mode.
7. Difference: No adaptive EV policy, timing, DEFER, explanations or reversibility modelling.
8. Direct competitor? Partial (it supplies an important negative result about user-customized policies)
9. Type / threat: academic / **MEDIUM**

#### M10. Iqbal & Bailey, "Oasis: A Framework for Linking Notification Delivery to the Perceptual Structure of Goal-Directed Tasks"
1. Name: as titled
2. Year: 2010 (ACM TOCHI)
3. Authors: Shamsi Iqbal, Brian P. Bailey
4. URL: https://www.microsoft.com/en-us/research/?p=161181
5. What it does: Detects task breakpoints on the fly and schedules (defers) notifications to align with them, reducing interruption cost. It is presented as a testbed for scheduling policies.
6. Overlap: "Defer the interruption to a natural breakpoint" is the core of AgentPause's DEFER/batch idea, transplanted from user tasks to agent trajectories.
7. Difference: The human is the one working (not an agent), there are no consequential agent actions, and it is not LLM-based.
8. Direct competitor? No (conceptual ancestor). Must cite.
9. Type / threat: both / **MEDIUM (conceptual)**

#### M11. Interpretable Learning-to-Defer for Sequential Decision-Making (SLTD)
1. Name: as titled
2. Year: 2021 (ICML 2021 Workshop on Interpretable ML in Healthcare, oral)
3. Authors: Shalmali Joshi, Sonali Parbhoo, Finale Doshi-Velez
4. URL: https://icml.cc/virtual/2021/12760
5. What it does: Sequential L2D that "explicitly measures the (expected) value of deferring now versus later" via posterior sampling. It introduces pre-emptive deferral and gives experts a signal about when the model is reliable.
6. Overlap: Formal precedent for "is asking now better than asking later?" within a trajectory.
7. Difference: Medical RL with no LLM, no clarification of intent, no batching, no interruption cost.
8. Direct competitor? No (conceptual). Cite as a formal ancestor of DEFER.
9. Type / threat: academic / **MEDIUM (conceptual)**

#### M12. Ask4Help: Learning to Leverage an Expert for Embodied Tasks
1. Name: as titled
2. Year: 2022 (NeurIPS 2022)
3. Authors: Kunal Pratap Singh, Luca Weihs, Alvaro Herrasti, Jonghyun Choi, Aniruddha Kembhavi, Roozbeh Mottaghi (AI2)
4. URLs: https://ar5iv.labs.arxiv.org/html/2211.09960 · https://github.com/allenai/ask4help
5. What it does: Learns a separate policy for when to request expert help, without changing the base agent. The reward has a failure penalty and per-ask costs. **User preferences on the help/success tradeoff are set at inference via a reward-configuration embedding, with no retraining.**
6. Overlap: A learned when-to-ask policy plus user-customized cost of interruption.
7. Difference: Embodied navigation rather than LLM tool actions; no severity or reversibility; no explanations.
8. Direct competitor? Partial (an older domain)
9. Type / threat: both / **MEDIUM-LOW**

#### M13. KnowNo: Robots That Ask For Help (uncertainty alignment for LLM planners)
1. Name: "Robots That Ask For Help: Uncertainty Alignment for Large Language Model Planners"
2. Year: 2023 (CoRL 2023, PMLR 229)
3. Authors: Allen Z. Ren, Anushri Dixit, … Dorsa Sadigh, Andy Zeng, Anirudha Majumdar (Princeton, Google DeepMind)
4. URL: https://proceedings.mlr.press/v229/ren23a.html
5. What it does: Conformal prediction over LLM-proposed next steps; asks for help when the prediction set has more than one option. It guarantees a user-specified success level with minimal help in multi-step planning.
6. Overlap: A calibrated uncertainty trigger for asking in multi-step LLM planning, with a user-set target.
7. Difference: Uncertainty is the only signal; no consequence/reversibility, interruption cost, timing or explanations.
8. Direct competitor? Partial (it is the standard "confidence-threshold" baseline AgentPause must beat)
9. Type / threat: both / **MEDIUM-LOW**

#### M14. Towards Automating Data Access Permissions in AI Agents
1. Name: as titled
2. Year: arXiv Nov 2025; IEEE S&P 2026
3. Authors: Yuhao Wu, Ke Yang, Franziska Roesner, Tadayoshi Kohno, Ning Zhang, Umar Iqbal
4. URL: https://arxiv.org/abs/2511.17959
5. What it does: A user study of what drives agent permission decisions, followed by an ML model that predicts a user's future permission decisions. Accuracy is 85.1% overall (94.4% on high-confidence predictions) and 66.9% without history; 1 to 4 samples of history add about 10.8%.
6. Overlap: The "user's past decisions" signal used to automate ask vs allow.
7. Difference: Data-access permissions only; no timing, EV, reversibility or explanations.
8. Direct competitor? Partial
9. Type / threat: academic / **MEDIUM-LOW**

#### M15. Structured Uncertainty guided Clarification for LLM Agents (SAGE-Agent, ClarifyBench)
1. Name: as titled
2. Year: arXiv Nov 2025; ACL Findings 2026
3. Authors: Manan Suri, Puneet Mathur, Nedim Lipka, Franck Dernoncourt, Ryan A. Rossi, Dinesh Manocha (UMD, Adobe)
4. URL: https://arxiv.org/abs/2511.08798
5. What it does: Uncertainty over tool parameters, separating the user's specification uncertainty from the model's prediction uncertainty. A POMDP framing with an EVPI score per question and an aspect-based cost. Reports 1.5 to 2.7× fewer questions. ClarifyBench uses a simulated user.
6. Overlap: EV-of-question with cost, in tool-calling agents, separating intent ambiguity from model confidence (two of AgentPause's signals).
7. Difference: Pre-execution clarification only; no consequence/reversibility, timing or DEFER.
8. Direct competitor? Partial
9. Type / threat: academic / **MEDIUM-LOW**

#### M16. Non-blocking or asynchronous agent questions in products (Cursor 2.4; OpenAI Codex)
1. Names: Cursor 2.4 "Clarification questions from the agent"; Codex `send_user_message_async`
2. Year: 2026 (Cursor Jan 22, 2026; Codex reported Aug 19, 2026)
3. Companies: Anysphere (Cursor); OpenAI
4. URLs: https://forum.cursor.com/t/cursor-2-4-clarification-questions-from-the-agent/149406 · https://daily.dev/posts/codex-can-now-keep-coding-while-it-waits-for-your-answer-sffflpz9x (secondary summary of a New Stack article)
5. What they do: The agent asks a clarifying question without blocking and keeps working on independent parts, folding in the answer later. The Codex summary notes there is no checkpoint or rollback if work conflicts with the late answer.
6. Overlap: A production form of "don't stop now; resolve the question later", partially overlapping DEFER.
7. Difference: No decision about when to ask or when to wait; no batching at breakpoints; no gating of irreversible steps on the pending answer. That last piece is exactly AgentPause's opportunity.
8. Direct competitor? Partial
9. Type / threat: software / **MEDIUM-LOW** (for the DEFER claim)

#### M17. LangChain HumanInTheLoopMiddleware
1. Name: HumanInTheLoopMiddleware (LangChain v1)
2. Year: 2025/26
3. Company: LangChain
4. URL: https://docs.langchain.com/oss/python/langchain/human-in-the-loop
5. What it does: Per-tool `interrupt_on` with an optional `when` predicate on arguments. Decisions are approve, edit, reject or respond. "Batched" mode raises one interrupt per model turn containing multiple pending calls.
6. Overlap: Middleware form factor, a conditional gate, and batching of approvals within a turn.
7. Difference: Rule-based only (verified: "docs do not describe an adaptive or learned policy"); no EV, timing or explanations. **AgentPause could ship as a LangChain middleware policy plug-in.**
8. Direct competitor? Partial (it is the obvious integration target)
9. Type / threat: software / **MEDIUM-LOW**

### 3.3 LOW threat (verified; relevant for related work)

| Item | Year | Authors / org | URL | What it does / relevance | Threat |
|---|---|---|---|---|---|
| GateArena: Environment-Enforced Confirmation for Irreversible Agent Actions | 2026 (NeurIPS'26 workshop) | Lan Jiang, Francesco Quinzan, Umang Bhatt | https://neurips.cc/virtual/2026/168290 | Single-use parameter-bound approval warrants for irreversible tools. Shows prompt-only "confirm first" is unreliable (38% / 48% / <1% across backbones). Configurable deviation rate. Relevant to BLOCK and enforcement; no timing. | LOW-MED |
| AgentAbstain: Do LLM Agents Know When Not to Act? | 2026 | Xun Liu … Varun Chandrasekaran | https://arxiv.org/abs/2607.10059 · agentabstain.github.io | 263 paired act/abstain tasks; failure mode "acting irreversibly before recognizing a trigger" (e.g., cancels flight before checking rebooking). | LOW-MED |
| Coding Agents Are Guessing (UnderSpecBench) | 2026 | Zimo Ji … Shing-Chi Cheung (HKUST/Tongji) | https://arxiv.org/abs/2607.02294 | 2,208 variants varying intent clarity, target certainty and blast radius. 55.8–67.8% of runs violate an action boundary; blast-radius cues barely reduce action propensity. Non-action runs are classified as clarification, refusal or deferment. Good evidence for AgentPause's motivation. | LOW |
| The Saturation Trap and the Subjectivity of Intervention Timing | 2026 | Manvendra Modgil | https://arxiv.org/abs/2606.04296 · code: github.com/2025eb1100268-tech/intervention-timing-saturation-trap | Intervention timing on autonomous coding agents. Human annotators agree on when to intervene only slightly above chance (α = 0.047). **Important threat to AgentPause's evaluation validity**: ground-truth "right moment" labels are unreliable. | LOW (novelty) / HIGH (methodology) |
| RegretBench: One More Turn, Less Regret | 2026 | Minh Ngoc Ta … Preslav Nakov | https://arxiv.org/abs/2607.21143 | Regret-based multi-turn clarification policy evaluation (when to stop asking; interaction cost). | LOW |
| When2Call: When (not) to Call Tools | 2025 (NAACL) | Hayley Ross, Ameya S. Mahabaleshwarkar, Yoshi Suhara | https://aclanthology.org/2025.naacl-long.174/ | Tool call vs follow-up question vs "cannot answer". Single-turn decision benchmark. | LOW |
| Ask or Assume? Uncertainty-Aware Clarification-Seeking in Coding Agents | 2026 (EMNLP) | Nicholas Edwards, Sebastian Schuster | https://arxiv.org/abs/2603.26233 | Underspecified SWE-bench; separate underspecification detector; asks more on complex tasks. | LOW |
| Uncertainty-Aware Clarification in LLM Agents with Information Gain | 2026 (ICML) | Mengyi Deng … Wei Wang | https://arxiv.org/abs/2606.03135 | Information-gain reward for clarifier in clarification-enhanced τ-bench. | LOW |
| Ask, Relax, or Act? Actionable Indeterminacy | 2026 | Ang Li … Baoxiang Wang | https://arxiv.org/abs/2610.03102 | Act when an action is shared across all admissible preferences; models over-intervene. Useful "don't ask when unnecessary" principle. | LOW |
| Ask-before-Plan (CEP) | 2024 (EMNLP Findings) | Xuan Zhang, Yang Deng, Zifeng Ren, See-Kiong Ng, Tat-Seng Chua | https://arxiv.org/abs/2406.12639 | Clarify before planning in travel planning. A precedent for "batch questions up front", but static and not timing-aware. | LOW |
| τ-bench | 2024 (ICLR'25) | Shunyu Yao, Noah Shinn, Pedram Razavi, Karthik Narasimhan (Sierra) | https://arxiv.org/abs/2406.12045 | Simulated user + tools + policies in airline and retail. Likely substrate. | LOW |
| Collaborative Gym (Co-Gym) | 2024–26 (ICLR'26) | Yijia Shao, Vinay Samuel, Yucheng Jiang, John Yang, Diyi Yang | https://arxiv.org/abs/2412.15701 | Asynchronous human-agent collaboration framework with simulated and real users, including travel planning. Notes communication failures in 65% of cases. | LOW-MED |
| PRISM: Festina Lente Proactivity | 2026 (ICLR'26) | Yuxuan Fu, Xiaoyu Tan, Teqi Hao, Chen Zhan, Xihe Qiu | https://arxiv.org/abs/2602.01532 · prism-festinalente.github.io | Decision-theoretic gate for proactive help: threshold from asymmetric costs of missed help vs false alarm; counterfactual checks near the boundary (internal, not user-facing). | LOW-MED |
| ProMemAssist | 2025 (UIST'25) | Kevin Pu … Tanya Jonker (Meta) | https://arxiv.org/abs/2507.21378 | Working-memory model feeds a timing predictor that balances value of assistance against cost of interruption. Precedent for a cognitive-load signal. | LOW |
| Sensing What Surveys Miss | 2026 (CHI'26) | Ailin Liu … Francesco Chiossi | https://arxiv.org/abs/2602.00880 | Personalized classifiers with adaptive thresholds time LLM help; aligned timing beats random. | LOW |
| Human-First Pacing and Initiative Auditing for Proactive Conversational Agents | 2026 (NeurIPS'26 workshop) | Tianqi Zhu | https://neurips.cc/virtual/2026/162434 | Estimates "would the user act if we waited" via randomized delays. Counterfactual waiting, but not an explanation feature. | LOW |
| When to Ask a Question: Communication Strategies in GenAI Tools | 2026 | Charlotte Park, Kate Donahue, Manish Raghavan | https://arxiv.org/abs/2605.11240 | Theoretical model of user burden vs preference representation. | LOW |
| Levels of Autonomy for AI Agents | 2025 | K. J. Kevin Feng, David W. McDonald, Amy X. Zhang | https://arxiv.org/abs/2506.12469 | Operator / collaborator / consultant / approver / observer levels. Conceptual framing for AgentPause's policy presets. | LOW |
| Measuring AI agent autonomy in practice | 2026 | Miles McCain … Deep Ganguli (Anthropic) | https://www.anthropic.com/research/measuring-agent-autonomy | Claude stops more as complexity rises. Stop reasons include approval before acting (11%) and clarifying vague requests (13%). Auto-approve use rises with experience (20% → >40%). Recommends against mandating approve-every-action. Empirical motivation. | LOW |
| The Safety Decisions Behind LLM Agents (census) | 2026 (NeurIPS'26 workshop) | B. L. M. de Oliveira et al. | https://neurips.cc/virtual/2026/168217 | "None of the 18 census works on [approval gates] compares a gate against no gate on a safety outcome." Supports AgentPause's evaluation gap. | LOW |
| How Agents Ask for Permission | 2026 (NeurIPS'26 workshop) | Alexandra E. Michael, Franziska Roesner | https://neurips.cc/virtual/2026/168232 | Taxonomy of 21 user-level permission systems plus 5 commercial agents. | LOW |
| AI Agents Push Humans Out of the Loop (position) | 2026 | Margaret Mitchell, Avijit Ghosh, Samir Passi | https://arxiv.org/abs/2608.23642 | Approval fatigue degrades oversight; argues for overseer-centred design. | LOW |
| From Control to Foresight: Simulation-in-the-loop | 2026 (CHI'26 workshop) | Gaole He, Brian Y. Lim | https://arxiv.org/abs/2603.11677 | Per-step approval lacks foresight; preview simulated futures before committing. | LOW |
| Autonomy Reshapes How Personalization Affects Privacy Concerns and Trust | 2025/26 (COLM'26) | Zhiping Zhang, Yi Evie Zhang, Freda Shi, Tianshi Li | https://arxiv.org/abs/2510.04465 | Risk-contingent autonomy (hand control back on privacy-leak detection) raises perceived control. | LOW |
| HumanAgencyBench | 2025 | Benjamin Sturgeon et al. | https://arxiv.org/abs/2509.08494 | Dimensions include "Ask Clarifying Questions" and "Defer Important Decisions". | LOW |
| ST-WebAgentBench | 2024–26 (ICLR'26) | Ido Levy … Segev Shlomov (IBM) | https://arxiv.org/abs/2410.06703 | "User consent" is one of 6 policy dimensions; Completion-under-Policy metric. | LOW |
| GoEX | 2024 | Shishir G. Patil … Ion Stoica (Berkeley) | https://arxiv.org/abs/2404.06921 | Undo and damage confinement; post-facto vs pre-facto validation. Precedent for the reversibility signal. | LOW |
| Causal Delta World Models | 2026 (NeurIPS'26) | Guo Yue et al. | https://neurips.cc/virtual/2026/poster/154820 | Predicts reversibility and irreversible cost per action; abstains on low confidence (no human ask). | LOW |
| HumanLayer | 2024–26 | HumanLayer | https://github.com/humanlayer/humanlayer | Approval and human-as-tool SDK; the repo README now says the code is "pretty much all deprecated". | LOW |
| Optimizing Agent Planning for Security and Autonomy | 2026 | Aashish Kolluri … Santiago Zanella-Béguelin (Microsoft) | https://arxiv.org/abs/2602.11416 | Defines autonomy as the share of consequential actions run without HITL approval while staying secure (AgentDojo, WASP). | LOW |

---

## 4. Novelty-audit answers

### Q1. Is an adaptive multi-signal intervention policy for LLM agents (deciding when to ask) already implemented? By whom?
**Yes, partially, by several groups. No verified system implements the full AgentPause action space and signal set.**
- **Dong et al. 2026 (VoI)** implements an adaptive EV-of-asking policy (ambiguity, stakes, user cost) for LLM agents, with code, and beats confidence-threshold baselines.
- **Huq et al. 2026 (PlowPilot)** implements a learned per-step ask/continue gate conditioned on the user's interaction history, deployed in a browser extension.
- **Anthropic Claude Code auto mode (2026)** runs a production per-action allow/block/escalate classifier that uses user-intent authorization and irreversibility/scope.
- **Magentic-UI (2025)** gates on irreversibility labels plus an LLM judge, with user-set approval frequency.
- **Headroom (2026)** uses an LLM risk score plus a tunable threshold and load-aware escalation.
- **Zhou et al. (CHI'26)** use per-step error probability and rollback cost to place confirmations.
- Older non-LLM precedents with user-tunable costs: Horvitz LookOut (1999) and Ask4Help (2022).

None of these has the explicit 5-way CONTINUE / CLARIFY / ASK_HUMAN / DEFER / BLOCK space, or combines severity, reversibility, interruption cost, cognitive load, preferences and history.

**Confidence:** high that partial implementations exist; medium-high that no single system combines all of these (the field is moving fast and the search budget was exhausted).

### Q2. Is DEFERRING / RE-TIMING a question within a trajectory (asking at a better step, batching at a breakpoint before an irreversible action) already studied for LLM agents?
**The timing question is studied. The specific DEFER-and-batch mechanism was not found.**
- **Studied:**
  - Zhou et al. (CHI'26) optimize where confirmations go in a multi-step agent run with DP, and re-plan after errors.
  - Gulati et al. (May 2026) measure the value of a clarification as a function of trajectory position. Goal questions are worthless after about 10% of execution, and asking after mid-run is worse than never asking. This directly constrains DEFER.
  - Huq et al. (2026) score predicted-intervention timing with the Perfect Timing Score.
- **Conceptual and formal ancestors (non-LLM):**
  - Horvitz 1999: defer action to a less distracting time.
  - Iqbal & Bailey's Oasis (2010): defer interruptions to task breakpoints.
  - Joshi et al. SLTD (2021): value of deferring now vs later.
- **Products:** Cursor 2.4 and Codex ask asynchronously and keep working, but nothing decides when to ask, nor holds irreversible steps until the answer arrives.
- **Not found:** an LLM-agent policy that decides to hold a pending question, keeps executing reversible steps, and batches questions at a natural breakpoint before the first irreversible step. Zhou et al. explicitly list irreversibility as future work.

**Confidence:** medium. Several 2026 papers explicitly call for "timing-aware clarification policies", so this gap may close quickly.

### Q3. Are counterfactual timing explanations ("why not earlier/later") for agent interventions implemented or studied?
**Not found.**
- The closest are:
  - PRISM: internal "counterfactual checks" near the decision boundary, not user-facing explanations.
  - Human-First Pacing (2026 workshop): estimates "would the user act if we waited", a counterfactual about waiting, but not an explanation feature.
  - SLTD (2021): computes the value of deferring now vs later and claims to give experts a reliability signal. This is the nearest formal basis, but it is not a natural-language counterfactual timing explanation.
  - Claude Code auto mode and Salesforce-style escalation patterns explain that something was blocked or escalated, not why at that moment rather than another.
- Targeted searches for "why not earlier", "temporal contrastive explanation" and "explainable deferral" returned only general XRL work (seen in snippets, not verified) and concept-bottleneck deferral, which is not about timing.

**Confidence:** medium-high that this is a genuine gap. Caveat: XRL "why-not" literature exists, so frame the contribution as "counterfactual timing explanations for human-intervention decisions in LLM agents", not as counterfactual explanations in general.

### Q4. Is the combination of signals (uncertainty + intent ambiguity + reversibility + interruption cost + user preferences + history) already published as one model?
**Not as one model. Each component, and several pairs or triples, is published.**

| Paper | Signals covered |
|---|---|
| VoI (Dong et al.) | ambiguity (belief), stakes, interruption cost |
| SAGE-Agent | user-spec uncertainty vs model uncertainty, question cost |
| Zhou et al. | per-step error probability, confirmation cost, rollback/redo cost |
| Claude Code auto mode | user-intent authorization, irreversibility, scope |
| Magentic-UI | irreversibility labels, user approval frequency |
| Wu et al. (S&P'26), Huq et al. | user history |
| Ask4Help, LookOut | user-specified cost preferences |
| ProMemAssist | cognitive load / working memory vs interruption cost |
| Headroom | reviewer fatigue as interruption cost |

Horvitz 1999 is conceptually the closest to the whole bundle: goal uncertainty, utilities, attention and timing, user-set thresholds, learning from the user. But it predates LLM agents and lacks reversibility and severity of tool actions.

AgentPause's claim should therefore be integration novelty, a unified and explainable model, not novelty of any one signal.

**Confidence:** medium-high.

### Q5. Is there an existing open-source framework or testbed whose purpose is comparing intervention policies (never / always / threshold / adaptive) with metrics like unnecessary and missed intervention rates?
**Fragmentary versions exist. No established, multi-scenario, deterministic testbed of AgentPause's scope was found, but one is being built.**
- **hitloop (GitHub, 2 stars):**
  - Policies: AlwaysApprove, RiskBased, Audit+Escalate, Telemetry, Composite.
  - Tooling: ExperimentRunner and ErrorInjector.
  - Metrics: approval_rate, error_catch_rate, false_reject_rate, latency.
  - Scenario: email.
  - This is the nearest match in purpose, at toy scale.
- **Headroom (GitHub, 2 stars):** missed-danger vs false-alarm across escalation thresholds, plus a fatigue simulation.
- **VoI repo:** compares never-ask / fixed / adaptive-prompting / threshold against VoI in 20Q and flight domains.
- **Zhou et al.:** simulate random-placement policies vs DP; no code.
- **SPAR "Benchmarking When to Apply Oversight" (Stanford, Fall 2026, in progress):**
  - Plans exactly always-ask / never-ask / threshold / LLM-monitor / learned baselines.
  - Every decision point gets a counterfactual safety label (act-would-violate vs deferral-unnecessary).
  - The most serious scooping risk for this contribution.
- **Benchmarks that measure over- vs under-asking for models rather than policies:** SteerBench-Work, HiL-Bench (Ask-F1), AppWorld-UL, UnderSpecBench.
- No verified framework combines travel / email / shopping / file / calendar scenarios, deterministic simulation, user-customized policies and a user-study mode.

**Confidence:** medium.

---

## 5. Implications for AgentPause positioning (red-team recommendations)

1. **Drop "first" claims** about decision-theoretic or adaptive when-to-ask. Cite Horvitz 1999, Dong et al. 2026, Zhou et al. CHI'26, Huq et al. 2026 and Gulati et al. 2026 prominently, and use VoI and KnowNo-style confidence thresholds as baselines.
2. **Lead with what is unoccupied:**
   - (a) DEFER as a first-class action: hold a question, continue reversible work, and batch at the breakpoint before the first irreversible step. Use Gulati et al.'s timing curves to bound how long deferral is safe.
   - (b) Counterfactual timing explanations.
   - (c) An open, deterministic, multi-scenario policy-comparison testbed with unnecessary, missed and override metrics.
3. **Ship fast on the testbed.** The SPAR/Stanford benchmark could occupy that space within months. Differentiate on UX timing and interruption cost, not only on safety and oversight budget.
4. **Address measurement validity.** The Saturation Trap paper (α = 0.047 human agreement on intervention timing) and Turan (κ = 0.52 on "risky") show that ground-truth labels are subjective. AgentPause's deterministic simulator with scripted ground truth is an answer to this; say so explicitly.
5. **Use Yan 2026 as a caution.** User-authored allow/ask/never rules reduced prompts but blocked less overreach, and most rules defaulted to "ask". AgentPause's "user-customized" condition should anticipate this.
6. **Integration targets:** LangChain HumanInTheLoopMiddleware (`when` predicate, batched interrupts), the OpenAI/Claude tool-approval hooks, and Magentic-UI action guards.
7. **Before release:** check the "AgentPause" name for collisions. Not done because the search budget was exhausted.

---

## 6. Leads seen only in search snippets (NOT verified, so excluded from the analysis above)
- Nguyen, Bisk, Daumé, "Learning When and What to Ask: a Hierarchical RL Framework" (arXiv 2110.08258; ICML 2022 talk)
- UserBench (Salesforce, arXiv 2507.22034)
- AskBench / rubric-guided RLVR (arXiv 2602.11199, ACL Findings 2026)
- "Learning to Interrupt in Language-based Multi-agent Communication" (arXiv 2604.06452)
- FALCON and DeCCaF (fatigue-aware and cost-sensitive deferral; cited by Headroom)
- OpenAI Operator confirmations, watch mode and takeover mode (the official pages returned 403)
- OpenAI Agents SDK `needs_approval` as a callable (only third-party sources)
- irredux (PyPI page blocked)
- Agentfield risk-score HITL example (page returned 404)
- "Revisable by Design" (arXiv 2604.23283)
- Path-Based Authorization (ICML 2026)
- ClarifyMT-Bench (arXiv 2512.21120)
- Proactive Agent (arXiv 2410.12361)
- Com-Peer timing study
- When2Speak MIR/FIR metrics (arXiv 2605.05626). Its MIR and FIR are named "missed intervention rate" and "false intervention rate", but for multi-party turn-taking, not agent actions; worth checking.

## 7. Query log (WebSearch, about 70 distinct queries)
Topics covered:
- when LLM agents should ask for confirmation; adaptive confirmation for irreversible actions
- structured-uncertainty EVPI; learning when to ask for human help; value of information vs interruption cost
- over- vs under-asking benchmarks; the Dong et al. decision-theoretic framework
- Magentic-UI action guards; Claude Code auto mode classifier; approval fatigue
- proactive interruption timing and cognitive load; Horvitz mixed-initiative (2 queries)
- counterfactual "why not earlier"; batching clarifications before irreversible steps; reversibility-aware agents
- computer-use permission and consent studies
- GitHub: risk-score HITL middleware; "adaptive autonomy"; HumanLayer; irredux; policy-comparison frameworks
- Ask4Help; Learning When and What to Ask; Iqbal & Bailey breakpoints; Oasis
- ST-WebAgentBench consent; τ-bench; asynchronous clarification; Levels of Autonomy
- information-gain clarification; PRISM; Co-Gym; When2Call; simulation-in-the-loop; "AI Agents Push Humans Out of the Loop"
- OpenAI Agents SDK approvals; learned user approval preferences; KnowNo; "Ask, Relax, or Act"; ProMemAssist
- sequential learning-to-defer; HumanAgencyBench; "natural breakpoint" batching; Ask-before-Plan
- unnecessary/missed intervention metrics; explainable escalation; over-confirmation benchmarks; RL ask-or-act with interruption cost
- Operator system card; ToolEmu confirmation; Anthropic measuring agent autonomy; oversight simulators; CHI timing studies
- Oversight Game; AskBench; personalized decision-theoretic intervention; signal-combination taxonomies
- contrastive "why now"; temporal counterfactual XRL; explainable HITL; checkpoint placement optimization; explainable learning-to-defer
- UserBench; position papers; `ask_human` tool RL; confirmation over/under benchmarks; UnderSpecBench
- "AgentPause" name check: blocked, search budget exhausted

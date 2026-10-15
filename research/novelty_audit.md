# Novelty Audit

This audit records, claim by claim, what already exists, how much AgentPause overlaps with it, what
is different, what contribution remains, and how confident we are. It was written after the
first prior-art review ([prior_art.md](prior_art.md), [research_gap.md](research_gap.md),
[literature_notes/E_novelty_red_team.md](literature_notes/E_novelty_red_team.md)) and updated
after a second search during the final audit (October 2026, §3).

**Scope and limits of the search.** We searched arXiv, the ACM DL, ACL Anthology, OpenReview,
Semantic Scholar, GitHub, PyPI, npm, and product documentation for 2023–2026 work, plus older HCI
foundations. Some pages could not be read (OpenAI Operator documentation returned 403). Work
under review, industry systems without public documentation, and non-English work are
under-represented. "We did not find X" means exactly that. It is not evidence that X does not
exist.

**Positioning.** AgentPause is *research infrastructure and an open-source toolkit for studying
adaptive human intervention timing in AI-agent systems*. It does not claim to be the first
adaptive or decision-theoretic approach to deciding when an agent should ask.

---

## 1. Claim-by-claim audit

### C1. Deciding *whether* to involve the human by weighing the value of asking against the cost of interrupting

| | |
|---|---|
| Existing work | Horvitz 1999 (LookOut: expected-utility thresholds for act / ask / do nothing); Dong et al. 2026 (value of information for LLM agents, ACL); Kiyani et al. 2026 (*Strategic Decision Support for AI Agents*: optimal policy is a threshold on support value); Zhou et al. CHI 2026 (decision-theoretic checkpoint placement); KnowNo (Ren et al. 2023, conformal "ask for help"); Zhang et al. 2026 (*Calibration Is Not Control*: intervene on intervention value, not failure risk) |
| Overlap | **High.** AgentPause's per-question value V = p_err·C_err·e − C_int is a variant of this idea |
| Difference | The cost term includes habituation, breakpoints, and load; C_err includes recoverability; the value is computed per question rather than per action |
| Remaining contribution | None as a concept. AgentPause *implements* this as baselines (`myopic_voi`) and as the core of `adaptive` |
| Confidence | High that this is not novel |

### C2. Using reversibility, consequence severity, and uncertainty as signals for approval gating

| | |
|---|---|
| Existing work | Magentic-UI (irreversibility labels + LLM judge); OpenHands `ConfirmRisky`; Claude Code auto mode (transcript classifier); Mastra and LangChain human-in-the-loop middleware; the ask-or-act rule set ([prior_art.md](prior_art.md) §1.29); Chen et al. 2026 (oversight strategies for computer-use agents) |
| Overlap | **High** for individual signals |
| Difference | AgentPause combines uncertainty, intent ambiguity, severity, reversibility, interruption cost, cognitive load, preferences, and history in one inspectable model, and tags every signal with its provenance |
| Remaining contribution | Integration and inspectability, not new signals. Moderate value for researchers, who can ablate signals one at a time (`experiments/configs/ablation.toml`) |
| Confidence | Medium. We found no single system with this whole set, but integration claims are fragile |

### C3. Re-timing a pending question within an executing trajectory: DEFER and batching, bounded by the first irreversible dependent step

| | |
|---|---|
| Existing work | Horvitz 1999 (deferring to less distracting moments); Iqbal & Bailey (breakpoint scheduling of notifications, OASIS); Gulati et al. 2026 (*Ask Early, Ask Late, Ask Right*: clarification value by trajectory position, but no deferral policy); Zhou et al. 2026 (checkpoint placement, time cost only, irreversibility left as future work); When2Talk (Hamid et al. 2026: in-car agent chooses immediate / delayed / silent communication, user study n = 41); Cursor and Codex non-blocking questions (asynchronous, not value-timed); optimal-stopping views of deferral in the uncertainty-quantification literature (2026) |
| Overlap | **Medium-high.** Deferring interruptions to better moments is established in HCI notification research and now in in-car agents (When2Talk) |
| Difference | AgentPause applies deferral to *clarification questions about the agent's assumptions inside an executing LLM-agent trajectory*. Each question has a commitment deadline (the first dependent step with recoverability < 0.5). Deferral is limited by rework cost and by information type: goal and constraint questions are not deferred, following Gulati et al. Questions are batched onto interruptions that are expected anyway (anticipated confirmations) |
| Remaining contribution | A specific, implemented, ablatable mechanism (`AdaptivePolicy(timing=False)` is the myopic ablation). In simulation it reduced interruptions relative to the myopic policy at similar harm. Whether people prefer it is untested |
| Confidence | Medium. When2Talk shows that the general idea of choosing *when* (now / later / never) is being studied for proactive agents. Our specific deadline-bounded mechanism for agent-assumption questions was not found |

### C4. Counterfactual *timing* explanations ("why now, and not earlier / later?") for human-intervention decisions

| | |
|---|---|
| Existing work | Krarup et al. 2021 (contrastive plan explanations, including temporal questions, for planners); Love et al. 2025/2026 (counterfactual explanations of behaviour-tree decisions, robotics); Wachter et al. 2017 (feature counterfactuals); Lim et al. 2009 (why / why-not explanations; why-not formats can reduce understanding); Fox et al. 2017; Körber 2018 and Hardt 2020 (explanations of automation and take-over requests) |
| Overlap | **Medium.** Contrastive temporal questions exist for planning; counterfactual explanations of robot decisions exist |
| Difference | AgentPause answers "why now / why not earlier / why not later" about the decision to *involve the human*. "Earlier" uses what the policy actually computed at earlier steps (logged item values). "Later" uses the same evaluation at planned future steps. The explainer is policy-agnostic: it works for any registered policy, including the baselines |
| Remaining contribution | A user-facing explanation type for intervention timing, implemented and ready for the explanation-condition study (including a placebic control). We have **no evidence yet** that it helps people. H4 and H5 are untested, and Lim et al. warn it might not |
| Confidence | Medium. We found no system that explains the timing of intervention decisions to users, but adjacent work (temporal plan explanations, behaviour-tree counterfactuals) is close |

### C5. An open, deterministic testbed for comparing intervention-timing policies, with ground-truth labels and a study mode

| | |
|---|---|
| Existing work | HiL-Bench (agents asking for help); AppWorld-UL (agent–user interaction); SteerBench-Work (steering at action boundaries); SPAR "Benchmarking When to Apply Oversight for Agentic AI" (in progress, Fall 2026); Headroom (fatiguing-human oversight simulation); hitloop; τ-bench-style user simulators |
| Overlap | **Medium.** Benchmarks for asking and for oversight exist or are being built |
| Difference | AgentPause provides, together: the six-scenario simulator with injected mistakes and wrong assumptions, common-random-number paired comparisons, unnecessary/missed-intervention labels, nine policies including re-implemented baselines from deployed systems, explanations for every policy, a REST API and SDKs, a web UI, and a counterbalanced study mode with licensing-aware questionnaires |
| Remaining contribution | Engineering and research infrastructure. Its value depends on adoption and on whether its scenarios are realistic. The scenarios are scripted and small |
| Confidence | Medium-high that this exact combination is not available as open source today. **High risk of being superseded**, for example when SPAR releases its benchmark |

---

## 2. What the simulated results do and do not support

Held-out seed 314159, 200 episodes per scenario × policy, six scenarios; all results
**simulated**. See `experiments/results/reference/` and the paper draft.

- Supported in simulation:
  - The adaptive policy needs about half the interruptions of always-confirm. The harm difference is not distinguishable from zero.
  - Compared with the myopic expected-value policy, it uses fewer interruptions *and* has slightly lower harm (H1b). This is the clearest evidence for the timing mechanism.
- Not supported, or mixed:
  - A well-tuned **fixed risk threshold** (τ = 0.10) reaches similar harm with fewer interruptions, though with about twice the rework.
  - A simple **rule-based** baseline (always confirm irreversible actions) matches the adaptive policy's harm with slightly fewer interruptions, though with more rework.
  - H1a (lower unnecessary-intervention rate than the default fixed threshold) is not supported.
- Not addressed at all: anything about people (RQ3–RQ5). Not yet evaluated with human participants.

These results limit the strength of any claim about C3. The timing mechanism improves on the
myopic expected-value policy that it extends, but simulation alone does not show that it beats
simple, well-tuned rules.

## 3. Second search (final audit, October 2026)

New or newly checked items, and their effect on the claims:

| Item | Relevance | Effect |
|---|---|---|
| Kiyani, Noorani, Pappas & Hassani 2026, *Strategic Decision Support for AI Agents* (arXiv:2606.12587) | Optimal help-seeking is a threshold on support value, learned online with calibration | Strengthens "C1 is not novel"; a candidate baseline for future work |
| Zhang et al. 2026, *Calibration Is Not Control* (arXiv:2606.21399, revised Oct 2026) | Intervene on intervention utility, not failure risk; handoff to a stronger model, not a human | Supports the value-based framing; no timing, batching, or explanations |
| Piatrashyn et al. 2026, *ReDAct* (arXiv:2604.07036) | Uncertainty-aware deferral to a larger model at the current step | Not human-facing; no overlap with C3 or C4 |
| Hamid, Li & Liang 2026, *When2Talk* (arXiv:2609.12503) | Proactive in-car agent chooses immediate / delayed / silent communication; VR study, n = 41 | Closest new work to C3 in spirit. Different domain (vehicle event notifications, not agent-assumption questions); added to related work |
| Love, Andriella & Alenyà, *Temporal Counterfactual Explanations of Behaviour Tree Decisions* (arXiv:2509.07674, v2 May 2026) | Causal counterfactual answers to contrastive "why" questions about robot decisions | Adjacent to C4. Not about the timing of involving a human; added to related work |
| AgentAbstain (arXiv:2607.10059) | Benchmark for agents knowing when not to act | Related to C5; abstention rather than intervention timing |

None of these items invalidates C3 or C4 as stated above. When2Talk and Love et al. lower our
confidence that the *ideas* are unexplored, which is why the claims are worded as specific
mechanisms in a specific setting.

## 4. Name and packaging

- **PyPI:** the name `agentpause` is **taken** by an unrelated project ("Predictive scheduling
  for autonomous LLM agents: suspend gracefully before rate limits", v0.5.0, July 2026). Our
  distributions are therefore named `agentpause-toolkit`, `agentpause-simulator`, and
  `agentpause-server`. These names were free on 15 October 2026. The *import* name `agentpause`
  is shared with that project, so **do not install both in the same environment**. Before any
  public release, decide whether to rename the import package or the project.
- **npm:** `@agentpause/sdk` and `agentpause` were free on 15 October 2026.
- **Other uses of the phrase:** Buildkite has an `agentPause` GraphQL mutation (CI agents), and
  several agent frameworks have "pause agent" features (OpenHands, CopilotKit, AnchorBrowser).
  These are pause/resume controls, not intervention-timing policies.

## 5. Bottom line

| Claim | Novel as a concept? | Remaining contribution | Confidence |
|---|---|---|---|
| C1 value-of-asking decisions | No | Baseline implementations | High |
| C2 signal set | No (individually) | Integration, provenance, ablation | Medium |
| C3 DEFER and batching to commitment deadlines | Partly established elsewhere (HCI, in-car agents) | Specific mechanism for agent-assumption questions; simulated evidence against the myopic policy only | Medium |
| C4 timing counterfactual explanations | Adjacent work exists | User-facing explanation of intervention timing; untested with people | Medium |
| C5 open testbed and study mode | Benchmarks exist or are in progress | The combined open toolkit | Medium-high, with a high risk of being superseded |

Language to use: "research infrastructure and open-source toolkit", "we implement and compare",
"in simulation", "not yet evaluated with human participants". Language to avoid: "first",
"novel framework", "outperforms", "state of the art", "solves".

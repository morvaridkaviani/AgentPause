# Research Gap

> Status: written after the prior-art review of 2026-10-14 (see [prior_art.md](prior_art.md)),
> re-checked in [novelty_audit.md](novelty_audit.md). All "we found no…" statements are scoped
> to the literature and systems we reviewed. They are not claims that no such work exists.

## 1. The original idea, and why it had to change

The starting hypothesis was:

> *Adaptive intervention timing can preserve or improve human agency while reducing unnecessary
> human interruptions compared with fixed or naive human-in-the-loop strategies.*

The original plan was an "expected value of asking" policy,
`P(error) × cost(error) − cost(interruption)`, compared against never-ask, always-ask, and
fixed-threshold baselines. **The prior-art review showed that this core idea, stated this
generally, is not new:**

| Idea | Already present in |
|---|---|
| Expected-utility choice between *act*, *ask (dialog)*, and *do nothing*, with user-settable thresholds and deferral "to a time when action will be less distracting" | Horvitz, *Principles of Mixed-Initiative User Interfaces*, CHI 1999 (LookOut) |
| Cost of interrupting now vs. cost of delayed delivery, learned per-user interruptibility | Horvitz et al. 2003 (CACM, ICMI); BusyBody (CSCW 2004) |
| Deferring interruptions to task breakpoints | Iqbal & Bailey 2005–2010 (OASIS); Adamczyk & Bailey CHI 2004 |
| Transfer-of-control strategies: when to ask, how long to wait, when to delay a commitment | Scerri, Pynadath & Tambe, JAIR 2002 |
| Net value of information minus a user-effort cost for LLM agents, compared against never-ask / fixed-rounds / confidence-threshold baselines | Dong et al., *Value of Information: A Framework for Human–Agent Communication*, ACL 2026 |
| Decision-theoretic placement of confirmation checkpoints in multi-step agent tasks, with a 48-participant study | Zhou et al., *When Should Users Check?*, CHI 2026 |
| Learned per-step `ask_user` / `continue` prediction from the user's interaction history | Huq et al., *Modeling Distinct Human Interaction in Web Agents* (CowCorpus/PlowPilot), 2026 |
| Empirical value-of-clarification curves over a trajectory ("asking after mid-run is worse than never") | Gulati et al., *Ask Early, Ask Late, Ask Right*, 2026 |
| Production per-action gates (allow / block / escalate) using user-intent authorization and irreversibility | Claude Code auto mode (2026); Codex auto-review (2026); Magentic-UI action guards (2025); Gemini Computer Use `safety_decision` (2025) |
| Swappable `AlwaysConfirm` / `NeverConfirm` / `ConfirmRisky(threshold)` policies | OpenHands (2024); AutoGen `human_input_mode` (2023) |
| Empirical comparison of fixed oversight strategies for computer-use agents, with a call for adaptive oversight | Chen et al., *Comparing Human Oversight Strategies for Computer-Use Agents*, 2026 |

So AgentPause **cannot** claim to introduce adaptive, decision-theoretic "when to ask" for
agents, user-customizable autonomy, or the idea of deferring interruptions. We cite these works
as foundations, and we implement simplified versions of several of them as **baselines**
instead of presenting them as our contribution.

## 2. What remains open

Each statement below is limited to the 250+ papers, products, and repositories we reviewed.

### Gap 1: Re-timing a question *within* an executing agent trajectory, bounded by reversibility

Existing LLM-agent work decides **whether** to interrupt **at the current step**. Examples are
VoI (Dong et al.), PlowPilot (Huq et al.), Magentic-UI, Claude Code auto mode, and OpenHands.
Zhou et al. (CHI 2026) decide **where to place checkpoints** in a plan, but they optimize
completion time only. Their paper explicitly leaves irreversibility, intent ambiguity,
high-stakes actions, and personalization to future work. Gulati et al. measure timing
empirically but propose no policy. Products such as Cursor 2.4 and Codex let agents ask
asynchronously, but nothing decides *when* to ask or *holds* irreversible steps until the
answer arrives.

**Not found in the reviewed work:** an LLM-agent intervention policy that, for each open
question, chooses among:

- **ask now**,
- **defer** (keep doing reversible work, re-time the question to a natural breakpoint, and
  batch it with other pending questions), and
- **never ask** (proceed autonomously),

with the deferral **hard-bounded by the question's commitment point**, that is, the first
dependent action that cannot be undone. The bound should also be **soft-bounded by rework
cost and information-type decay**, consistent with Gulati et al.'s finding that goal and
constraint questions lose their value early.

Conceptual ancestors are Horvitz (1999), Iqbal & Bailey (2010), Scerri et al. (2002), and
Joshi et al.'s sequential learning-to-defer (2021). They predate LLM agents. They also do not
combine deferral with action reversibility as a deadline.

*Confidence that this gap exists:* **medium**. Several 2026 papers explicitly call for
"timing-aware" policies, so we expect this gap to close quickly.

### Gap 2: Counterfactual *timing* explanations for intervention decisions

**The question form is not new, so we do not claim it.**

- Krarup et al. (*Contrastive Explanations of Plans through Model Restrictions*, JAIR 2021)
  formalize question type FQ7: *"Why is action A used at time T, rather than at least some
  time T′ after/before T?"* They answer it by forcing the foil into a planner and comparing
  plans.
- Fox, Long & Magazzeni (*Explainable Planning*, 2017) list *"Why do I (not) need to replan at
  this point?"*.
- Körber, Prasch & Bengler (*Why Do I Have to Drive Now?*, Human Factors 2018) explained the
  *reason* for an automated vehicle's takeover request. That raised perceived understanding
  but not trust.
- Hardt et al. (CHIL 2020) explain *why an alert fires now* by attributing the rise in risk to
  recent inputs.
- Time2Stop (CHI 2024) attaches top-factor explanations to ML-timed interventions.

Agent products give one-line reasons only:

- Gemini Computer Use `safety_decision.explanation`
- Claude Code `permissionDecisionReason`
- Codex risk level and authorization assessment
- MCP elicitation `message`
- Vercel AI SDK approval `reason`

**Not found in the reviewed work:** user-facing explanations of an **AI agent's decision to
involve a human** (ask, clarify, defer, block) that contrast **this step against earlier and
later steps of the same trajectory**. In AgentPause they are computed *faithfully* by
re-evaluating the actual intervention policy on the real trajectory prefix (steps that
happened) and the planned suffix (steps still to come). They are not post-hoc LLM
rationalizations. The study mode is built to evaluate them with users, with a placebic-reason
control. Krarup's FQ7 applies to a planner's own actions under a full PDDL model, and it
models no human-attention cost.

*Confidence:* **medium-high**, with a narrow claim. We cite Krarup et al. FQ7 and Fox et al.
Q5/Q6 as prior art for the question form. The explanation literature also warns that:

- why-not explanations can *lower* understanding (Lim et al. 2009);
- explanations can raise acceptance regardless of correctness (Bansal et al. 2021);
- placebic reasons raise trust as much as real ones (Eiband et al. 2019).

So the benefit of these explanations is a hypothesis to test (H4, H5), not an assumption.

### Gap 3: One inspectable model integrating the signal set

Each signal has been studied, sometimes in pairs or triples:

| Work | Signals |
|---|---|
| VoI | stakes, ambiguity, user effort |
| SAGE-Agent | specification vs. model uncertainty, question cost |
| Zhou et al. | per-step error probability, rollback cost |
| Claude Code auto mode | intent authorization, irreversibility |
| Magentic-UI | irreversibility labels, user-set approval frequency |
| Wu et al. (S&P 2026); Huq et al. | decision history |
| ProMemAssist | working-memory load vs. interruption cost |
| Headroom (Turan 2026) | reviewer fatigue |
| Ask4Help | user-configured cost of asking |

**Not found in the reviewed work:** one model, with every term inspectable, that combines all of:

- agent uncertainty;
- intent ambiguity, attached to explicit **assumptions**;
- severity;
- reversibility/recoverability;
- task structure (breakpoints, commitment points);
- interruption cost driven by cognitive load and **habituation**, where repeated prompts
  reduce the probability that a human catches an error;
- user preference rules;
- decision history, weighted so that rubber-stamped approvals count for less.

The novelty here is **integration, not any single signal**. We claim nothing more.

*Confidence:* **medium-high**.

### Gap 4: An open, deterministic testbed for comparing intervention-timing policies

Fragments exist:

- **hitloop** (2 GitHub stars): four approval policies, error injection, catch and false-reject rates, email scenario.
- **Headroom**: missed-danger vs. false-alarm curves over 125 actions.
- **VoI repo**: never / fixed / threshold baselines.
- **Zhou et al.**: simulation, no code released.
- **Benchmarks that score *models*** on over- vs under-asking: HiL-Bench, SteerBench-Work, AppWorld-UL, UnderSpecBench.

The Stanford SPAR project *Benchmarking When to Apply Oversight for Agentic AI* (Fall 2026,
in progress) plans always / never / threshold / learned baselines with counterfactual safety
labels. It is the strongest risk of being scooped on this point.

**Not found among released artifacts:** a deterministic, multi-scenario simulator with these
properties:

- scripted ground truth: injected errors, wrong assumptions, and their commitment points;
- a parametric simulated user who habituates;
- pluggable policies covering fixed, threshold, myopic expected-value, timing-aware, and user-customized policies;
- formally defined unnecessary, missed, and late-intervention metrics;
- paired (common-random-number) comparisons;
- a user-study mode that runs the *same* scenarios with real participants.

*Confidence:* **medium**. The window is open now but may close soon.

## 3. Revised contribution

AgentPause is positioned as:

> **A research infrastructure and open-source toolkit for studying adaptive human intervention
> timing in AI-agent systems.**

Its contributions, in decreasing order of how defensible we believe they are:

1. **A testbed (Gap 4).** The testbed is research software: simulator, policies, metrics, experiment runner, study mode, and dashboard. It lets other researchers reproduce and extend comparisons. Its baseline policies are simplified re-implementations of designs from prior work:
   - never-ask, after AutoGen `NEVER`;
   - always-confirm, after OpenHands `AlwaysConfirm`;
   - a fixed risk threshold, after OpenHands `ConfirmRisky` and Mastra's classifier ≥ τ;
   - a reversibility × confidence rule set, after Magentic-UI and the *ask-or-act* rules;
   - a confidence threshold, after KnowNo and Warp;
   - a myopic expected-value policy, in the spirit of Horvitz 1999 and Dong et al. 2026.

   They are labelled as re-implementations, not faithful reproductions.
2. **Counterfactual timing explanations (Gap 2).** These are policy-agnostic: they work for any policy that implements the `InterventionPolicy` interface.
3. **A trajectory-aware intervention-timing model (Gaps 1 and 3).** Its parts:
   - an expected-value core adapted from Horvitz 1999;
   - assumptions with **commitment points**;
   - **DEFER with batching at breakpoints**;
   - deferral limited by rework cost and information-type decay;
   - habituation-aware asking effectiveness;
   - history weighting that discounts approvals given under fatigue.

## 4. What we explicitly do *not* claim

- We do **not** claim to be the first adaptive or decision-theoretic "when to ask" system.
- We do **not** claim that our parameter values (interruption-cost weights, habituation rates,
  category severities) are empirically calibrated. They are documented, configurable
  priors. Calibrating them requires human data.
- We do **not** claim the simulator's ground truth captures what real users consider
  "necessary". Human annotators agree poorly on when to intervene: Krippendorff's α = 0.047 in
  Modgil 2026, and κ = 0.52 on "risky" in Turan 2026. Scripted ground truth makes comparisons
  reproducible, but it encodes the scenario authors' judgement. The study mode exists to
  test whether simulated conclusions hold for people.
- We do **not** claim that simulation results support RQ3–RQ5. No human-participant study
  has been run yet.

## 5. Risks to the claimed gap

| Risk | Mitigation |
|---|---|
| SPAR/Stanford releases its oversight benchmark | Our differentiators are UX timing (DEFER/batching), clarification vs. approval, explanations, and the user-study mode, not safety labels alone. Integrate their tasks if released |
| A timing-aware LLM clarification policy appears (Gulati et al. explicitly invite one) | Our policy also covers approval gating and reversibility deadlines. Run their forced-injection protocol as an external validity check |
| The user-customized condition underperforms (Yan 2026: 114/140 user rules were "ask") | Treat this as a research question (RQ6), not a selling point |
| Simulator built to favour the proposed policy | Pre-registered metrics; sensitivity analysis across simulator parameters; report scenarios where timing gives no benefit; release all code and seeds |

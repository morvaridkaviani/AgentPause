# AgentPause: Research Infrastructure for Studying When AI Agents Should Pause and Ask

*Draft, October 2026. Target: CHI / UIST / IUI (systems + simulation paper), with a follow-up human
study. All quantitative results in this draft are **simulated**. The human study has **not** been
run: every human-study section is marked **Not yet evaluated with human participants**.*

---

## Abstract

AI agents that act for people must decide, at every step, whether to continue on their own or to
involve the person. Asking too often trains people to approve without reading. Asking too rarely
lets mistakes through, and asking at the wrong moment either interrupts people mid-task or comes
after an irreversible action. Prior work has established decision-theoretic rules for *whether* to
ask, and recent studies show that *when* a question is asked changes its value. Evaluation,
however, remains fragmented across systems, metrics, and domains.

We present AgentPause, an open-source research toolkit for studying adaptive human intervention
timing. It has five parts:

1. a decision engine with nine intervention policies, including re-implemented baselines from deployed agent systems;
2. a trajectory-aware timing policy that defers and batches clarification questions up to the first irreversible step that depends on them;
3. counterfactual timing explanations that answer "why now, and not earlier or later?" for any policy;
4. a deterministic simulator with six scripted scenarios, injected mistakes and wrong assumptions, ground-truth labels, and a habituating simulated user;
5. a study mode with counterbalanced conditions and licensing-aware questionnaires, exposed through a REST API, SDKs, and a web interface.

In simulation (1,200 paired episodes per policy on held-out seeds), the timing policy used 53% fewer interruptions than always-confirm, with no detectable difference in harm. It also needed fewer interruptions than the myopic value-of-asking policy it extends, with slightly lower harm. However, simple well-tuned rules (a reversibility rule and a low fixed risk threshold) reached similar harm with similar or fewer interruptions, at the cost of more rework. We report these results as properties of a simulator whose assumptions we vary, not as evidence about people. The toolkit's purpose is to make such comparisons reproducible and to run the human studies that simulation cannot replace. Not yet evaluated with human participants.

---

## 1. Introduction

Autonomous agents now book travel, send email, edit files, and make purchases. Every deployed
agent embeds a policy for involving its user, usually a fixed one:

- **ask before everything:** OpenHands' always-confirm mode;
- **ask above a risk score:** OpenHands' "confirm risky" mode and classifier thresholds;
- **ask for irreversible actions:** Magentic-UI's action guards;
- **let a classifier decide:** Claude Code's auto mode;
- **never ask:** AutoGen's `NEVER`.

Each choice trades interruption against oversight in a way that is rarely measured and seldom
explained to users. The trade-off is well documented. Users habituate to warnings and approve most
prompts (Akhawe & Felt 2013; Anderson, Vance et al. 2015–18). Interruptions in the middle of a task
cost more than interruptions at task boundaries (Iqbal & Bailey; Bailey & Konstan 2006). In a
recent comparison of oversight strategies for computer-use agents, 56% of failures involved a
timing mismatch (Chen et al. 2026).

The idea that a system should weigh the value of asking against the cost of interrupting is not
new. Horvitz's LookOut (1999) chose between acting, asking, and doing nothing by expected utility,
and deferred actions to less distracting moments. Recent work brings this to LLM agents:

- value-of-information rules (Dong et al. 2026);
- dynamic-programming placement of confirmation checkpoints (Zhou et al. 2026);
- learned predictors of when a user would intervene (Huq et al. 2026);
- empirical measurements showing that the value of a clarification depends on where in the trajectory it is asked (Gulati et al. 2026).

What is missing is less a new rule than **shared infrastructure**: a common set of policies,
scenarios with ground truth, metrics that separate unnecessary from missed interventions, and a
study protocol, so that claims about intervention timing can be compared and reproduced.

AgentPause provides this infrastructure and uses it to examine one specific timing mechanism. We
contribute:

1. **An open, deterministic testbed** for intervention policies. It includes nine policies, six scenarios with injected errors and scripted ground truth, paired comparisons with common random numbers, an experiment runner, and a counterbalanced study mode. The baselines re-implement designs from deployed systems and prior work.
2. **Counterfactual timing explanations** for human-intervention decisions. They answer "why now?", "why not earlier?", and "why not later?" from what the policy actually computed. They work for any policy and are designed for an explanation study with a placebic control.
3. **A trajectory-aware timing policy.** It keeps a clarification question pending while the agent continues on reversible steps. It asks at a natural breakpoint, or batches the question with an interruption that is expected anyway, and never later than the first irreversible step that depends on the question.

We also report what the testbed shows about this policy in simulation, including where it does
*not* beat simpler rules.

## 2. Related work

**Mixed-initiative interaction and interruption.** Horvitz (1999) formalized acting versus asking
under uncertainty with expected utility, user-adjustable thresholds, and attention-aware
deferral. Work on attention-sensitive alerting and breakpoints showed that the cost of
interruption depends on task structure:

- Adamczyk & Bailey, *If not now, when?*;
- Iqbal & Bailey's OASIS, which holds notifications until breakpoints.

Adjustable-autonomy research studied transfer-of-control strategies with deadlines (Scerri et
al.). When2Talk (Hamid et al. 2026) recently applied immediate, delayed, or silent communication to
a proactive in-car agent. AgentPause applies these ideas to clarification and approval questions
inside an executing agent trajectory.

**When LLM agents should ask.** Value-of-information approaches compare the expected gain of a
question with its cost (Dong et al. 2026; Kiyani et al. 2026). Zhou et al. (2026) place
confirmation checkpoints in multi-step tasks to minimize time. They leave irreversibility and
ambiguity to future work. Gulati et al. (2026) show that goal clarifications lose value quickly
and that late questions can be worse than none. KnowNo, Ask4Help, SAGE-Agent, and HiL-Bench study
asking for help or clarification. Learning-to-defer and abstention work (SLTD, ReDAct,
AgentAbstain) decides when to hand a decision to an expert or a stronger model. Zhang et al.
(2026) argue that oversight should be driven by the value of intervening rather than by
calibrated failure risk. Our myopic baseline belongs to this family. Our timing policy adds
deferral bounded by commitment points.

**Deployed approval gates.** Production agents expose approval policies:

- OpenHands: always, never, or risky;
- Magentic-UI: irreversibility labels and an LLM judge;
- Claude Code: permission rules, hooks, and a transcript classifier;
- OpenAI Codex: auto-review;
- Gemini Computer Use: `safety_decision`;
- framework middleware in LangChain and Mastra.

User-authored permission policies are often conservative (Yan 2026). We re-implement simplified
versions of these designs as baselines and label them as such.

**Explanations.** Contrastive and counterfactual explanations (Wachter et al. 2017) include
temporal contrastive questions for planners (Krarup et al. 2021; Fox et al.) and counterfactual
explanations of behaviour-tree decisions (Love et al.). Why-not explanations can reduce
understanding (Lim et al. 2009). Content-free "placebic" reasons can raise trust as much as real
ones (Eiband et al. 2019). Appropriate reliance should be measured, not only satisfaction
(Schemmer et al. 2023). We therefore lead with "why now", put "why not earlier/later" second, and
include a placebic control condition.

**Testbeds.** Several benchmarks touch asking and oversight: HiL-Bench, AppWorld-UL,
SteerBench-Work, Headroom, hitloop, and an in-progress SPAR benchmark. The full review is in
`research/prior_art.md`, and claim-by-claim overlap is in `research/novelty_audit.md`.

## 3. The AgentPause toolkit

### 3.1 Interface

An agent sends AgentPause a proposed action. This is metadata only, never content:

- action name, consequence category, severity, reversibility;
- agent confidence and intent confidence;
- task progress, breakpoint flag, cognitive load;
- declared assumptions, the remaining plan, and dependencies.

Every signal carries a **provenance**: agent-provided, user-provided, estimated, inferred,
simulated, or default. Missing signals fall back to documented category priors and are flagged in
the explanation. AgentPause returns one of five decisions:

| Decision | Meaning |
|---|---|
| CONTINUE | act without involving the human |
| DEFER | act now; a pending question is scheduled for a later step |
| CLARIFY | ask about an assumption before acting |
| ASK_HUMAN | approve, edit, or reject this action |
| BLOCK | stop and hand control back |

Each decision comes with reason codes, a template explanation, factor attributions,
counterfactuals, a timing explanation, and the model terms. The same engine runs in-process
(Python SDK), over a REST API (FastAPI, OpenAPI), from TypeScript, and as a Claude Code
`PreToolUse` hook.

### 3.2 Policies

| Policy | Rule | Source of the design |
|---|---|---|
| `full_autonomy` | never ask (only hard constraints block) | AutoGen `NEVER` |
| `always_confirm` | ask before every non-read-only action | OpenHands always-confirm |
| `fixed_threshold` | ask if consequence risk ≥ τ (default 0.35) | OpenHands risky, classifier ≥ τ |
| `confidence_threshold` | ask if agent or intent confidence < 0.8 | KnowNo-style thresholds |
| `rule_based` | reversibility × confidence rules | Magentic-UI, ask-or-act |
| `myopic_voi` | ask now if expected benefit > cost, each step on its own | Horvitz 1999; Dong et al. 2026 (simplified) |
| `adaptive` | expected value per question, with timing (§4) | this work |
| `user_customized` | adaptive plus user rules and profiles | user-authored policies (Yan 2026) |
| `learned` | logistic model on 11 features (experimental) | trained on simulator labels |

All policies share the hard constraints: an action that requires human input (for example a
payment credential) always involves the human. All parameters are documented priors, not
calibrated estimates (`GET /api/v1/model`).

## 4. A trajectory-aware timing policy

### 4.1 Value of a question

For a question *q* that could be asked at step *t*, AgentPause estimates

  **V(q, t) = p_err · C_err · e(t) − C_int(t) − RW(q, now → t)**

The terms are:

- *p_err*: the probability that proceeding is wrong, combining agent error and intent mismatch, assumed independent.
- *C_err = sev · [(1 − r) + r · ρ]*: the harm if wrong. Here *r* is recoverability and *ρ* the relative cost of undoing a recoverable mistake.
- *e(t) = e₀ · (1 − effect · h)*: the probability that the person catches the problem when asked. The habituation term is *h = 1 − exp(−λ · recent interruptions)*.
- *C_int(t) = c₀ · pref · (1 + γ · load) · m_breakpoint · (1 + κ · h) · m_kind*: the cost of interrupting. It rises with load and mid-task, falls at breakpoints, and is scaled by the user's profile.
- *RW*: the expected rework from continuing on a possibly wrong assumption until *t*.

The default interruption cost is *c₀ = 0.02* harm units. It was chosen on development seeds by sweeping the harm–interruption frontier (§6.2). The decision score shown to users is *B / (B + C)*.

### 4.2 Timing

At each step the policy considers two kinds of question:

- **the approval question** for the current action, whose deadline is now;
- **one clarification per open assumption.** Its deadline is the assumption's *commitment point*: the first planned step that depends on it and has recoverability below 0.5.

Each clarification is evaluated at several candidate moments:

- now;
- the next breakpoints;
- steps where a confirmation is likely to be requested anyway;
- the deadline.

The policy then does one of the following:

- If some question's best moment is now and its value is positive, the policy interrupts. It adds every other question whose *marginal* value is positive (batching at marginal cost 0.35·c₀).
- If a question is worth asking but not yet, the decision is **DEFER**, and the question is scheduled.
- Goal and constraint questions are not deferred, because their value decays early in the trajectory (Gulati et al. 2026). Only input and context questions are.
- Catastrophic actions are blocked: severity ≥ 0.9, recoverability ≤ 0.15, and p_err ≥ 0.6.

Setting `timing=False` turns off DEFER, lookahead, and anticipated confirmations. It gives the
**myopic** ablation, which is identical to `myopic_voi`. Comparing the two isolates the timing
contribution.

## 5. Explanations

Every decision carries five kinds of explanation:

1. **Reason codes and template narrative.** Deterministic templates map each reason code to a phrase. No language model is involved, so every clause is traceable to a code the policy emitted.
2. **Factor attribution.** The score change when one signal is set to a low-risk reference value (occlusion). Interactions are not decomposed.
3. **Feature counterfactuals.** Minimal single-signal changes that flip the decision. Each is verified by re-running the policy.
4. **Timing counterfactuals.**
   - *Why not earlier?* Read from the session history: what the policy computed for this question at earlier steps, or the fact that the question did not exist yet.
   - *Why not later?* The same evaluation at the planned future steps, with their feasibility relative to the deadline.

   Because the explainer treats the policy as a black box, timing explanations also work for baselines, for example to explain why always-confirm asked at a moment when nothing was at stake. Only policies that plan ahead (the adaptive family) can name specific later moments in "why not later?".
5. **Stability.** The share of 16 small, seeded perturbations of the uncertain signals under which the decision stays the same.

In the study, explanation type is a between-subjects factor with four levels: none, placebic
reason, factors, and factors + timing (§7).

## 6. Simulation study

*All results in this section are simulated. Not yet evaluated with human participants.*

### 6.1 Method

**Scenarios.** There are six scripted tasks, with 7–8 steps each: travel booking, email reply,
shopping, file clean-up, calendar scheduling, and a research assistant. Each step has the
following metadata:

- consequence category, severity, recoverability;
- whether it is a breakpoint;
- which assumptions it depends on;
- a plain-language preview for the intervention card.

Each episode injects two kinds of error, deterministically from the seed:

- **mistakes**: a wrong action that becomes visible at one step and causes harm at a later step unless caught;
- **wrong assumptions**: the agent's interpretation differs from the user's real intent, which is stated in the scenario brief.

**Agent signals.** Agent confidence drops when a mistake is present (calibration 0.7) and
partially when an upstream mistake propagates (0.35), with noise. Intent confidence reflects
assumption ambiguity.

**Simulated user.** The simulated user catches a shown error with a probability that falls with
recent interruptions (habituation rate 0.12). It answers clarifications with the true intent and
takes time to respond. This user shares functional forms with the policy's model, a circularity
we address with sensitivity analyses (§6.5).

**Labels and metrics.** An intervention is *necessary* if it showed a pending error. A *missed
intervention* is an error that caused harm without ever being shown. *Harm* is the sum of the
costs of the errors that caused harm. *Rework* counts executed steps redone after a late
correction. Definitions are in `research/metrics.md`.

**Protocol.** Policy parameters were developed on seed 20261014. All results below use held-out
seed 314159 with 200 episodes per scenario × policy (1,200 per policy). Every policy faces
identical episodes (common random numbers), so comparisons are paired. Intervals are 95%
bootstrap intervals. The full pipeline reproduces with one command
(`python experiments/reproduce_all.py`), and every result carries a hash.

### 6.2 Results: policy comparison

**Table 1.** Means per episode or pooled rates, held-out seeds. *SIMULATED.*

| Policy | Interruptions | Unnecessary rate | Missed rate | Harm | Rework steps | Task time (s) |
|---|---|---|---|---|---|---|
| Full autonomy | 0.17 | 0.00 | 1.00 | 0.377 | 0.00 | 47.7 |
| Fixed threshold (τ = 0.35) | 1.02 | 0.42 | 0.46 | 0.104 | 0.85 | 66.5 |
| Learned (experimental) | 2.03 | 0.50 | 0.13 | 0.059 | 0.21 | 69.0 |
| Rule-based | 2.37 | 0.59 | 0.08 | 0.038 | 0.81 | 79.5 |
| Confidence threshold | 2.56 | 0.60 | 0.13 | 0.057 | 0.05 | 71.1 |
| **Adaptive (AgentPause)** | **2.63** | **0.63** | **0.12** | **0.038** | **0.44** | **75.7** |
| User-customized (balanced profile) | 2.98 | 0.67 | 0.12 | 0.040 | 0.44 | 78.9 |
| Myopic value of asking | 3.26 | 0.69 | 0.15 | 0.048 | 0.10 | 77.8 |
| Always confirm | 5.59 | 0.80 | 0.03 | 0.047 | 0.39 | 105.5 |

**Table 2.** Paired differences, adaptive − baseline (95% bootstrap CI over 1,200 pairs).
Missed interventions and unnecessary interventions are counts per episode. *SIMULATED.*

| Baseline | Interruptions | Harm | Missed interventions | Rework steps |
|---|---|---|---|---|
| Always confirm | −2.96 [−3.05, −2.88] | −0.009 [−0.021, +0.003] | +0.085 [+0.068, +0.102] | +0.05 [−0.00, +0.10] |
| Myopic value of asking | −0.63 [−0.69, −0.57] | −0.009 [−0.016, −0.002] | −0.036 [−0.047, −0.027] | +0.33 [+0.30, +0.38] |
| Rule-based | +0.26 [+0.21, +0.31] | +0.000 [−0.010, +0.011] | +0.033 [+0.014, +0.051] | −0.37 [−0.44, −0.31] |
| Fixed threshold (τ = 0.35) | +1.61 [+1.55, +1.67] | −0.066 [−0.077, −0.054] | −0.351 [−0.391, −0.312] | −0.42 [−0.48, −0.35] |
| Confidence threshold | +0.07 [+0.02, +0.12] | −0.018 [−0.029, −0.008] | −0.016 [−0.038, +0.006] | +0.38 [+0.34, +0.43] |

Observations:

- Against always-confirm, the adaptive policy removed about 53% of interruptions. The harm difference was not distinguishable from zero. It missed slightly more errors: about one more missed error every 12 episodes.
- Against the myopic policy it extends (H1b), it used fewer interruptions and had slightly lower harm. This is the clearest simulated evidence that timing matters *in this simulator*. The cost is more rework, because deferring a question means some steps run on assumptions that later turn out to be wrong.
- H1a was supported against always-confirm and **not** against the default fixed threshold. That threshold asks rarely and therefore has a low unnecessary-interruption rate, but it misses 46% of errors.

**Frontiers.** Single operating points can mislead, so we swept each parameterized policy
(Figure 1: `experiments/figures/reference/frontier_harm.png`). The adaptive frontier lies below
or on the myopic frontier across the range. However:

- **A low fixed threshold** (τ = 0.10) reaches harm comparable to adaptive (0.041 vs 0.038) with fewer interruptions (1.98 vs 2.63), but about twice the rework (0.95 vs 0.44).
- **The rule-based policy** sits close to the adaptive frontier.

In these scenarios, consequence category and reversibility carry most of the information. A
simple rule that uses them is a strong baseline. We consider this a substantive finding, not a
nuisance: the timing mechanism's simulated advantage is mainly fewer interruptions than the
policy it extends, and less rework than simple rules.

### 6.3 Results: where and how the policies interrupt

The adaptive policy deferred on 21% of steps, an average of 1.8 DEFER decisions per episode
(Figure 2: `decision_mix.png`). 54% of its interruptions combined several questions, with 1.66
questions per interruption. For comparison:

| Policy | Batched interruptions | Questions per interruption |
|---|---|---|
| Adaptive | 54% | 1.66 |
| Always confirm | 48% | 1.60 |
| Myopic | 28% | 1.28 |
| Rule-based | 66% | 2.14 |

Rule-based and always-confirm batch "for free": they ask at irreversible steps, where the pending
assumptions are due anyway.

The adaptive policy rarely interrupts in the 25–50% band of task progress and concentrates
interruptions near the end, before commitments (Figure 3: `timing.png`). The myopic policy instead
asks early: about 1.0 interruptions per episode in the first quarter, against 0.5 for adaptive.

### 6.4 Signal ablation (RQ2)

Removing one signal at a time (Figure 4: `ablation.png`) gave these results:

- **Intent confidence.** Removing it was catastrophic: harm rose from 0.038 to 0.310 and the missed rate from 0.12 to 0.79. Most injected errors are wrong assumptions, and without intent confidence the policy cannot see them.
- **The plan.** Removing it cut interruptions by 0.85 but doubled rework (0.44 → 0.94). Without lookahead the policy cannot schedule clarifications before their commitment points, so it asks too late.
- **The breakpoint signal.** Removing it lowered interruptions but raised missed interventions.
- **Severity and recoverability.** Removing either had little effect, because the category priors already encode them in these scenarios.
- **Session history.** Removing it had no measurable effect at this episode length.

H2 predicted that reversibility and intent would matter most. This was half confirmed (intent).
Reversibility mattered less than predicted because category priors stand in for it.

### 6.5 Sensitivity to simulator assumptions

We varied the simulated world while keeping policies fixed (Figure 5: `sensitivity.png`).

- **Uncalibrated agent.** When agent confidence carried no information about mistakes, the adaptive policy's harm rose from 0.038 to 0.055 and its missed rate from 0.11 to 0.19. Always-confirm (0.048) and rule-based (0.046) were unaffected. Expected-value policies depend on calibrated confidence, and real LLM confidence is often miscalibrated.
- **Agent unaware of upstream mistakes.** Similar but smaller degradation.
- **Fast-habituating user.** Always-confirm's harm rose most (0.048 → 0.077). Adaptive went from 0.038 to 0.055.
- **Non-habituating user.** Always-confirm had the lowest harm (0.022). The penalty for asking often disappears when people never habituate.
- **Careless user.** All policies converged (≈ 0.10), because shown errors are approved anyway.
- **Better-calibrated agent.** Confidence fell further on mistakes (0.82 vs 0.85 on error steps), but no adaptive decision changed. The decision is dominated by consequence and intent signals at these margins.

The ranking of policies therefore depends on assumptions about people that only a human study
can settle.

### 6.6 Learned policy (experimental)

A logistic model on 11 features was trained on simulator labels: whether an intervention was
needed at the step (5,400 training rows on separate seeds). It reached a test AUC of 0.78, and
0.68–0.86 when one scenario was held out. As a policy it interrupted less (2.03) at higher harm
(0.059). It learns the simulator's labelling rule, not human preferences. It is included as an
example of plugging a learned component into the testbed, not as a contribution.

## 7. Planned human study

*Not yet evaluated with human participants.* The protocol is implemented in the study mode and
documented in `docs/experiments.md`. Pre-registration is planned before data collection.

**Design.** The study has two factors:

- **Policy, within subjects.** Four core policies: full autonomy, always confirm, fixed threshold, adaptive. Order is counterbalanced with a balanced (Williams) Latin square, and scenarios are rotated across blocks. There is a practice block first.
- **Explanation type, between subjects.** Four levels: none, placebic reason, factors, factors + timing.

Participants supervise a scripted (not LLM) agent. They see a private brief describing their real
intent and check the agent's proposals against it. Problematic actions are injected
deterministically, so catch rates are measurable.

**Measures.**

- Behavioural: catch rate of injected errors, false rejections, response time, overrides, acceptance.
- Appropriate reliance: acceptance of correct proposals and override of incorrect ones, by explanation condition (RAIR/RSR after Schemmer et al. 2023).
- Questionnaires: NASA-TLX raw; trust (Körber 2018 or Jian et al. 2000, items supplied by the researcher under their licence); pilot items for perceived control, interruption annoyance, and timing appropriateness (marked not validated); a scored timing-comprehension check.

**Hypotheses.** H1c, H3a, H3b, H4, H5, and H6 (`research/research_questions.md`).

**Power.** Not computed yet. The smallest effect size of interest (and the non-inferiority
margin for H1c) will be fixed on substantive grounds before data collection; a small pilot
(n ≈ 12) estimates variances. `docs/experiments.md` describes the procedure.

**Ethics.** All actions are simulated, participants are identified only by random codes, there is
no free-text personal data, and ethics approval is required before running.

## 8. Discussion

**What the testbed changed in our own claims.** We set out to build an adaptive policy and
expected it to dominate the baselines. The paired, frontier-based evaluation showed something
different. Timing beats the myopic expected-value policy, but a reversibility rule is hard to
beat on harm per interruption in scripted scenarios where the consequence category is known.
This is the kind of result a shared testbed should surface early. It also suggests where adaptive
timing should matter more:

- when consequence metadata is uncertain or must be estimated;
- when tasks are longer and assumptions are revealed gradually;
- when interruption cost varies strongly with the user's situation.

The current scenarios capture these only weakly.

**Simulators share assumptions with policies.** The simulated user habituates in the way the
policy's model assumes, and the agent's confidence is calibrated in the way the policy expects. We
mitigate this with sensitivity analyses in which the world departs from the model, and these
change the conclusions (§6.5). Simulation can rank designs under stated assumptions. It cannot
tell us what people want.

**Explaining timing.** Timing explanations make a policy's behaviour inspectable. Developers can
check whether "why not earlier?" is sensible, and whether a baseline asked at a moment when
nothing was at stake. Whether they help users calibrate reliance, or merely raise trust as
placebic reasons do, is the central question for the human study.

## 9. Limitations

- **Simulation only.** No human data. Not yet evaluated with human participants.
- **Priors, not calibrated parameters.** All costs, severities, and habituation rates are documented priors chosen on development seeds.
- **Scripted ground truth.** It encodes the scenario authors' judgement of what is "necessary", and annotator agreement on intervention timing is known to be low (Modgil 2026).
- **Simple scenarios.** Short, linear, single-agent tasks with known plans. Real agents branch, re-plan, and run in parallel.
- **Simulated confidence.** It is noisy but correlated with errors. Real LLM confidence may be worse, and §6.5 shows that this matters.
- **Heuristic integrations.** The Claude Code hook classifies tools with a heuristic and is not a security boundary.
- **Name conflict.** The PyPI name `agentpause` belongs to an unrelated project (see `research/novelty_audit.md` §4).

## 10. Conclusion

AgentPause makes questions about *when* an agent should involve its user concrete and comparable.
It provides shared policies, scenarios, metrics, explanations, and a study protocol in one open
toolkit. In simulation, deferring and batching clarification questions up to their commitment
points reduced interruptions relative to a myopic expected-value policy without increasing harm.
Simple rules remained competitive. Whether timing-aware interventions and their explanations
help people is the next step, and the toolkit is built to run that study.

## Reproducibility statement

All code, scenarios, configurations, seeds, and reference results are in the repository. The
following commands regenerate every simulated number and figure in this draft and check its
hashes:

```
python experiments/reproduce_all.py
python scripts/check_reproducibility.py
```

## References

The full bibliography with URLs is in `research/prior_art.md`. Works cited in this draft:

- Adamczyk & Bailey; Iqbal & Bailey; Bailey & Konstan (2006): interruption and breakpoints, OASIS.
- Akhawe & Felt (2013), *Alice in Warningland*; Anderson, Vance et al. (2015–18): habituation to warnings.
- Chen et al. (2026), *Comparing Human Oversight Strategies for Computer-Use Agents*.
- Dong et al. (2026), *Value of Information: A Framework for Human–Agent Communication*, ACL.
- Eiband et al. (2019), placebic explanations.
- Fox et al. (2017), explainable planning; Krarup et al. (2021), contrastive explanations of plans, JAIR.
- Gulati et al. (2026), *Ask Early, Ask Late, Ask Right*.
- Hamid, Li & Liang (2026), *When2Talk*.
- Horvitz (1999), *Principles of Mixed-Initiative User Interfaces*, CHI.
- Huq et al. (2026), *Modeling Distinct Human Interaction in Web Agents*.
- Jian, Bisantz & Drury (2000), trust in automated systems; Körber (2018), trust in automation questionnaire.
- Kiyani, Noorani, Pappas & Hassani (2026), *Strategic Decision Support for AI Agents*.
- Lim, Dey & Avrahami (2009), why and why-not explanations.
- Love, Andriella & Alenyà (2025/2026), temporal counterfactual explanations of behaviour-tree decisions.
- Modgil (2026), *The Saturation Trap*.
- Ren et al. (2023), KnowNo; Singh et al., Ask4Help; SAGE-Agent / ClarifyBench; HiL-Bench; AppWorld-UL; SteerBench-Work.
- Scerri, Pynadath & Tambe (2002), adjustable autonomy, JAIR.
- Schemmer et al. (2023), appropriate reliance on AI advice.
- Wachter, Mittelstadt & Russell (2017), counterfactual explanations.
- Yan (2026), user-authored permission policies for AI agents.
- Zhang et al. (2026), *Calibration Is Not Control*.
- Zhou et al. (2026), *When Should Users Check?*, CHI.
- Systems: AutoGen, OpenHands, Magentic-UI, Claude Code, OpenAI Codex, Gemini Computer Use, LangChain, Mastra.

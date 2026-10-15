# C. Prior art: HCI, human factors and human–agent interaction for AgentPause

Investigation date: 2026-10-14. Scope: interruption management and timing, levels and adaptive automation, human–AI interaction guidelines, human–LLM-agent collaboration and oversight (2023–2026), confirmation, consent and warning fatigue, and sense of agency.

**How the items were checked.** Each item was checked against its DOI record (Crossref API), its arXiv abstract or HTML page, or the publisher's or proceedings page. ACM DL pages return HTTP 403 to automated fetches. For ACM papers, the title, authors, venue and year were confirmed through Crossref DOI metadata, and the content came from arXiv or author PDFs. Where content comes from a secondary source or from knowledge of the paper rather than a fetched abstract, the entry says so ("content note"). Items that could not be verified were left out (see the end of the file).

**Legend.** Competitor = **yes** (does the same job as AgentPause: decides at runtime whether, when and how to involve the human) / **partial** (overlaps on one or two dimensions) / **no** (background, evidence or design input only).

---

## 0. Quick map (most relevant first)

| # | Item | Year | Competitor | Why it matters |
|---|---|---|---|---|
| D1 | Zhou et al., *When Should Users Check? Modeling Confirmation Frequency in Multi-Step Agentic AI Tasks* (CHI '26) | 2026 | **yes (closest)** | Decision-theoretic placement of confirmation checkpoints for LLM agents, compared against confirm-at-end |
| D2 | Chen et al., *Comparing Human Oversight Strategies for Computer-Use Agents* | 2026 | **partial→yes** | Compares 4 oversight strategies live (per-action confirm, risk-gated, plan, hybrid). Finds timing mismatch and calls for adaptive oversight |
| D3 | Huq et al., *Modeling Distinct Human Interaction in Web Agents* (CowCorpus / PlowPilot) | 2026 | **yes** | Learns when users will intervene and prompts only then |
| D16 | Li et al., *Options, Not Clicks* (Conleash) | 2026 | **yes (architecture)** | Client-side consent middleware for MCP: risk lattice, auto-permit or escalate, learns rules from user decisions |
| D6 | Magentic-UI (Microsoft) | 2025 | **partial** | Action guards (irreversibility labels plus an LLM judge), co-planning, simulated-user help-seeking |
| D14 | Anthropic: Claude Code auto mode and *Measuring agent autonomy* | 2026 | **partial (industry)** | 93% of prompts approved (approval fatigue). Tiered classifier replaces prompts |
| D13 | Zhang et al., *Autonomy Reshapes How Personalization Affects Privacy…* (COLM '26) | 2026 | partial | Risk-contingent autonomy raises perceived control: direct support for the AgentPause hypothesis |
| C6 | Feng, McDonald & Zhang, *Levels of Autonomy for AI Agents* | 2025 | partial | L1–L5 user roles. Flags "rubber-stamping" at the Approver level. Autonomy is fixed, not adaptive |
| A1 | Horvitz, *Principles of Mixed-Initiative UIs* (CHI '99) | 1999 | partial (ancestor) | Expected-utility thresholds for act / dialog / do nothing. Timing services to attention |
| A2–A3 | Horvitz et al., attention models / BusyBody (2003–04) | 2003–04 | partial (ancestor) | Personalized, learned cost-of-interruption models. Deferral as a decision |
| A5–A7 | Adamczyk & Bailey '04; Iqbal & Bailey '05–'10 (OASIS) | 2004–10 | no (evidence) | Interrupting at task breakpoints cuts resumption lag, annoyance and frustration |
| E1–E2 | Chen et al. *Need Help?*; Pu et al. *Assistance or Disruption?* (CHI '25) | 2025 | partial | Timing of proactive LLM help; too-frequent help is "annoying" |
| F-series | Warning and consent habituation (Böhme '10, Bravo-Lillo '13/'14, Anderson '15, Vance '18, Akhawe & Felt '13, Wijesekera '17) | 2008–18 | no (design input) | Why always-ask fails, and how to make rare prompts effective |

---

## A. Interruption management and timing (foundational)

### A1. Principles of Mixed-Initiative User Interfaces
- **Year:** 1999 (CHI '99)
- **Authors / affiliation:** Eric Horvitz, Microsoft Research
- **URL:** https://doi.org/10.1145/302979.303030 (author page: https://erichorvitz.com/uiact.htm)
- **What it does / finds:** Sets out 12 principles for coupling automated services with direct manipulation, shown through the LookOut calendaring agent. They include "considering uncertainty about a user's goals," "considering the user's attention in the timing of services," "inferring ideal action in light of costs, benefits, and uncertainties," "employing dialog to resolve key uncertainties," "allowing efficient direct invocation and termination," "minimizing the cost of poor guesses about action and timing," "scoping precision of service to match uncertainty," and "continuing to learn by observing." Its decision-theoretic core: given the inferred probability that the user has a goal, choose *no action*, *dialog* (ask) or *autonomous action* by comparing expected utilities. This yields probability thresholds between the three regimes. LookOut also learned how long to wait (timing) before offering help, based on observed user dwell behavior. (Content note: the list and threshold scheme were confirmed through course summaries of the paper; the PDF did not text-extract.)
- **Overlap with AgentPause:** Very high at the concept level. Act versus ask versus do-nothing is the ancestor of CONTINUE / CLARIFY / ASK_HUMAN. It already factors in uncertainty, cost of interruption, timing and learning from the user.
- **What AgentPause does differently / builds on:** It moves the idea from single-shot desktop assistance to multi-step LLM agents acting on the world. It adds consequence severity, reversibility, task progress and breakpoints, and explicit DEFER and BLOCK outcomes. It also produces explanations and evaluates human agency, not only utility.
- **Direct competitor?** Partial. This is the conceptual ancestor, not a system for LLM agents.
- **Type:** Academic (plus a research prototype, LookOut)

### A2. Models of attention in computing and communication / Learning and reasoning about interruption
- **Year:** 2003
- **Authors / affiliation:** Eric Horvitz, Carl Kadie, Tim Paek, David Hovel (CACM); Eric Horvitz, Johnson Apacible (ICMI '03), Microsoft Research
- **URL:** https://doi.org/10.1145/636772.636798 ; https://doi.org/10.1145/958432.958440
- **What it does / finds:** Treats attention as a scarce resource. Alerts are delivered by comparing the expected cost of interrupting now against the expected cost of *delayed review*, so deferral is a first-class decision. The ICMI paper learns Bayesian models of a user's interruptibility from desktop activity, calendar and visual/acoustic cues. (Content note: summarized from knowledge of the papers; DOIs verified.)
- **Overlap:** AgentPause's DEFER and interruption-cost signals restate this "cost of delayed action versus cost of interruption" trade-off.
- **What AgentPause does differently:** Here the decision is about delivering messages to a busy user, not about gating an agent's actions. AgentPause has to weigh the harm of the *agent continuing* (irreversibility) on top of the cost of interrupting.
- **Direct competitor?** No. Foundational model.
- **Type:** Academic

### A3. BusyBody: creating and fielding personalized models of the cost of interruption
- **Year:** 2004 (CSCW '04)
- **Authors / affiliation:** Eric Horvitz, Paul Koch, Johnson Apacible, Microsoft Research
- **URL:** https://doi.org/10.1145/1031607.1031690
- **What it does / finds:** A system that collects experience-sampling labels of how costly an interruption would be. From these it learns per-user models that predict the current cost of interruption from desktop events, meetings and context, for use by alerting systems. (Content note: from knowledge of the paper; DOI verified.)
- **Overlap:** Personalized, learned cost-of-interruption estimation. This corresponds to AgentPause's "interruption cost" plus "user preferences / history" signals.
- **What AgentPause does differently:** It combines interruption cost with action-risk signals and the agent's uncertainty, and it outputs gating decisions for the agent rather than notification delivery.
- **Direct competitor?** No. A component-level precursor.
- **Type:** Both (academic plus fielded MSR prototype)

### A4. Comparison of Four Primary Methods for Coordinating the Interruption of People in HCI
- **Year:** 2002 (Human–Computer Interaction 17(1))
- **Authors / affiliation:** Daniel C. McFarlane (affiliation not verified)
- **URL:** https://doi.org/10.1207/S15327051HCI1701_2
- **What it does / finds:** A lab experiment comparing four coordination methods: **immediate** (no notice), **negotiated** (the user is warned and chooses when to handle the interruption), **mediated** (a proxy decides when to deliver) and **scheduled** (fixed intervals). Negotiated generally gave the best overall performance. Immediate was best only for promptness on the interrupting task. (Content note: from a secondary summary.)
- **Overlap:** These four methods map directly onto AgentPause's design space: ASK_HUMAN now (immediate), DEFER to a breakpoint (mediated or scheduled), and "agent asks, user picks when" (negotiated).
- **What AgentPause does differently:** It chooses the coordination method per action, adaptively, using risk and context, instead of fixing one method per system.
- **Direct competitor?** No. Supplies the baselines AgentPause should compare against (immediate versus mediated/adaptive).
- **Type:** Academic

### A5. If not now, when? The effects of interruption at different moments within task execution
- **Year:** 2004 (CHI '04)
- **Authors / affiliation:** Piotr D. Adamczyk, Brian P. Bailey, University of Illinois at Urbana-Champaign
- **URL:** https://doi.org/10.1145/985692.985727 (PDF: https://hci.rwth-aachen.de/materials/conferences/CHI2004/1p271.pdf)
- **What it does / finds:** Builds task models with event-perception techniques and interrupts users at moments predicted to be best or worst. Different moments had different effects on emotional state (annoyance, frustration) and on social attribution (the interrupting system was seen as more respectful at "best" moments). This is a key piece of evidence that **when** you interrupt matters, not only **whether**.
- **Overlap:** This is the empirical basis for AgentPause's "task progress / breakpoint" signal and its DEFER action.
- **What AgentPause does differently:** Applies breakpoint timing to an agent's request for human input. In AgentPause, the "primary task" is both the user's own work and the agent's ongoing execution.
- **Direct competitor?** No (evidence)
- **Type:** Academic

### A6. Iqbal & Bailey: workload as a predictor of opportune moments (CHI EA '05) and task structure predicts cost of interruption (CHI '06)
- **Year:** 2005, 2006
- **Authors / affiliation:** Shamsi T. Iqbal, Brian P. Bailey, UIUC
- **URL:** https://doi.org/10.1145/1056808.1056948 ; https://doi.org/10.1145/1124772.1124882
- **What it does / finds:** In the 2005 paper, interrupting at predicted *best* (low-workload, subtask-boundary) moments consistently caused less resumption lag and less annoyance than random or *worst* moments, and fostered more positive social attribution. In the 2006 paper, the cost of interruption depends on where in the task hierarchy it lands. Boundaries between larger units (coarser breakpoints) are cheaper, and task models can predict the cost. (Content note: the 2005 result is confirmed by secondary summary; the 2006 characterization is from knowledge of the paper; DOIs verified.)
- **Overlap:** Supports modeling the *granularity* of breakpoints. Interrupt at coarse boundaries, such as between plan steps, rather than mid-step.
- **What AgentPause does differently:** It has to locate breakpoints in two tasks at once: the agent's plan (between steps or subgoals) and the user's concurrent activity.
- **Direct competitor?** No (evidence)
- **Type:** Academic

### A7. Effects of intelligent notification management on users and their tasks (CHI '08) / OASIS (TOCHI '10)
- **Year:** 2008, 2010
- **Authors / affiliation:** Shamsi T. Iqbal, Brian P. Bailey, UIUC
- **URL:** https://doi.org/10.1145/1357054.1357070 ; https://doi.org/10.1145/1879831.1879833
- **What it does / finds:** OASIS detects breakpoints with statistical models and holds notifications until one occurs. Delivering at breakpoints reduced frustration and reaction time compared with immediate delivery. The relevance of a notification's content determines the *type* of breakpoint (coarse, medium or fine) at which it should be delivered. The models detected breakpoints reasonably well but struggled to tell their types apart.
- **Overlap:** This is effectively a "DEFER until breakpoint" middleware for notifications, which is AgentPause's DEFER for agent questions.
- **What AgentPause does differently:** Deferral has to be bounded by consequence. A question about an irreversible step cannot wait if the agent is about to take it. AgentPause therefore couples deferral with pausing the agent (DEFER + hold) or continuing safe work.
- **Direct competitor?** Partial for the DEFER mechanism only
- **Type:** Both (academic plus OASIS research system)

### A8. A diary study of task switching and interruptions
- **Year:** 2004 (CHI '04)
- **Authors / affiliation:** Mary Czerwinski, Eric Horvitz, Susan Wilhite, Microsoft Research
- **URL:** https://doi.org/10.1145/985692.985715
- **What it does / finds:** A week-long diary study of information workers. It documents frequent task switching, interruptions, and difficulty returning to complex tasks after interruption, which motivates tools for reinstating task context. (Content note: from knowledge of the paper; DOI verified.)
- **Overlap:** Motivates re-entry support in ASK_HUMAN dialogs (what was happening, what is at stake).
- **What AgentPause does differently:** Supplies that re-entry context automatically in the explanation that accompanies each intervention.
- **Direct competitor?** No
- **Type:** Academic

### A9. The cost of interrupted work: more speed and stress
- **Year:** 2008 (CHI '08)
- **Authors / affiliation:** Gloria Mark (UC Irvine), Daniela Gudith, Ulrich Klocke (Humboldt-Universität zu Berlin)
- **URL:** https://doi.org/10.1145/1357054.1357072 (PDF: https://www.ics.uci.edu/~gmark/chi08-mark.pdf)
- **What it does / finds:** In a simulated email-office task, interrupted participants finished *faster* with no loss of quality. They paid for it with more stress, frustration, time pressure and effort. Whether the interruption shared the task's context made no difference. Personality (openness, need for structure) predicted disruption costs.
- **Overlap:** Interruption cost is largely *subjective* (stress and workload), so measuring only time or accuracy under-counts it. AgentPause's evaluation should include NASA-TLX-style workload and stress measures.
- **What AgentPause does differently:** Uses these costs as an objective to minimize, and personalizes using individual differences (preferences).
- **Direct competitor?** No (evidence)
- **Type:** Academic

### A10. Memory for goals (Altmann & Trafton) and resumption-lag studies
- **Year:** 2002; 2003; 2008
- **Authors / affiliation:** Erik M. Altmann (Michigan State), J. Gregory Trafton (Naval Research Laboratory); Trafton, Altmann, Brock, Mintz (IJHCS 2003); Monk, Trafton, Boehm-Davis (JEP: Applied 2008)
- **URL:** https://doi.org/10.1207/s15516709cog2601_2 ; https://doi.org/10.1016/s1071-5819(03)00023-5 ; https://doi.org/10.1037/a0014402
- **What it does / finds:** The memory-for-goals model holds that suspended goals decay in activation and need priming or rehearsal to resume. A brief warning before an interruption (the "interruption lag") lets people encode where they were and resume faster (Trafton et al. 2003). Longer and more demanding interruptions increase resumption time (Monk et al. 2008). (Content note: from knowledge of the papers; DOIs verified.)
- **Overlap:** Supports a "negotiated" pre-alert ("in about 2 steps I'll need your input on X") and provides resumption cues after the intervention.
- **What AgentPause does differently:** Applies this to the human's goal state *and* to the human's model of the agent's state (situation awareness on re-entry).
- **Direct competitor?** No
- **Type:** Academic

### A11. On the need for attention-aware systems
- **Year:** 2006 (Computers in Human Behavior 22(4))
- **Authors / affiliation:** Brian P. Bailey, Joseph A. Konstan (UIUC; University of Minnesota)
- **URL:** https://doi.org/10.1016/j.chb.2005.12.009
- **What it does / finds:** Interruptions during task execution increased completion time, error rates, annoyance and anxiety compared with interruptions at task boundaries. This is the core argument for attention-aware systems. (Content note: title and venue verified; findings from knowledge of the paper.)
- **Overlap / AgentPause difference:** The same justification for breakpoint-aware timing, applied to agent oversight.
- **Direct competitor?** No
- **Type:** Academic

### A12. Multitasking and monotasking: the effects of mental workload on deferred task interruptions
- **Year:** 2010 (CHI '10)
- **Authors / affiliation:** Dario D. Salvucci, Peter Bogunovich, Drexel University
- **URL:** https://doi.org/10.1145/1753326.1753340
- **What it does / finds:** When people *may defer* an interruption, they switch to it during low-workload periods 94% of the time and during high-workload periods only 6% of the time. People "monotask" until primary-task workload is minimal.
- **Overlap:** Strong support for a DEFER option and for letting users choose when to answer (a negotiated mode). Users naturally pick breakpoints themselves.
- **What AgentPause does differently:** Predicts those low-load moments for the user and still forces immediate attention for high-severity, irreversible decisions.
- **Direct competitor?** No (evidence)
- **Type:** Academic

### A13. Predicting human interruptibility with sensors
- **Year:** 2003 (CHI) / 2005 (TOCHI)
- **Authors / affiliation:** James Fogarty, Scott E. Hudson, Christopher G. Atkeson, Daniel Avrahami, Jodi Forlizzi, Sara Kiesler, Johnny C. Lee, Jie Yang, Carnegie Mellon University
- **URL:** https://doi.org/10.1145/1057237.1057243 (CHI version: https://doi.org/10.1145/642611.642657)
- **What it does / finds:** Simple sensors (such as speech detection and keyboard/mouse activity) predicted self-reported interruptibility about as well as human observers could. (Content note: from knowledge of the paper; DOIs verified.)
- **Overlap / AgentPause difference:** Cheap behavioral signals can estimate "cognitive load / interruptibility." AgentPause can use interaction telemetry (typing, focus, idle time) as its load proxy.
- **Direct competitor?** No
- **Type:** Academic

### A14. Beyond Interruptibility: Predicting Opportune Moments to Engage Mobile Phone Users
- **Year:** 2017 (IMWUT 1(3))
- **Authors / affiliation:** Martin Pielot et al. (full author list not re-verified)
- **URL:** https://doi.org/10.1145/3130956
- **What it does / finds:** A study of 337 phone users. An ML model predicting whether a user will click *and engage* with notified content achieved a 66.6% higher success rate than a naive baseline. Attracting attention is not the same as holding it.
- **Overlap / AgentPause difference:** For AgentPause, the measure of success is not "user responded" but "user responded *meaningfully*" (did not rubber-stamp).
- **Direct competitor?** No
- **Type:** Academic

### A15. Robot Classification of Human Interruptibility and a Study of Its Effects (HRI)
- **Year:** 2018 (ACM THRI 7(2)); preprint "Effects of Interruptibility-Aware Robot Behavior" (arXiv:1804.06383)
- **Authors / affiliation:** Siddhartha Banerjee, Andrew Silva, Sonia Chernova, Georgia Tech
- **URL:** https://doi.org/10.1145/3277902 ; https://arxiv.org/abs/1804.06383
- **What it does / finds:** A robot that needs help classifies human interruptibility on an ordinal scale (temporal CRF models) and interrupts at better moments. In a 42-participant mock manufacturing study, participants kept their task performance, and interruptibility-awareness improved the robot's task performance and how participants perceived it socially.
- **Overlap:** An agent deciding *when* to ask a human for help, timed by human interruptibility. Structurally the same as AgentPause's ASK_HUMAN/DEFER.
- **What AgentPause does differently:** Adds action risk, reversibility and agent uncertainty, plus the CLARIFY and BLOCK outcomes, in a software-agent setting.
- **Direct competitor?** Partial (HRI analogue)
- **Type:** Academic

---

## B. Levels of automation, adaptive automation, trust and transparency

### B1. Human and computer control of undersea teleoperators (levels of automation)
- **Year:** 1978 (MIT Man-Machine Systems Lab technical report; NTIS ADA057655)
- **Authors / affiliation:** Thomas B. Sheridan, William L. Verplank, MIT
- **URL:** https://ntrl.ntis.gov/NTRL/dashboard/searchResults/titleDetail/ADA057655.xhtml
- **What it does / finds:** The origin of the "levels of automation" scale. Automation is not all-or-nothing; intermediate levels include "computer suggests, human approves," "computer executes and informs the human," and "computer decides whether to tell the human." (Content note: the original 10-level wording was seen only in secondary adaptations.)
- **Overlap:** AgentPause's outputs correspond to points on this scale. CONTINUE ≈ "execute and maybe inform," ASK_HUMAN ≈ "execute if human approves," BLOCK ≈ "human must act."
- **What AgentPause does differently:** It selects the level *per action at runtime* instead of fixing it per system.
- **Direct competitor?** No (foundational)
- **Type:** Academic (technical report)

### B2. A model for types and levels of human interaction with automation
- **Year:** 2000 (IEEE Trans. SMC-A 30(3))
- **Authors / affiliation:** Raja Parasuraman (Catholic University of America), Thomas B. Sheridan (MIT), Christopher D. Wickens (UIUC)
- **URL:** https://doi.org/10.1109/3468.844354
- **What it does / finds:** Automation can be applied at different levels to four function classes: information acquisition, information analysis, decision selection and action implementation. Primary evaluation criteria are human performance consequences (workload, situation awareness, complacency, skill degradation). Secondary criteria are automation reliability and the *costs of decision/action consequences*. High automation of decision and action is advised only when reliability is high and consequences are low. (Content note: from knowledge of the paper; DOI verified.)
- **Overlap:** AgentPause's "severity" and "reversibility" signals are exactly the "consequence costs" criterion. Agent uncertainty is a proxy for "reliability."
- **What AgentPause does differently:** Turns the static design guidance into a runtime policy evaluated on each proposed action.
- **Direct competitor?** No (framework)
- **Type:** Academic

### B3. The effects of level of automation and adaptive automation on human performance, SA and workload in a dynamic control task
- **Year:** 2004 (Theoretical Issues in Ergonomics Science 5(2))
- **Authors / affiliation:** David B. Kaber (NC State), Mica R. Endsley (SA Technologies)
- **URL:** https://doi.org/10.1080/1463922021000054335
- **What it does / finds:** A dual-task experiment with low, intermediate and high levels of automation, dynamically allocated with cycle times of 20, 40 and 60% of task time. Level of automation drove primary-task performance and situation awareness. Low-level (action-support) automation gave the best performance, and intermediate levels supported higher SA.
- **Overlap:** Classic adaptive automation, where control shifts between human and machine over time.
- **What AgentPause does differently:** The triggers are content-dependent (risk, uncertainty, ambiguity) rather than time-cycled or driven by operator workload alone. The domain is LLM agents.
- **Direct competitor?** No (paradigm precursor)
- **Type:** Academic

### B4. Toward a Characterization of Adaptive Systems: a framework for researchers and system designers
- **Year:** 2012 (Human Factors 54(6))
- **Authors / affiliation:** Karen M. Feigh (Georgia Tech), Michael C. Dorneich (Honeywell), Caroline C. Hayes (University of Minnesota)
- **URL:** https://doi.org/10.1177/0018720812443983
- **What it does / finds:** A taxonomy of adaptive systems by **triggers** (operator-based, such as workload and state; system-based; environment-based; task/mission-based; spatio-temporal) and by **what adapts** (function allocation, task scheduling, interaction, content). (Content note: title, venue and authors verified; taxonomy from knowledge of the paper.)
- **Overlap:** A ready-made vocabulary for AgentPause's signals (triggers) and outputs (adaptations: allocation = CONTINUE/ASK, scheduling = DEFER, content = explanation).
- **What AgentPause does differently:** Instantiates the framework for LLM-agent oversight and evaluates it on agency.
- **Direct competitor?** No (framework)
- **Type:** Academic

### B5. Trust in Automation: Designing for Appropriate Reliance
- **Year:** 2004 (Human Factors 46(1))
- **Authors / affiliation:** John D. Lee, Katrina A. See, University of Iowa
- **URL:** https://doi.org/10.1518/hfes.46.1.50_30392
- **What it does / finds:** Trust should be *calibrated* to automation capability, with resolution and specificity. Misuse (over-reliance) and disuse follow from miscalibration. Designers should reveal the automation's performance, process and purpose. (Content note: from knowledge of the paper; DOI verified.)
- **Overlap:** AgentPause's explanations and uncertainty displays should calibrate trust. Asking too often can cause disuse, and too rarely can cause misuse.
- **What AgentPause does differently:** Uses the user's decision history to detect over-reliance (for example, 100% approvals) and adjust.
- **Direct competitor?** No
- **Type:** Academic

### B6. Complacency and Bias in Human Use of Automation: An Attentional Integration
- **Year:** 2010 (Human Factors 52(3))
- **Authors / affiliation:** Raja Parasuraman, Dietrich H. Manzey
- **URL:** https://doi.org/10.1177/0018720810376055
- **What it does / finds:** Automation complacency and automation bias share attentional mechanisms. They occur in experts as well as novices, are not easily prevented by training or instructions, and are most likely when operators are multitasking. (Content note: from knowledge of the paper; DOI verified.)
- **Overlap:** Explains why approval prompts get rubber-stamped, especially when the user is busy. This bears on how cognitive load and approval quality interact.
- **What AgentPause does differently:** Treats a high load estimate as a reason to *defer* a non-urgent approval, rather than to ask a distracted user, or to require friction for high-stakes approvals.
- **Direct competitor?** No
- **Type:** Academic

### B7. Ironies of Automation
- **Year:** 1983 (Automatica 19(6))
- **Authors / affiliation:** Lisanne Bainbridge, University College London
- **URL:** https://doi.org/10.1016/0005-1098(83)90046-8
- **What it does / finds:** The more automated a system, the more crucial and the harder the human's residual role becomes. Monitors lose skill and situation awareness, yet are expected to take over in the hardest cases.
- **Overlap / AgentPause difference:** A warning for AgentPause. If it suppresses most interruptions, the remaining ones reach a human who is out of the loop, so each ASK_HUMAN needs re-entry context.
- **Direct competitor?** No
- **Type:** Academic

### B8. Situation awareness-based agent transparency (SAT) and human–autonomy teaming effectiveness
- **Year:** 2018 (Theoretical Issues in Ergonomics Science 19(3))
- **Authors / affiliation:** Jessie Y. C. Chen, Shan G. Lakhmani, Kimberly Stowers, Anthony R. Selkowitz, Julia L. Wright, Michael Barnes, US Army Research Laboratory
- **URL:** https://doi.org/10.1080/1463922X.2017.1315750 (decade review: https://doi.org/10.1080/10447318.2026.2724199)
- **What it does / finds:** The SAT model specifies three levels of agent transparency: (1) goals, current actions and plans; (2) reasoning; (3) projected outcomes and uncertainty. Studies found that higher transparency improved operators' decision accuracy and trust calibration, generally without large workload costs. (Content note: from knowledge of the SAT line; DOI verified.)
- **Overlap:** A template for what AgentPause's intervention explanations should contain.
- **What AgentPause does differently:** Scales transparency to the decision. A short card for CLARIFY, and a full SAT1–3 view for high-severity ASK_HUMAN or BLOCK.
- **Direct competitor?** No
- **Type:** Academic

---

## C. Human–AI interaction guidelines, mixed initiative and autonomy frameworks

### C1. Agents that reduce work and information overload, and the direct manipulation vs. interface agents debate
- **Year:** 1994 (CACM 37(7)); 1997 (Interactions)
- **Authors / affiliation:** Pattie Maes (MIT Media Lab); Ben Shneiderman (University of Maryland) and Pattie Maes
- **URL:** https://doi.org/10.1145/176789.176792 ; https://doi.org/10.1145/267505.267514
- **What it does / finds:** Learning interface agents that observe the user and earn delegation over time. The two central problems are *competence* (knowing when, what and how to help) and *trust*. The 1997 debate frames the tension between user control and delegation. (Content note: I could not confirm through a fetched source that Maes's agents used confidence "tell-me / do-it" thresholds, so that claim is omitted.)
- **Overlap:** Learning *when* to act from user history is AgentPause's "history of user decisions."
- **What AgentPause does differently:** Explicit risk gating plus agency preservation, applied to LLM agents.
- **Direct competitor?** No
- **Type:** Academic

### C2. Mixed-Initiative Interaction
- **Year:** 1999 (IEEE Intelligent Systems 14(5))
- **Authors / affiliation:** James E. Allen, Curry I. Guinn, Eric Horvitz
- **URL:** https://doi.org/10.1109/5254.796083
- **What it does / finds:** Defines mixed initiative as a flexible interaction strategy in which each agent contributes what it is best suited for, and initiative shifts between parties as needed. (Content note: from knowledge of the paper; DOI verified.)
- **Overlap / AgentPause difference:** AgentPause is a policy for *initiative shifts* between agent and human.
- **Direct competitor?** No
- **Type:** Academic

### C3. Guidelines for Human-AI Interaction
- **Year:** 2019 (CHI '19)
- **Authors / affiliation:** Saleema Amershi, Dan Weld, Mihaela Vorvoreanu, Adam Fourney, Besmira Nushi, Penny Collisson, Jina Suh, Shamsi Iqbal, Paul N. Bennett, Kori Inkpen, Jaime Teevan, Ruth Kikin-Gil, Eric Horvitz, Microsoft
- **URL:** https://doi.org/10.1145/3290605.3300233 ; guideline list: https://www.microsoft.com/en-us/haxtoolkit/library/
- **What it does / finds:** 18 validated guidelines. Those most relevant to AgentPause: **G3 Time services based on context**, **G7 Support efficient invocation**, **G8 Support efficient dismissal**, **G9 Support efficient correction**, **G10 Scope services when in doubt**, **G11 Make clear why the system did what it did**, **G13 Learn from user behavior**, **G14 Update and adapt cautiously**, **G16 Convey the consequences of user actions**, **G17 Provide global controls**.
- **Overlap:** AgentPause operationalizes G3, G10, G13 and G16 (plus G11 through explanations).
- **What AgentPause does differently:** The guidelines are qualitative. AgentPause is a computational policy that can be evaluated against them, and the guidelines can serve as a heuristic-evaluation rubric.
- **Direct competitor?** No
- **Type:** Academic (plus HAX toolkit artifact)

### C4. Human-Centered Artificial Intelligence: Reliable, Safe & Trustworthy
- **Year:** 2020 (IJHCI 36(6)); expanded in the book *Human-Centered AI* (OUP, 2022)
- **Authors / affiliation:** Ben Shneiderman, University of Maryland
- **URL:** https://doi.org/10.1080/10447318.2020.1741118
- **What it does / finds:** A two-dimensional HCAI framework in which high automation *and* high human control are achievable together, not opposite ends of one axis. It warns against both excessive automation and excessive human control. (Content note: from knowledge of the paper; DOI verified.)
- **Overlap:** The AgentPause hypothesis (more agency *and* fewer interruptions) is the HCAI "high control + high automation" claim made testable.
- **What AgentPause does differently:** Supplies an empirical, measurable mechanism and an evaluation.
- **Direct competitor?** No
- **Type:** Academic

### C5. Challenges in Human-Agent Communication
- **Year:** 2024 (arXiv:2412.10380; MSR-TR-2024-53)
- **Authors / affiliation:** Gagan Bansal, Jennifer Wortman Vaughan, Saleema Amershi, Eric Horvitz, Adam Fourney, Hussein Mozannar, Victor Dibia, Daniel S. Weld (Microsoft; Weld at AI2)
- **URL:** https://arxiv.org/abs/2412.10380
- **What it does / finds:** Twelve communication challenges for LLM agents. Agent→user: A1 what can it do, **A2 what is it about to do** (including getting permission before expensive, irreversible or preference-violating actions), A3 what is it doing, A4 side effects, A5 was the goal achieved. User→agent: **U1 what to achieve** (resolving critical goal uncertainty), U2 preferences, U3 what to do differently next time. Overarching: **X1 verifying behavior**, X2 consistency, **X3 appropriate level of detail** (including "must it confirm every request or act autonomously in familiar situations?"), X4 which past interactions matter.
- **Overlap:** A2, U1 and X3 name AgentPause's problem almost verbatim.
- **What AgentPause does differently:** An actual policy and evaluation for A2/U1/X3.
- **Direct competitor?** No (problem statement)
- **Type:** Academic

### C6. Levels of Autonomy for AI Agents
- **Year:** 2025 (arXiv:2506.12469; Knight First Amendment Institute essay series)
- **Authors / affiliation:** K. J. Kevin Feng, David W. McDonald, Amy X. Zhang, University of Washington
- **URL:** https://arxiv.org/abs/2506.12469
- **What it does / finds:** Autonomy is a design choice separate from capability. Five levels are defined by the user's role. **L1 Operator:** the agent acts only when invoked or approved. **L2 Collaborator:** shared planning and execution, and the user can take over. **L3 Consultant:** the agent does most of the work and consults the user; "when should the agent consult" is called critical. **L4 Approver:** the user is involved only at blockers or consequential actions, with *user-customizable conditions for when approval is sought*. **L5 Observer:** monitoring plus an off-switch. The paper warns that L4 invites "meaningless rubber stamping" and that misaligned agents could exploit disengaged approvers. It also notes that deciding which actions are consequential is hard. It proposes "autonomy certificates." Autonomy is treated as **fixed per deployment**, with no in-task shifting.
- **Overlap:** AgentPause effectively *moves between L1 and L4 at runtime* based on context.
- **What AgentPause does differently:** Dynamic, per-action level selection. It addresses the "which actions are consequential" question with severity and reversibility signals, and counters rubber-stamping through rationing and friction.
- **Direct competitor?** Partial. Same design space, but static and conceptual.
- **Type:** Academic

### C7. Levels of AGI for Operationalizing Progress on the Path to AGI (position paper)
- **Year:** 2024 (ICML 2024; arXiv:2311.02462)
- **Authors / affiliation:** Meredith Ringel Morris, Jascha Sohl-Dickstein, Noah Fiedel, Tris Warkentin, Allan Dafoe, Aleksandra Faust, Clement Farabet, Shane Legg, Google DeepMind
- **URL:** https://arxiv.org/abs/2311.02462
- **What it does / finds:** Alongside capability levels, defines autonomy levels and human–AI interaction paradigms: L0 No AI, L1 AI as a Tool, L2 AI as a Consultant, L3 AI as a Collaborator, L4 AI as an Expert, L5 AI as an Agent. It argues that the choice of interaction paradigm is a key lever for responsible deployment.
- **Overlap / AgentPause difference:** As with C6, a static taxonomy. AgentPause chooses the paradigm per action.
- **Direct competitor?** No
- **Type:** Academic

### C8. Ask Not What AI Can Do, But What AI Should Do: Towards a Framework of Task Delegability
- **Year:** 2019 (NeurIPS 2019; arXiv:1902.03245)
- **Authors / affiliation:** Brian Lubars, Chenhao Tan, University of Colorado Boulder
- **URL:** https://arxiv.org/abs/1902.03245
- **What it does / finds:** Four factors shape delegation preference: motivation, difficulty, **risk** and **trust**. In a survey over 100 tasks, people showed little support for full AI control and preferred "machine-in-the-loop" arrangements. Trust was the factor most associated with preferred delegation.
- **Overlap:** Justifies "user preferences" and "risk" as policy inputs, and suggests eliciting per-task delegation preferences.
- **What AgentPause does differently:** Applies delegability per action at runtime and updates it from behavior.
- **Direct competitor?** No
- **Type:** Academic

---

## D. Human–LLM-agent collaboration, oversight and confirmation (2023–2026)

### D1. When Should Users Check? Modeling Confirmation Frequency in Multi-Step Agentic AI Tasks — CLOSEST COMPETITOR
- **Year:** 2026 (CHI '26; arXiv:2510.05307)
- **Authors / affiliation:** Jieyu Zhou, Aryan Roy, Sneh Gupta, Daniel Weitekamp, Christopher J. MacLellan, Georgia Institute of Technology
- **URL:** https://doi.org/10.1145/3772318.3790655 ; https://arxiv.org/abs/2510.05307
- **What it does / finds:** Frames *where to place intermediate confirmations* in an N-step agent plan as a minimum-time scheduling problem. A formative study (n=8) found a Confirmation–Diagnosis–Correction–Redo (CDCR) cycle. The model includes per-step success probability, confirmation, diagnosis and redo costs, and cascading errors. A backward dynamic program picks the next checkpoint, with optional Beta–Bernoulli updating and re-planning after errors. In the user study, however, the parameters were **fixed per domain** (for example, 87.5% per-step accuracy and 8 steps for shopping), and per-user online adaptation is left to future work. In a within-subjects study (n=48; shopping, image editing, Overcooked; *simulated* agents), model-placed checkpoints beat **confirm-at-end**. Completion time fell 13.54% (264.7 s to 228.9 s), diagnosis time fell 17% and redo time fell 22%, and 81% of participants preferred the approach. Early errors gained about 29%, but late errors were about 4.5% *slower*. 77% disagreed that the checks disrupted flow. At each checkpoint the dialog showed the original request, the list of confirmed actions and per-step screenshots, and let the user mark the first wrong step. Stated limitations: the model ignores money, safety and emotional costs; uses simulated environments; and some users found frequent checks on trivial tasks disruptive.
- **Overlap:** Directly studies *adaptive timing of confirmations* for LLM agents and compares against a fixed strategy. It is the nearest prior art to AgentPause's core hypothesis.
- **What AgentPause does differently:** (1) Multi-signal: severity, reversibility, intent ambiguity, cognitive load, preferences and history, not just error probability and time costs. Zhou et al. explicitly exclude safety and money costs. (2) A richer action space (CLARIFY, DEFER, BLOCK), not just "check here or not." (3) Optimizes *agency and unnecessary interruptions*, not only completion time. (4) Online per-user adaptation, which Zhou et al. leave as future work. (5) Live agents rather than simulated plans. (6) Baselines should include always-ask, never-ask and confirm-at-end, where Zhou et al. compared only to confirm-at-end.
- **Direct competitor?** **Yes.** Same research question (adaptive confirmation timing for agents), narrower signal set and objective.
- **Type:** Academic

### D2. Comparing Human Oversight Strategies for Computer-Use Agents — CLOSEST EMPIRICAL COMPARATOR
- **Year:** 2026 (arXiv:2604.04918, v2 Sep 2026; venue not stated)
- **Authors / affiliation:** Chaoran Chen, Zhiping Zhang, Zeya Chen, Eryue Xu, Yinuo Yang, Ibrahim Khalilov, Simret A. Gebreegziabher, Yanfang Ye, Ziang Xiao, Yaxing Yao, Tianshi Li, Toby Jia-Jun Li (Johns Hopkins, Northeastern, Illinois Tech, UIUC, Notre Dame)
- **URL:** https://arxiv.org/abs/2604.04918
- **What it does / finds:** 48 participants in 192 live web sessions, each task containing one embedded problematic action. Four strategies modeled on industry practice were compared: **Action Confirmation** (approve every action, modeled on Claude Computer Use, with "always allow this site"); **Risk-Gated** (pause only at actions the agent flags as risky, modeled on OpenAI Operator, with "approve similar"); **Supervisory Co-Execution** (plan approval plus per-step approval, modeled on Magentic-UI); and **Structurally Enriched** (plan studio, action trace with risk labels and risk-triggered prompts). Results: plan-based strategies cut the occurrence of problematic actions (OR 0.24), but users **blocked only 29 of 138 problematic actions that reached execution (21%)**, with no reliable difference between strategies. **56% of failure episodes showed a *timing mismatch*** between when risk emerged and when the UI asked for judgment, sometimes prompting only after risky content had already been entered. Users checked *procedural* correctness ("did it follow the workflow?") rather than whether the step *should* happen, even though risk cues were present in 92% of failures. Upfront plan approval reduced runtime scrutiny. Workload and trust effects depended on consequence level: per-action confirmation was trusted more in low-consequence tasks, and the reverse held in high-consequence tasks. Design implications: **adaptive oversight** (adjust timing and granularity to task and reversibility); **request judgment *before* a consequential state change**; **re-entry scaffolding** (how the agent got here, what is at stake, what approval authorizes); **judgment-oriented transparency** (state the consequence, such as "discloses a health identifier," not just "medium risk"); **scoped, renewable delegation**; and treat plans as constraints, not authorization.
- **Overlap:** Very high. It compares fixed oversight policies empirically and concludes that oversight should align "authority, timing, and attention with decision-critical moments," which is AgentPause's thesis.
- **What AgentPause does differently:** Supplies the adaptive policy this paper calls for. It adds DEFER, CLARIFY and BLOCK, user-state signals (load, preferences, history) and agency measures. The paper's protocol (embedded problematic actions, block rate, timing-mismatch coding) is an excellent evaluation template to adopt.
- **Direct competitor?** **Partial → yes.** Empirical rather than a policy system, but it occupies the same evaluation space and already includes a risk-gated, semi-adaptive condition.
- **Type:** Academic

### D3. Modeling Distinct Human Interaction in Web Agents (CowCorpus; PlowPilot) — CLOSEST LEARNED "WHEN TO ASK" SYSTEM
- **Year:** 2026 (arXiv:2602.17588, v4 Jul 2026; "Preprint")
- **Authors / affiliation:** Faria Huq, Zora Zhiruo Wang, Zhanqiu Guo, Venu Arvind Arangarajan, Tianyue Ou, Frank Xu, Graham Neubig, Jeffrey P. Bigham (Carnegie Mellon University); Shuyan Zhou (Duke)
- **URL:** https://arxiv.org/abs/2602.17588
- **What it does / finds:** Argues that agents "either overlook critical decision points or request unnecessary confirmation." Introduces the task of *predicting human intervention* in collaborative web navigation. CowCorpus contains 400 real-user trajectories with more than 4,200 interleaved human and agent actions. It identifies four user styles: hands-off supervision, hands-on oversight, collaborative task-solving and full takeover. A step-wise classifier (`<ask_user>` versus `<agent_continue>`) takes the screenshot, accessibility tree, proposed action and history, with style-specific fine-tuned models. It improved intervention-prediction accuracy 61.4–63.4% over base LMs, and including human action history helped. **PlowPilot** (a Chrome extension) prompts the user only when an intervention is predicted. Its user study is small (4 returning participants in v2) and "preliminary." The reported usefulness gain differs by version (26.5% in v1/v2, 36.8% in v4), and participants noticed extra time cost.
- **Overlap:** Same core decision as AgentPause's CONTINUE versus ASK_HUMAN, learned from history and personalized by style.
- **What AgentPause does differently:** It predicts *where the user should be involved* (normative: risk, reversibility, ambiguity) rather than only *where the user would intervene* (descriptive), which matters because users miss risky steps (D2). It adds DEFER, CLARIFY, BLOCK and explanations, uses explicit cost-of-interruption and load signals, and is agent-agnostic middleware with a rigorous comparison against always-ask and never-ask.
- **Direct competitor?** **Yes.** A learned intervention-timing module for web agents.
- **Type:** Both (academic plus software prototype)

### D4. CowPilot: A Framework for Autonomous and Human-Agent Collaborative Web Navigation
- **Year:** 2025 (NAACL 2025 System Demonstrations; arXiv:2501.16609)
- **Authors / affiliation:** Faria Huq, Zora Zhiruo Wang, Frank F. Xu, Tianyue Ou, Shuyan Zhou, Jeffrey P. Bigham, Graham Neubig, Carnegie Mellon University
- **URL:** https://arxiv.org/abs/2501.16609 ; code: https://github.com/oaishi/CowPilot
- **What it does / finds:** The agent proposes the next step. The user can pause, reject or take alternative actions, interleave their own actions, and hand control back. In case studies on five sites, collaborative mode reached 95% success with humans performing only 15.2% of steps, and the agent alone drove up to half of the successes.
- **Overlap:** Shared-control infrastructure with human pause and override.
- **What AgentPause does differently:** In CowPilot the *human* decides when to intervene (user-initiated). AgentPause adds *system-initiated* intervention timing.
- **Direct competitor?** Partial
- **Type:** Both

### D5. "Here, Let Me Help": An Empirical Study of User Interventions in Human–Web Agent Collaboration
- **Year:** 2026 (CHI '26, Article 1541)
- **Authors / affiliation:** Joohee Kim, Sungbeom Cho, Duc M. Nguyen, Jaehyeong Jeon, Minjeong Shin, Sungahn Ko (affiliations not verified)
- **URL:** https://doi.org/10.1145/3772318.3791536
- **What it does / finds:** A controlled lab study (n=30, 12 tasks on live shopping, travel and information sites). It distinguishes **explicit interventions** (halting or overriding) from **implicit** ones (guiding or preparing the environment without stopping execution). **Perceived slowness, rather than correctness, was a primary trigger for intervention.** Breakdowns included skipped filters and sub-steps and UI elements hidden in dropdowns or tooltips. (Content note: from search-result excerpts of the ACM page; the full text was inaccessible, 403.)
- **Overlap:** Evidence about *why* users intervene. They intervene for efficiency more than safety, which shows that user-initiated oversight alone does not protect high-risk steps.
- **What AgentPause does differently:** System-initiated, risk-aware intervention. It also suggests surfacing progress and ETA so users don't interrupt out of impatience.
- **Direct competitor?** No (evidence)
- **Type:** Academic

### D6. Magentic-UI: Towards Human-in-the-loop Agentic Systems
- **Year:** 2025 (arXiv:2507.22358; open source)
- **Authors / affiliation:** Hussein Mozannar, Gagan Bansal, Cheng Tan, Adam Fourney, Victor Dibia, Jingya Chen, Jack Gerrits, Tyler Payne, Matheus Kunzler Maldaner, Madeleine Grunde-McLaughlin, Eric Zhu, Griffin Bassman, Jacob Alber, Peter Chang, Ricky Loynd, Friederike Niedtner, Ece Kamar, Maya Murad, Rafah Hosn, Saleema Amershi, Microsoft Research AI Frontiers
- **URL:** https://arxiv.org/abs/2507.22358 ; code (MIT licence): https://github.com/microsoft/magentic-ui
- **What it does / finds:** A multi-agent web, code and file agent with human-in-the-loop mechanisms: co-planning (plan editor), co-tasking, multi-tasking, **action guards** and long-term memory. In action guards, each tool action carries a developer-assigned irreversibility label: "always irreversible" (for example, uploading a file) always needs approval, "never" (scrolling) runs freely, and "maybe" (clicking) is decided by an **LLM judge**. In the qualitative study, users endorsed approvals for payments, sending email and subscribing, but found approvals for adding to cart, or after they had just edited a plan, excessive. They wanted a **third option** beyond approve or reject, valued clarifying questions, and preferred **bundling several questions into one interruption**. In the simulated-user evaluation on GAIA, help-seeking with an informed simulated user raised completion from 30.3% to 51.9% while the agent asked for help in only about 10% of tasks.
- **Overlap:** Irreversibility-based gating of actions plus clarifying questions, the two main AgentPause intervention types.
- **What AgentPause does differently:** Static labels plus a binary LLM judge are replaced by a multi-signal policy that includes timing, load and history. AgentPause adds DEFER, BLOCK and bundling of deferred questions, explanations, and a formal evaluation of agency and unnecessary prompts. Magentic-UI is a natural **host and baseline**.
- **Direct competitor?** **Partial.** Its action guards are the closest deployed open-source analogue.
- **Type:** Both

### D7. Overseeing Agents Without Constant Oversight: Challenges and Opportunities
- **Year:** 2026 (arXiv:2602.16844)
- **Authors / affiliation:** Madeleine Grunde-McLaughlin, Hussein Mozannar, Maya Murad, Jingya Chen, Saleema Amershi, Adam Fourney (Microsoft Research team; per-author affiliations not verified)
- **URL:** https://arxiv.org/abs/2602.16844
- **What it does / finds:** Three studies with a computer-use agent on how detailed action traces should be for verification. Basic traces are cumbersome. A redesigned interface cut error-finding time and raised confidence but **did not meaningfully improve accuracy**. Challenges include built-in assumptions, users' subjective and shifting correctness criteria, and the limits of communicating process.
- **Overlap:** The goal of oversight without constant attention.
- **What AgentPause does differently:** Focuses human attention on the few decision-critical moments instead of improving after-the-fact trace review.
- **Direct competitor?** No (evidence)
- **Type:** Academic

### D8. Cocoa: Co-Planning and Co-Execution with AI Agents
- **Year:** 2024 preprint; CHI 2026 (arXiv:2412.10999, v4)
- **Authors / affiliation:** K. J. Kevin Feng, Kevin Pu, Matt Latzke, Tal August, Pao Siangliulue, Jonathan Bragg, Daniel S. Weld, Amy X. Zhang, Joseph Chee Chang (UW, AI2, U Toronto, UIUC)
- **URL:** https://arxiv.org/abs/2412.10999
- **What it does / finds:** "Interactive plans" in a notebook-like document. Each step is assigned to the agent or the user, and planning and execution interleave. A lab study (n=16) found better steerability with no loss of ease of use compared with a chat baseline, and a field deployment followed (n=7).
- **Overlap:** Human involvement placed at plan-step granularity, which is where natural breakpoints fall.
- **What AgentPause does differently:** Decides automatically, at runtime, which steps need the human, rather than having the user assign them up front.
- **Direct competitor?** Partial
- **Type:** Both

### D9. Plan-Then-Execute: An Empirical Study of User Trust and Team Performance When Using LLM Agents As A Daily Assistant
- **Year:** 2025 (CHI '25)
- **Authors / affiliation:** Gaole He, Gianluca Demartini, Ujwal Gadiraju (TU Delft; University of Queensland)
- **URL:** https://doi.org/10.1145/3706598.3713218 ; https://arxiv.org/abs/2502.01390 ; data: https://data.4tu.nl/datasets/d34aa48b-9722-4ad4-b108-a62878c1feca
- **What it does / finds:** n=248 across six everyday tasks of varying risk (for example, flight booking and credit-card payment) with step-wise planning and execution. LLM agents are a "double-edged sword." Outcomes are good with high-quality plans and *necessary* user involvement during execution, but users readily mistrust, or over-trust, plausible-looking plans.
- **Overlap:** User involvement in plan and execution, studied across risk levels.
- **What AgentPause does differently:** Makes user involvement *selective* (only "necessary" involvement) and calibrated by risk.
- **Direct competitor?** No (evidence)
- **Type:** Academic (plus released data and code)

### D10. Interactive Debugging and Steering of Multi-Agent AI Systems (AGDebugger)
- **Year:** 2025 (CHI '25; arXiv:2503.02068)
- **Authors / affiliation:** Will Epperson et al. (CMU and Microsoft Research)
- **URL:** https://arxiv.org/abs/2503.02068
- **What it does / finds:** A developer tool to pause multi-agent runs, inject or edit messages, reset to earlier states and step through the queue. A user study (n=14) found that interactive message resets were central to steering.
- **Overlap:** Mid-execution pause and steer.
- **What AgentPause does differently:** Targets end users and decides automatically when to pause.
- **Direct competitor?** No
- **Type:** Both

### D11. WaitGPT: Monitoring and Steering Conversational LLM Agent in Data Analysis with On-the-Fly Code Visualization
- **Year:** 2024 (UIST '24)
- **Authors / affiliation:** Liwenhan Xie, Chengbo Zheng, Haijun Xia, Huamin Qu, Chen Zhu-Tian (HKUST, UCSD, University of Minnesota)
- **URL:** https://doi.org/10.1145/3654777.3676374 ; https://arxiv.org/abs/2408.01703
- **What it does / finds:** Visualizes agent-generated data operations step by step as they are generated, so users can verify and modify them mid-stream. It improved error detection and confidence (n=12).
- **Overlap / AgentPause difference:** A monitoring and steering UI. AgentPause is a policy deciding when to demand attention.
- **Direct competitor?** No
- **Type:** Both

### D12. Plover / Sidekick / Unintended Consequences / InterruptBench / OpenClaw values (supporting 2026 work)
- **Plover: Steering GUI Agents through Plan-Centric Interaction** (2026, Venkatesan, Wen, Guo, Ono, Ren, Liu; https://arxiv.org/abs/2607.15193). Plans and replans are made persistent and editable, with localized interventions that preserve progress. Its formative study found that users want controls to pause and intervene. *Partial overlap (steering UI); not a competitor. Academic plus system.*
- **Sidekick: Designing Communication for Effective Multitasking with Computer Use Agents** (2026, Ruei-Che Chang, Wenqian Xu, Dingzeyu Li, Bryan Wang, Anhong Guo; https://arxiv.org/abs/2607.17527). Three-stage feedback: **ambient cues while the agent runs in the background, multimodal summaries when the user returns**, and explanations in the foreground. With n=30, it improved multitasking performance, progress awareness and error tracing compared with chat-text or ambient-only baselines. *Directly informs how AgentPause should present DEFERred items and re-entry summaries. No (design input). Academic plus prototype.*
- **Characterizing Unintended Consequences of GUI Agents for Web Browsing** (CHI '26; Shuning Zhang, Jingruo Chen, Zhiqi Gao, Jiajing Gao, Xin Yi, Hewu Li; Tsinghua, Cornell, Nankai, Zhongguancun Lab; https://doi.org/10.1145/3772318.3790696 ; arXiv:2505.09875). Drawing on 221 social-media posts and 14 interviews, agents misread instructions, mis-plan, mis-click and mishandle errors, leading to unanticipated actions, privacy and security harms, and eroded trust. Users mitigate with manual oversight. *Motivating evidence. No.*
- **When Users Change Their Mind: Evaluating Interruptible Agents in Long-Horizon Web Navigation (InterruptBench)** (2026, Henry Peng Zou et al.; https://arxiv.org/abs/2604.00892). A benchmark of user-initiated interruptions (adding a requirement, revising a goal, retracting a request) on WebArena-Lite. Strong LLMs still handle mid-task intent changes poorly. *The reverse direction (human interrupts agent); relevant to AgentPause's "resume after CLARIFY." No.*
- **Value-Sensitive Delegation in Everyday AI Agent Use: Evidence from OpenClaw** (2026, Renkai Ma, Ruyuan Wan, Xuan Lu, Fan Yang, Chen Chen, Lingyao Li; https://arxiv.org/abs/2609.22067). An analysis of 73,093 Reddit posts. Values were mostly *unmet when users described supervising* the agent (all six value groups), and users care about operating conditions (bounded reach, reviewability, cost). *Evidence that supervision UX is the pain point. No.*

### D13. Autonomy Reshapes How Personalization Affects Privacy Concerns and Trust in LLM Agents
- **Year:** 2026 (COLM 2026; arXiv:2510.04465)
- **Authors / affiliation:** Zhiping Zhang, Yi Evie Zhang, Freda Shi, Tianshi Li (affiliations not verified; Li's group is at Northeastern per D2)
- **URL:** https://arxiv.org/abs/2510.04465
- **What it does / finds:** A 3×3 between-subjects experiment (N=450) crossing autonomy level with personalization. **Risk-contingent autonomy**, where the agent hands control back when it detects potential privacy leakage, raised **perceived control**, which buffered the negative effects of personalization on privacy concern and trust. Secondary sources report that this yielded *more* perceived control than a no-autonomy agent despite less direct oversight, and that constant approvals cause decision fatigue. The authors argue for "autonomy alignment" and say perceived control is necessary but not sufficient: users must also be able to exercise control effectively.
- **Overlap:** Direct evidence for the AgentPause hypothesis: context-contingent hand-back can preserve agency better than always-ask.
- **What AgentPause does differently:** Generalizes beyond privacy to multiple risk and context signals and timing, measures objective oversight effectiveness as well as perceived control, and adds explanations.
- **Direct competitor?** Partial. A one-signal version of the idea, as an experiment rather than a system.
- **Type:** Academic

### D14. Anthropic: "Measuring AI agent autonomy in practice" and "How we built Claude Code auto mode"
- **Year:** 2026 (Feb 18 and Mar 25, 2026)
- **Authors / affiliation:** Miles McCain, Thomas Millar, Saffron Huang, … Deep Ganguli (Anthropic); John Hughes et al. (Anthropic)
- **URL:** https://www.anthropic.com/research/measuring-agent-autonomy ; https://www.anthropic.com/engineering/claude-code-auto-mode
- **What it does / finds:** **Users approve 93% of Claude Code permission prompts**, which Anthropic calls "approval fatigue." Full auto-approve use rises from about 20% of sessions (fewer than 50 sessions of experience) to over 40% (750+ sessions). Experienced users also *interrupt* more (about 9% versus 5% of turns). On complex tasks the agent stops to ask for clarification more than twice as often as on simple ones. Its reasons for stopping: presenting a choice (35%), gathering diagnostics (21%) and clarifying vague requests (13%). Humans interrupt to add missing context or corrections (32%) or because the agent is slow (17%). Auto mode replaces prompts with tiers: (1) read-only allowlist, (2) in-project edits, (3) a two-stage transcript classifier for everything else. On real traffic the full pipeline had a 0.4% false-positive rate and **missed 17% of real "overeager" actions**. Its main failure is judging whether a past approval covers an action's full impact. The data are Anthropic's own and Claude-classified.
- **Overlap:** An industrial risk-tiered gate that replaces always-ask. It is real-world evidence of rubber-stamping and of the adaptive-gating trade-off.
- **What AgentPause does differently:** Uses user-state signals (load, progress, preferences), DEFER timing and explanations, and is evaluated on human agency rather than only on safety false-positive and false-negative rates. It also addresses "scope of prior approval" explicitly.
- **Direct competitor?** Partial (industry product feature)
- **Type:** Software artifact (plus industry research reports)

### D15. Reframing LLM Agent Security as an Agent–Human Interaction Problem
- **Year:** 2026 (arXiv:2605.24309)
- **Authors / affiliation:** Peiran Wang, Ying Li, Yuan Tian (affiliations not verified)
- **URL:** https://arxiv.org/abs/2605.24309
- **What it does / finds:** Reviews 59 papers, 21 production agent systems and 26 security plugins. Policy specification, **runtime approval** and scope configuration dominate in industry (14–16 of 21 systems), leaving users "caught between approval fatigue and uncontrolled agent autonomy." Academic proposals such as intent anchoring and trust labeling are not deployed. Calls for "agent–human interaction security" as a research area.
- **Overlap / AgentPause difference:** Positions AgentPause's problem in the security context. AgentPause is a concrete answer to the fatigue-versus-autonomy dilemma.
- **Direct competitor?** No (position/survey)
- **Type:** Academic

### D16. Options, Not Clicks: Lattice Refinement for Consent-Driven MCP Authorization (Conleash)
- **Year:** 2026 (arXiv:2605.11360)
- **Authors / affiliation:** Ying Li, Yanju Chen, Peiran Wang, Issac Khabra, Faysal Hossain Shezan, Yu Feng, Yuan Tian (affiliations not verified)
- **URL:** https://arxiv.org/abs/2605.11360
- **What it does / finds:** **Client-side middleware** for MCP tool calls. A **risk lattice** auto-permits calls within known safe boundaries and escalates risky ones, considering dangerous *arguments* rather than only tool names. It adds a policy engine for user invariants and a **refinement loop that turns user decisions into reusable scoped rules**. On 984 real traces it reached 98.2% accuracy and 99.4% escalation recall with 8.2 ms overhead. In a user study (n=16), people preferred scoped permissions, citing trust and fewer prompts. Pre-screening found only 3 of 16 participants read prompts carefully, and 13 of 16 used "Always Allow" just to dismiss prompts.
- **Overlap:** Architecturally the closest: a middleware between agent and environment that decides allow versus ask and learns from user decisions.
- **What AgentPause does differently:** Covers human-factors timing (breakpoints, load, interruption cost, DEFER), CLARIFY for intent ambiguity, and agent uncertainty, and is evaluated on agency. Conleash is a security and authorization system (allow/escalate) with no timing model.
- **Direct competitor?** **Yes (architecture-level)**, but with a security framing and no timing or agency.
- **Type:** Both

---

## E. Proactive assistance timing and agents asking for help

### E1. Need Help? Designing Proactive AI Assistants for Programming
- **Year:** 2025 (CHI '25; arXiv:2410.04596)
- **Authors / affiliation:** Valerie Chen, Alan Zhu, Sebastian Zhao, Hussein Mozannar, David Sontag, Ameet Talwalkar (CMU, MIT, Microsoft; per-author affiliations not re-verified)
- **URL:** https://arxiv.org/abs/2410.04596 ; https://www.microsoft.com/en-us/research/publication/need-help-designing-proactive-ai-assistants-for-programming/
- **What it does / finds:** Explicit timing rules for a proactive chat assistant: **no suggestions during active typing ("acceleration")**; after 5 s of idle time ("exploration"), at most once per 20 s, and dropped if the user resumes coding; **immediately after a run error** (debugging). Suggest (+18%) and Suggest+Preview (+12.1%) improved test cases passed over a non-proactive baseline. A **"Persistent Suggest"** condition (5 s wait, more suggestions) was preferred by only 47% of users, compared with 90% for Suggest, and was called "distracting" and "annoying." More frequent suggestions were less often used. Design considerations: efficient evaluation and dismissal, context relevance, learning from feedback, **timing based on context**, letting users decide when proactivity is on, and varying the amount of information.
- **Overlap:** Rule-based breakpoint timing for system-initiated LLM interventions, with evidence that over-frequent intervention backfires.
- **What AgentPause does differently:** Applies this to *gating agent actions* (where safety matters), not to offering suggestions, and learns timing rather than hard-coding idle thresholds.
- **Direct competitor?** Partial
- **Type:** Academic (plus prototype)

### E2. Assistance or Disruption? Exploring and Evaluating the Design and Trade-offs of Proactive AI Programming Support (Codellaborator)
- **Year:** 2025 (CHI '25)
- **Authors / affiliation:** Kevin Pu, Daniel Lazaro, Ian Arawjo, Haijun Xia, Ziang Xiao, Tovi Grossman, Yan Chen (U Toronto, Virginia Tech and others)
- **URL:** https://doi.org/10.1145/3706598.3713357 ; https://arxiv.org/abs/2502.18658
- **What it does / finds:** Within-subjects study (n=18) of prompt-only versus proactive agent versus proactive agent with **presence indicators and interaction context**. Proactivity improved efficiency but disrupted workflows. Presence indicators and context reduced disruption and improved awareness. There are tensions between control, ownership and code understanding, and proactivity should adapt to the stage of the programming process.
- **Overlap:** The disruption cost of system-initiated agent behavior, mitigated by awareness cues.
- **What AgentPause does differently:** Adds stage-aware timing and ambient presence cues for DEFERred items.
- **Direct competitor?** Partial
- **Type:** Both

### E3. Proactive Conversational Agents with Inner Thoughts
- **Year:** 2025 (CHI '25; arXiv:2501.00383)
- **Authors / affiliation:** Xingyu Bruce Liu, Shitao Fang, Weiyan Shi, Chien-Sheng Wu, Takeo Igarashi, Xiang "Anthony" Chen (affiliations not re-verified)
- **URL:** https://doi.org/10.1145/3706598.3713760 ; https://arxiv.org/abs/2501.00383
- **What it does / finds:** Rather than predicting turn-taking, the agent keeps a covert stream of "inner thoughts" and models its **intrinsic motivation** to voice each one, speaking only when motivation is high enough and the moment fits. Heuristics come from a formative study (n=24) of when people speak or hold back. It beat baselines on turn-taking appropriateness, coherence, intelligence and anthropomorphism.
- **Overlap:** A learned "is it worth interrupting now?" score combining the value of the contribution with conversational timing.
- **What AgentPause does differently:** Its interventions are approval and safety gates rather than conversational contributions, with explicit consequence signals.
- **Direct competitor?** No (analogous mechanism)
- **Type:** Both (open-source implementations)

### E4. ProMemAssist: Exploring Timely Proactive Assistance Through Working Memory Modeling in Multi-Modal Wearable Devices
- **Year:** 2025 (UIST '25)
- **Authors / affiliation:** Kevin Pu, Ting Zhang, Naveen Sendhilnathan, Sebastian Freitag, Raj Sodhi, Tanya R. Jonker (U Toronto; Meta Reality Labs)
- **URL:** https://doi.org/10.1145/3746059.3747770 ; https://arxiv.org/abs/2507.21378
- **What it does / finds:** Models the user's **working memory** in real time (items, displacement, interference) and uses a timing predictor that **weighs the value of an intervention against its disruption cost**. Compared with an LLM baseline (n=12), it gave more selective help and drew more engagement.
- **Overlap:** An explicit value-versus-interruption-cost timing model grounded in a cognitive-load model. This is AgentPause's "cognitive load" plus "interruption cost" signals.
- **What AgentPause does differently:** Domain is agent action oversight, and it adds risk and reversibility, which can override the load-based timing.
- **Direct competitor?** Partial (mechanism-level)
- **Type:** Both

### E5. When to Show a Suggestion? Integrating Human Feedback in AI-Assisted Programming
- **Year:** 2024 (AAAI-24; arXiv:2306.04930)
- **Authors / affiliation:** Hussein Mozannar, Gagan Bansal, Adam Fourney, Eric Horvitz (MIT; Microsoft Research)
- **URL:** https://doi.org/10.1609/aaai.v38i9.28878 ; https://arxiv.org/abs/2306.04930
- **What it does / finds:** CDHF learns from accept/reject telemetry of 535 programmers to *hide* suggestions likely to be rejected, reducing verification time and latency in a retrospective evaluation. It warns that **optimizing acceptance as the reward can degrade quality**.
- **Overlap:** Learning from the user's decision history to suppress unnecessary interventions.
- **What AgentPause does differently:** Should *not* optimize "user approved" as its objective, because approvals are noisy and rubber-stamped (see F-series). It needs outcome-based or normative labels.
- **Direct competitor?** Partial
- **Type:** Academic

### E6. ProAgentBench: Evaluating LLM Agents for Proactive Assistance with Real-World Data
- **Year:** 2026 (arXiv:2602.04482)
- **Authors / affiliation:** Yuanbo Tang, Huaze Tang, Tingyu Cao, Lam Nguyen, Anping Zhang, Xinwen Cao, Chunkang Liu, Wenbo Ding, Yang Li (affiliations not verified)
- **URL:** https://arxiv.org/abs/2602.04482
- **What it does / finds:** Splits proactivity into **when to intervene** and **what to say**. It provides 28,000+ events from more than 500 h of real sessions. Long-term memory and historical context improve timing prediction, and real data beats synthetic.
- **Overlap / AgentPause difference:** A possible benchmark and data source for the timing component. Its domain is assistance, not gating.
- **Direct competitor?** No
- **Type:** Both (dataset)

### E7. Robots That Ask For Help: Uncertainty Alignment for LLM Planners (KnowNo)
- **Year:** 2023 (CoRL 2023, oral; arXiv:2307.01928)
- **Authors / affiliation:** Allen Z. Ren, Anushri Dixit, Alexandra Bodrova, Sumeet Singh, Stephen Tu, Noah Brown, Peng Xu, Leila Takayama, Fei Xia, Jake Varley, Zhenjia Xu, Dorsa Sadigh, Andy Zeng, Anirudha Majumdar (Princeton, Google DeepMind)
- **URL:** https://arxiv.org/abs/2307.01928
- **What it does / finds:** Uses conformal prediction over LLM plan options. If the prediction set has more than one option, the robot **asks for help**. This gives statistical task-success guarantees while minimizing help requests.
- **Overlap:** A principled agent-uncertainty to CLARIFY trigger.
- **What AgentPause does differently:** Uncertainty is one signal among many. AgentPause adds severity, reversibility, human state and timing.
- **Direct competitor?** Partial (for the uncertainty/CLARIFY component)
- **Type:** Academic

### E8. Robot, asker of questions (collaborative control)
- **Year:** 2003 (Robotics and Autonomous Systems 42(3–4))
- **Authors / affiliation:** Terrence Fong, Charles Thorpe, Charles Baur (CMU Robotics Institute; EPFL)
- **URL:** https://doi.org/10.1016/S0921-8890(02)00378-0
- **What it does / finds:** "Collaborative control" teleoperation, in which the robot treats the human as a resource and asks questions through dialogue, adapting to the human's availability and expertise. (Content note: from knowledge of the paper; DOI verified.)
- **Overlap / AgentPause difference:** An early "agent asks the human" architecture. AgentPause adds risk-aware timing and explanations.
- **Direct competitor?** No
- **Type:** Academic

---

## F. Confirmation, consent and warning fatigue, habituation and rubber-stamping

### F1. You've Been Warned: An Empirical Study of the Effectiveness of Web Browser Phishing Warnings
- **Year:** 2008 (CHI '08)
- **Authors / affiliation:** Serge Egelman, Lorrie Faith Cranor, Jason Hong, Carnegie Mellon University
- **URL:** https://doi.org/10.1145/1357054.1357219
- **What it does / finds:** **Active** (interruptive, blocking) warnings were far more effective than **passive** ones. My recollection of the abstract is that 79% heeded active warnings while only one participant heeded passive ones, but these numbers were not re-fetched. Habituation to look-alike dialogs reduced effectiveness. (Content note: title, authors and venue verified via DOI; figures from knowledge of the abstract.)
- **Overlap:** When an intervention is truly needed it should be active and blocking, and the rest should be passive. This maps to BLOCK/ASK_HUMAN versus CONTINUE with a notice.
- **Direct competitor?** No
- **Type:** Academic

### F2. Trained to Accept? A Field Experiment on Consent Dialogs
- **Year:** 2010 (CHI '10)
- **Authors / affiliation:** Rainer Böhme, Stefan Köpsell (affiliations not verified)
- **URL:** https://doi.org/10.1145/1753326.1753689
- **What it does / finds:** A large field experiment showing that users are conditioned to click "accept" on dialogs resembling familiar consent/EULA dialogs. Habituated dialog designs lead to more acceptance regardless of content. (Content note: from knowledge of the paper; DOI verified.)
- **Overlap / AgentPause difference:** Uniform approve/deny modals train rubber-stamping. AgentPause should vary form with severity and keep prompts rare.
- **Direct competitor?** No
- **Type:** Academic

### F3. How to Ask for Permission
- **Year:** 2012 (USENIX HotSec '12)
- **Authors / affiliation:** Adrienne Porter Felt, Serge Egelman, Matthew Finifter, Devdatta Akhawe, David Wagner, UC Berkeley
- **URL:** https://www.usenix.org/conference/hotsec12/workshop-program/presentation/felt
- **What it does / finds:** Guidelines for choosing *which* permission-granting mechanism to use for a given permission (for example automatic grant, trusted UI, runtime confirmation, install-time), so that warnings are kept for cases that need them. Applying the guidelines would reduce the number of warnings and therefore habituation.
- **Overlap:** A rule-based precursor to AgentPause's mapping from action type to intervention type.
- **What AgentPause does differently:** Makes the mapping context-dependent and adaptive at runtime.
- **Direct competitor?** No (design precursor)
- **Type:** Academic

### F4. Alice in Warningland: A Large-Scale Field Study of Browser Security Warning Effectiveness
- **Year:** 2013 (USENIX Security '13)
- **Authors / affiliation:** Devdatta Akhawe (UC Berkeley), Adrienne Porter Felt (Google)
- **URL:** https://www.usenix.org/conference/usenixsecurity13/technical-sessions/presentation/akhawe
- **What it does / finds:** Telemetry from more than 25 million warning impressions. Clickthrough was about 10% (Firefox malware/phishing), about 25% (Chrome malware/phishing), about 33% (Firefox SSL) and **70.2% (Chrome SSL)**. Warnings can work, and their UX strongly affects behavior. High clickthrough probably reflects fatigue and false positives.
- **Overlap / AgentPause difference:** The false-positive rate of interventions drives clickthrough. AgentPause's precision on "needs human" directly affects whether humans heed it.
- **Direct competitor?** No
- **Type:** Academic

### F5. Bravo-Lillo et al.: "Your Attention Please" (SOUPS '13) and "Harder to Ignore? Revisiting Pop-Up Fatigue and Approaches to Prevent It" (SOUPS '14)
- **Year:** 2013, 2014
- **Authors / affiliation:** Cristian Bravo-Lillo, Saranga Komanduri, Lorrie Faith Cranor, Robert W. Reeder, Manya Sleeper, Julie Downs, Stuart Schechter (CMU; Microsoft Research)
- **URL:** https://doi.org/10.1145/2501604.2501610 ; https://www.usenix.org/conference/soups2014/proceedings/presentation/bravo-lillo
- **What it does / finds:** Habituation to pop-ups cut the share of users who noticed a changed, security-critical field by roughly 3×. **Attractors** that delay dismissal helped. Attractors that **force interaction with the critical field** removed the effect of habituation.
- **Overlap:** Concrete dialog techniques for the rare high-stakes ASK_HUMAN, such as requiring the user to type or select the critical value (recipient, amount, path).
- **Direct competitor?** No (design input)
- **Type:** Academic

### F6. Habituation to warnings: polymorphic warnings (CHI '15), habituation over time (CHI '17), longitudinal fMRI and field (MISQ '18)
- **Year:** 2015, 2017, 2018
- **Authors / affiliation:** Bonnie Brinton Anderson, C. Brock Kirwan, Jeffrey L. Jenkins, David Eargle, Seth Howard, Anthony Vance, Daniel Bjornn (Brigham Young University and others)
- **URL:** https://doi.org/10.1145/2702123.2702322 ; https://doi.org/10.1145/3025453.3025896 ; https://doi.org/10.25300/MISQ/2018/14124
- **What it does / finds:** Neural and behavioral responses to warnings drop sharply with repeated exposure. **Polymorphic** warnings (which vary in appearance) slow habituation, and habituation partially recovers after rest. (Content note: from knowledge of the papers; DOIs verified.)
- **Overlap / AgentPause difference:** Repeated identical approval dialogs habituate users. AgentPause should ration prompts and vary their form by risk.
- **Direct competitor?** No
- **Type:** Academic

### F7. A Design Space for Effective Privacy Notices
- **Year:** 2015 (SOUPS '15)
- **Authors / affiliation:** Florian Schaub, Rebecca Balebako, Adam L. Durity, Lorrie Faith Cranor, Carnegie Mellon University
- **URL:** https://www.usenix.org/conference/soups2015/proceedings/presentation/schaub
- **What it does / finds:** A design space with dimensions for timing, channel, modality and control. **Timing options are at setup, just in time, context-dependent, periodic, persistent and on demand.**
- **Overlap:** A vocabulary for AgentPause's timing outputs: ASK_HUMAN is just-in-time, DEFER is context-dependent or periodic, a summary is on demand, and pre-task preference elicitation happens at setup.
- **Direct competitor?** No
- **Type:** Academic

### F8. The Feasibility of Dynamically Granted Permissions: Aligning Mobile Privacy with User Preferences
- **Year:** 2017 (IEEE S&P '17)
- **Authors / affiliation:** Primal Wijesekera, Arjun Baokar, Lynn Tsai, Joel Reardon, Serge Egelman, David Wagner, Konstantin Beznosov (UBC; UC Berkeley/ICSI)
- **URL:** https://doi.org/10.1109/SP.2017.51
- **What it does / finds:** A 131-person field study showing that permission decisions are contextual. A classifier infers preferences from **past decisions and behavior**, auto-grants or auto-denies, and **prompts only when uncertain**. It predicted decisions with 96.8% accuracy, a fourfold error reduction compared with ask-on-first-use.
- **Overlap:** The same idea as AgentPause's "history of user decisions" plus "ask only when uncertain about the *user's* preference." Evidence that prompting adaptively from history beats a fixed strategy.
- **What AgentPause does differently:** Covers agent actions with severity and reversibility, and adds timing (DEFER) and explanations.
- **Direct competitor?** Partial (mobile-permission analogue)
- **Type:** Academic

### F9. Effects of workload, work complexity, and repeated alerts on alert fatigue in a clinical decision support system
- **Year:** 2017 (BMC Medical Informatics and Decision Making 17:36)
- **Authors / affiliation:** Jessica S. Ancker, Alison Edwards, Sarah Nosal, Diane Hauser, Elizabeth Mauer, Rainu Kaushal (Weill Cornell Medicine and others)
- **URL:** https://doi.org/10.1186/s12911-017-0430-8
- **What it does / finds:** Clinicians' acceptance of alerts declined as the number of alerts and especially **repeated alerts** grew. This is evidence that alert fatigue is driven by volume and repetition more than by workload alone. (Content note: from knowledge of the paper; DOI verified.)
- **Overlap / AgentPause difference:** De-duplicate and batch repeated agent questions rather than re-asking.
- **Direct competitor?** No
- **Type:** Academic

### F10. To Trust or to Think: Cognitive Forcing Functions Can Reduce Overreliance on AI
- **Year:** 2021 (PACM HCI / CSCW 2021)
- **Authors / affiliation:** Zana Buçinca, Maja Barbara Malaya, Krzysztof Z. Gajos, Harvard University
- **URL:** https://doi.org/10.1145/3449287
- **What it does / finds:** Cognitive forcing (for example, asking the user to decide before seeing the AI's recommendation, or adding wait time) reduced over-reliance compared with simple explanations. It was rated less favorably, and helped people high in need for cognition more. (Content note: from knowledge of the paper; DOI verified.)
- **Overlap / AgentPause difference:** For high-severity ASK_HUMAN, add deliberate friction (for example, "what do you expect this action to do?") to prevent rubber-stamping, used sparingly because it costs satisfaction.
- **Direct competitor?** No
- **Type:** Academic

### F11. "I'm Not Sure, But...": Examining the Impact of LLMs' Uncertainty Expression on User Reliance and Trust
- **Year:** 2024 (FAccT '24)
- **Authors / affiliation:** Sunnie S. Y. Kim, Q. Vera Liao, Mihaela Vorvoreanu, Stephanie Ballard, Jennifer Wortman Vaughan (Princeton; Microsoft Research)
- **URL:** https://doi.org/10.1145/3630106.3658941
- **What it does / finds:** First-person natural-language uncertainty expressions reduced over-reliance on incorrect LLM answers and somewhat lowered trust and confidence, without much reduction in reliance on correct answers. (Content note: from knowledge of the paper; DOI verified.)
- **Overlap / AgentPause difference:** Phrasing for CLARIFY and ASK_HUMAN explanations ("I'm not sure which account you meant…").
- **Direct competitor?** No
- **Type:** Academic

---

## G. Sense of agency and perceived control (measurement)

### G1. "I did that!" Measuring users' experience of agency in their own actions
- **Year:** 2012 (CHI '12)
- **Authors / affiliation:** David Coyle, James Moore, Per Ola Kristensson, Paul Fletcher, Alan Blackwell (University of Cambridge)
- **URL:** https://doi.org/10.1145/2207676.2208350
- **What it does / finds:** Brings the **intentional binding** paradigm (perceived compression of time between action and outcome) into HCI as an implicit measure of sense of agency, and shows that input modality changes it. (Content note: from knowledge of the paper; DOI verified.)
- **Overlap:** An implicit agency measure for AgentPause studies, to complement questionnaires.
- **Direct competitor?** No
- **Type:** Academic

### G2. The experience of agency in human–computer interactions: a review
- **Year:** 2014 (Frontiers in Human Neuroscience 8:643)
- **Authors / affiliation:** Hannah Limerick, David Coyle, James W. Moore
- **URL:** https://doi.org/10.3389/fnhum.2014.00643
- **What it does / finds:** Reviews explicit (self-report) and implicit (intentional binding, sensory attenuation) measures of sense of agency and their relevance to HCI, including automation and intelligent systems.
- **Overlap:** Methodological grounding for "preserve or improve human agency."
- **Direct competitor?** No
- **Type:** Academic

### G3. Automation Technology and Sense of Control: A Window on Human Agency
- **Year:** 2012 (PLoS ONE 7(3): e34075)
- **Authors / affiliation:** Bruno Berberian (ONERA), Jean-Christophe Sarrazin, Patrick Le Blaye, Patrick Haggard (UCL)
- **URL:** https://doi.org/10.1371/journal.pone.0034075
- **What it does / finds:** In an aircraft conflict-avoidance supervision task with autopilot levels based on the Sheridan–Verplank scale, intentional binding tracked the level of automation. Secondary sources report that **sense of agency decreases as automation increases**, and implicit measures correlated with explicit agency judgments.
- **Overlap:** The central tension in AgentPause's hypothesis (automation lowers agency), plus a validated paradigm for measuring it in supervisory control.
- **What AgentPause does differently:** Tests whether *well-timed, selective* involvement can keep agency high at high automation.
- **Direct competitor?** No
- **Type:** Academic

### G4. The Sense of Agency Scale (SoAS)
- **Year:** 2017 (Frontiers in Psychology 8:1552)
- **Authors / affiliation:** Adam Tapal, Ela Oren, Reuven Dar, Baruch Eitam
- **URL:** https://doi.org/10.3389/fpsyg.2017.01552
- **What it does / finds:** A 13-item questionnaire on general, consciously perceived control (positive and negative agency subscales). (Content note: item count and subscales from knowledge of the paper; DOI verified.) Note that it measures *trait-level* agency, so state- and task-level items need adapting.
- **Overlap:** A candidate trait covariate and item source for AgentPause studies.
- **Direct competitor?** No
- **Type:** Academic

### G5. How does HCI Understand Human Agency and Autonomy?
- **Year:** 2023 (CHI '23)
- **Authors / affiliation:** Dan Bennett, Oussama Metatla, Anne Roudaut, Elisa D. Mekler
- **URL:** https://doi.org/10.1145/3544548.3580651
- **What it does / finds:** A review of how HCI uses "agency" and "autonomy," distinguishing dimensions such as self-causality (the experience of causing outcomes) from self-determination (acting on one's own values), across time scales. It cautions against conflating them. (Content note: dimensions from knowledge of the paper; DOI verified.)
- **Overlap:** AgentPause must specify *which* agency it preserves: moment-to-moment control over actions versus whether outcomes match the user's goals and values. It should measure both.
- **Direct competitor?** No
- **Type:** Academic

### G6. The AI Ghostwriter Effect
- **Year:** 2024 (ACM TOCHI 31(2))
- **Authors / affiliation:** Fiona Draxler, Anna Werner, Florian Lehmann, Matthias Hoppe, Albrecht Schmidt, Daniel Buschek, Robin Welsch (LMU Munich and others)
- **URL:** https://doi.org/10.1145/3637875
- **What it does / finds:** Users did not perceive ownership of AI-generated text yet still declared themselves authors. Perceived ownership and authorship diverge. (Content note: from title and knowledge of the paper.)
- **Overlap / AgentPause difference:** Measure perceived ownership and responsibility for agent outcomes alongside control.
- **Direct competitor?** No
- **Type:** Academic

### G7. HumanAgencyBench: Scalable Evaluation of Human Agency Support in AI Assistants
- **Year:** 2025 preprint; EMNLP 2026 Findings (arXiv:2509.08494)
- **Authors / affiliation:** Benjamin Sturgeon, Daniel Samuelson, Jacob Haimes, Jacy Reese Anthis (affiliations not verified)
- **URL:** https://arxiv.org/abs/2509.08494
- **What it does / finds:** An LLM-simulated, LLM-judged benchmark of six agency-supporting behaviors: **Ask Clarifying Questions**, Avoid Value Manipulation, Correct Misinformation, **Defer Important Decisions**, Encourage Learning and Maintain Social Boundaries. Agency support is low to moderate across assistants and does not reliably improve with capability or RLHF.
- **Overlap:** Two of the six dimensions are exactly AgentPause's CLARIFY and ASK_HUMAN/DEFER outputs.
- **What AgentPause does differently:** Enforces these behaviors externally as middleware instead of hoping the model shows them. Could serve as an offline evaluation.
- **Direct competitor?** No
- **Type:** Both (benchmark)

### G8. User Autonomy in Human-LLM Interaction: A Scoping Review
- **Year:** 2026 (CHI EA '26)
- **Authors / affiliation:** Yumeng Wang, Ge Wang (affiliations not verified)
- **URL:** https://doi.org/10.1145/3772363.3798855
- **What it does / finds:** Finds that frameworks often equate user autonomy with the level of agent automation. It identifies **steerability** (prioritizing user control over automated convenience) as a design theme. (Content note: from search-result excerpts.)
- **Overlap / AgentPause difference:** Positions AgentPause in this literature. AgentPause separates user autonomy from the agent's automation level.
- **Direct competitor?** No
- **Type:** Academic

---

## Closest competitors and key takeaways

**Closest competitors (ranked):**
1. **Zhou et al., CHI '26 (D1)**: adaptive, decision-theoretic placement of confirmations for multi-step agents, evaluated against confirm-at-end (81% preference, −13.5% time). *This is the nearest prior art to the AgentPause hypothesis.* Its gaps: a single error-probability signal; time is the only objective (it explicitly ignores safety and money costs); no CLARIFY, DEFER or BLOCK; fixed per-domain parameters with no per-user adaptation; simulated agents; no always-ask or never-ask baseline; no agency measure.
2. **Huq et al., 2026, CowCorpus/PlowPilot (D3)**: learns when a user *would* intervene and asks only then. Gaps: descriptive rather than normative (users miss risky steps), binary ask/continue, a very small user study, no explicit risk or load signals.
3. **Chen et al., 2026, Comparing Human Oversight Strategies for CUAs (D2)**: the strongest empirical evidence that fixed strategies fail. Users blocked only 21% of problematic actions, and 56% of failures involved a timing mismatch. It explicitly calls for adaptive oversight aligned to decision-critical moments, so it is the natural baseline set and protocol for AgentPause.
4. **Conleash (D16)**: the same middleware architecture (agent → middleware → environment; allow/escalate; learns rules from user decisions) in a security and MCP framing. It has no timing, cognitive-load or agency component.
5. **Magentic-UI action guards (D6)** and **Claude Code auto mode (D14)**: deployed risk-gating (irreversibility labels plus an LLM judge; tiered allowlist plus classifier). They are the de facto industrial baselines for "adaptive-ish" gating, with documented approval fatigue (93% approval rate) and residual misses (17% of overeager actions).
6. **Zhang et al., COLM '26 (D13)**: risk-contingent hand-back raises perceived control. This is direct evidence for the agency half of the hypothesis, but it covers one signal (privacy) and is not a system.
7. **Conceptual ancestors:** Horvitz '99 (act/dialog/no-action thresholds), Horvitz et al. '03–'04 (cost of interruption versus cost of delay; BusyBody), and Feng et al. '25 (autonomy levels L1–L4; rubber-stamping risk at L4).

**Key takeaways:**
- **(a) Breakpoints reduce interruption cost (justifies the task-progress/breakpoint signal and DEFER).** Adamczyk & Bailey '04, Iqbal & Bailey '05/'06/'08 and Bailey & Konstan '06 show that interruptions at (coarse) task boundaries reduce resumption lag, annoyance and frustration, and that deferring notifications to breakpoints lowers frustration and reaction time. Salvucci & Bogunovich '10 show users who *can* defer will do so to low-workload moments 94% of the time. McFarlane '02 found negotiated (user-chosen-timing) coordination best overall. Mark et al. '08 show costs are largely stress and workload rather than time. For agents, Zhou et al. find early checkpoints pay off most (−29% on early errors) while late checks can cost time, and Need Help? (CHI '25) suppresses help during active typing.
- **(b) Adaptive confirmation timing for LLM agents has begun to be studied (2025–2026), but the full AgentPause comparison has not been done.** Zhou et al. compare adaptive versus confirm-at-end. Chen et al. compare four fixed or risk-gated strategies. Huq et al. compare learned asking against CowPilot. Magentic-UI and Claude Code use risk tiers. **No study found compares always-ask vs. never-ask vs. adaptive *with a multi-signal policy* (uncertainty + severity + reversibility + ambiguity + progress + load + preferences + history) on *both* unnecessary interruptions *and* human agency (perceived control plus objective oversight effectiveness).** That is AgentPause's open niche.
- **Fixed human-in-the-loop strategies fail in two ways.** Always-ask leads to habituation and rubber-stamping: 93% approval in Claude Code, 13 of 16 users using "Always Allow" to dismiss prompts, warning clickthrough of up to 70% (Chrome SSL), and roughly 3× lower noticing after habituation. Confirm-at-end or never-ask leads to error cascades and costly redo (Zhou et al.), and users miss problematic actions anyway (21% blocked).
- **User-initiated intervention is not a safety mechanism.** Users intervene mostly over slowness (Kim et al. CHI '26) or missing context (Anthropic), and check procedural correctness rather than whether the action is appropriate (Chen et al.). Therefore AgentPause's **normative** signals (severity, reversibility) must be able to override **descriptive** predictions of what users would do (Huq et al.).
- **Do not train on approvals as ground truth.** Optimizing acceptance degrades quality (Mozannar et al. AAAI '24). Approvals are noisy because of rubber-stamping, so use outcome-based or expert labels and treat an extreme approval rate as a fatigue signal.

---

## Design implications for AgentPause

1. **Decision policy shape.** Keep Horvitz's expected-utility framing, with thresholds between CONTINUE, CLARIFY and ASK_HUMAN. Add DEFER as "expected cost of delayed review < cost of interrupting now, and the agent can safely continue or hold" (Horvitz et al. '03). Make BLOCK a hard gate for irreversible, high-severity actions taken under high uncertainty. Severity and reversibility act as *overrides* on timing: you may defer a question about a reversible preference, but never one about an imminent irreversible step (Chen et al. temporal alignment; Iqbal & Bailey relevance → breakpoint type).
2. **Timing.** Ask *before* the consequential state change, not after the data has been typed (Chen et al.). Prefer plan-step boundaries (coarse breakpoints) for non-urgent questions. Suppress interventions while the user is actively typing or working (Need Help?). Bundle multiple deferred questions into one interruption (Magentic-UI users asked for this). Give a short pre-alert ("I'll need your call on X in about 2 steps") to support goal encoding (Trafton et al. '03; McFarlane's negotiated mode).
3. **Rationing as a design goal.** Track a per-user interruption budget and approval-rate statistics. Repeated identical prompts and near-100% approval rates are signals of habituation or rubber-stamping (Anthropic 93%; Ancker '17; Vance '18). Turn repeated user decisions into *scoped, renewable* rules ("allow X on site Y for this task"), make the scope explicit, and re-ask when the scope changes (Conleash; Chen et al.; Wijesekera '17 "prompt only when uncertain").
4. **What the intervention dialog should show** (Chen et al. re-entry scaffolding; Zhou et al. checkpoint UI; SAT levels; Amershi G11/G16; Bansal et al. A2/A4/X3):
   - The user's original goal and where the agent is in the plan (progress, step k of n).
   - How the agent got here: a compact trace of the actions since the last human touchpoint, with screenshots on demand.
   - **The concrete consequence** ("will send $412 to …", "will disclose your health ID to …"), not just a risk label. Say whether it is reversible and how.
   - **Why it is asking** (which signal fired: uncertainty, ambiguity, severity, irreversibility), with first-person uncertainty phrasing (Kim et al. FAccT '24).
   - **What the approval authorizes**: scope and duration (this action, this site, this task).
   - More than two options: approve / reject / **edit or take over** / **defer** / "ask me later about this type" (Magentic-UI users wanted a third option; CowPilot-style takeover).
5. **Friction proportional to stakes.** For low-severity items use non-modal, passive notices (CONTINUE plus log). For high-severity items use active, blocking dialogs (Egelman '08) with attractors that force interaction with the critical field, such as confirming the amount or recipient (Bravo-Lillo '13/'14). Use optional cognitive forcing ("what do you expect will happen?"; Buçinca '21). Vary the dialog's appearance by risk class to slow habituation (Anderson '15).
6. **DEFER presentation.** Show ambient presence and status cues while the agent works in the background, and a summary when the user returns (Sidekick '26; Pu et al. CHI '25 presence indicators). Show progress and ETA, so that users don't interrupt out of impatience (Kim et al. CHI '26).
7. **User control over the policy itself.** Offer global controls and user-tunable approval conditions (Amershi G17; Feng et al. L4), let the user switch proactivity on or off (Need Help?), and elicit delegation preferences at setup (Schaub et al. "at setup" timing; Lubars & Tan).
8. **Evaluation protocol.**
   - Baselines: always-ask (per-action confirmation), never-ask, confirm-at-end, and risk-gated (Operator- or Magentic-UI-style), as in Chen et al. D2.
   - Embed problematic actions to measure block rate and timing mismatch (D2).
   - Measure the number of interruptions and the "unnecessary" rate, completion time, and redo and diagnosis time (D1).
   - Measure workload (NASA-TLX) and stress (Mark '08).
   - Measure trust calibration (Lee & See).
   - Measure **agency**: an explicit state-level sense of agency or perceived control (adapted SoAS items; Zhang et al. COLM '26 perceived-control items), optionally an implicit measure (intentional binding; Coyle '12; Berberian '12), perceived ownership and responsibility (Draxler '24), plus *objective oversight effectiveness* (problematic actions caught). Distinguish self-causality from self-determination (Bennett et al. '23).
   - Report results separately for low- and high-consequence tasks, because trust effects reverse between them (D2).

---

## Items not verified or omitted

- **Horvitz, Jacobs & Hovel, "Attention-sensitive alerting" (UAI 1999):** not verified (no DOI or abstract retrieved), so omitted. The 2003 CACM, ICMI '03 and CSCW '04 papers cover the same line.
- **Maes (1994) "tell-me / do-it" confidence thresholds:** not confirmed by any fetched source, so the claim is omitted. The paper itself is cited (C1).
- **Sheridan & Verplank (1978):** existence and report number verified (NTIS). The exact original 10-level wording was seen only in secondary adaptations.
- **Content of several classic ACM, APA and journal papers** (Iqbal & Bailey '06, Czerwinski '04, BusyBody, Parasuraman et al. '00, Lee & See, Parasuraman & Manzey, Feigh et al., Böhme & Köpsell, Egelman '08 figures, Anderson/Vance, Ancker, Buçinca, Kim & Liao, Coyle '12, Tapal '17, Bennett '23, Draxler '24): bibliographic metadata was verified via Crossref DOIs, and content summaries are from knowledge of the papers because ACM DL and publisher abstracts were not retrievable (HTTP 403, or no abstract in the API). These summaries are flagged "content note" in their entries.
- **Kim et al. CHI '26 "Here, Let Me Help":** metadata verified via Crossref. Findings come from search-result excerpts only (full text returned 403).
- **Huq et al. (D3) user-study figures:** the usefulness gain differs between arXiv versions (26.5% versus 36.8%), and the v2 study had only 4 returning participants. Treat it as preliminary.
- **Affiliations marked "not verified"** were not confirmed from a fetched page.
- The shared web-search budget ran out late in the investigation. No further searches were made for (i) additional CHI 2026 / IUI 2026 agent-oversight papers, (ii) the OpenAI Operator confirmation design (industry docs, likely covered by another research thread), or (iii) mobile breakpoint-detection work such as Okoshi et al. (Attelia).

# D. Explanations and validated questionnaires: prior-art investigation for AgentPause

*Investigation date: 2026-10-14. Scope: Area 1 covers explanations, especially counterfactual explanations of intervention timing. Area 2 covers validated questionnaires for the user-study mode.*

## How items were verified

- **[V]** means the title, authors, year and venue were checked against a primary record: the arXiv abstract or API, a Crossref DOI record, PubMed, the publisher or official page, or the paper's own PDF text. Claims about content come from the abstract or full text that was actually read.
- **[V-meta]** means the bibliographic data was verified, but the content claims rest on the abstract only.
- **[U]** means unverified. The item is a lead, or a detail that could not be confirmed from a primary source.

**Limitation.** The shared web-search budget for this session ran out partway through Area 2. After that, verification relied on direct fetches of known URLs and on DOI and arXiv-ID lookups. A few scale details (item counts or response formats behind paywalls) and the "perceived control over AI" and "interruption annoyance" searches are therefore incomplete and are marked as such. The novelty assessment in §1.8 should get one more targeted search pass before it is used in a paper (suggested queries are in §1.8).

---

## AREA 1: Explanations

Every Area-1 entry records the nine requested fields: (1) Name, (2) Year, (3) Authors, (4) URL, (5) What it does, (6) Overlap with AgentPause, (7) What AgentPause does differently, (8) Direct competitor?, (9) Type.

### 1.1 Foundations: why/why-not, contrastive, counterfactual

**A1. Why and Why Not Explanations Improve the Intelligibility of Context-Aware Intelligent Systems [V]**
1. Name: Why/Why-Not intelligibility study (CHI '09, pp. 2119–2128, DOI 10.1145/1518701.1519023)
2. Year: 2009
3. Authors: Brian Y. Lim, Anind K. Dey, Daniel Avrahami
4. URL: https://doi.org/10.1145/1518701.1519023 (PDF: https://www.cs.cmu.edu/~byl/publications/lim_chi09.pdf)
5. What it does: Controlled study with more than 200 participants comparing explanation types for a context-aware system. From the abstract: "why" explanations "resulted in better understanding and stronger feelings of trust", while "why not" explanations "resulted in lower understanding yet adequate performance."
6. Overlap: AgentPause's "Why didn't you ask me earlier/later?" are why-not questions. Its "why this decision" output is a why explanation.
7. Difference: Lim et al. explain static classifications in context-aware apps. AgentPause explains a gating decision and its position in time within a multi-step agent trajectory.
8. Direct competitor: No. This is foundational, and it carries a design warning: why-not formats hurt understanding in this study.
9. Type: Academic

**A2. Assessing Demand for Intelligibility in Context-Aware Applications [V]**
1. Name: Intelligibility demand study (UbiComp '09, pp. 195–204, DOI 10.1145/1620545.1620576)
2. Year: 2009
3. Authors: Brian Y. Lim, Anind K. Dey
4. URL: https://doi.org/10.1145/1620545.1620576
5. What it does: Studies which intelligibility types users want (Why, Why Not, How, What If, What Else, Certainty, Control, Situation) under different circumstances. The type list comes from the CMU project page https://www.cs.cmu.edu/~byl/intelligibility.html.
6. Overlap: Gives a taxonomy of question types. AgentPause implements Why, Why-Not (counterfactual timing) and reason codes, which map roughly to Certainty and Situation.
7. Difference: The taxonomy has no explicit "When / Why now" type. Timing questions are the gap AgentPause fills.
8. Direct competitor: No
9. Type: Academic

**A3. Toolkit to Support Intelligibility in Context-Aware Applications (Intelligibility Toolkit) [V-meta]**
1. Name: Intelligibility Toolkit (UbiComp '10, pp. 13–22, DOI 10.1145/1864349.1864353)
2. Year: 2010
3. Authors: Brian Y. Lim, Anind K. Dey
4. URL: https://doi.org/10.1145/1864349.1864353
5. What it does: A toolkit that generates explanation types automatically from context-aware decision models. Content is known from the title and project page only.
6. Overlap: Middleware-style automatic generation of why/why-not explanations.
7. Difference: No agent actions, no human-intervention decisions, no timing counterfactuals.
8. Direct competitor: No (architectural ancestor)
9. Type: Both (academic and software). The software's availability and license are [U].

**A4. Explanation in Artificial Intelligence: Insights from the Social Sciences [V]**
1. Name: Miller survey (Artificial Intelligence 267:1–38, DOI 10.1016/j.artint.2018.07.007; arXiv 1706.07269)
2. Year: 2019 (arXiv 2017)
3. Authors: Tim Miller
4. URL: https://arxiv.org/abs/1706.07269
5. What it does: Reviews philosophy and psychology on explanation and argues that XAI should build on it. The widely cited takeaway is that explanations are contrastive ("why P rather than Q", where Q is the foil), selected, and social.
6. Overlap: AgentPause's "why at step k rather than k−j / k+j" is a contrastive explanation with a temporal foil.
7. Difference: Miller gives the theory. AgentPause gives a concrete temporal-foil implementation for intervention decisions.
8. Direct competitor: No
9. Type: Academic

**A5. Counterfactual Explanations without Opening the Black Box: Automated Decisions and the GDPR [V]**
1. Name: Wachter counterfactuals (Harvard Journal of Law & Technology, 2018; arXiv 1711.00399)
2. Year: 2017 (arXiv) / 2018 (journal)
3. Authors: Sandra Wachter, Brent Mittelstadt, Chris Russell
4. URL: https://arxiv.org/abs/1711.00399
5. What it does: Proposes "unconditional counterfactual explanations": the smallest change to inputs that would flip a decision. These support understanding, contesting, and recourse.
6. Overlap: AgentPause's counterfactual statements, such as "If the irreversibility score had been below X, I would have continued," follow this minimal-change pattern.
7. Difference: Wachter et al. perturb features of a single static decision. AgentPause perturbs the time index (which step) and the trajectory state.
8. Direct competitor: No
9. Type: Academic

**A6. Questioning the AI: Informing Design Practices for Explainable AI User Experiences (XAI Question Bank) [V]**
1. Name: XAI Question Bank (CHI 2020, DOI 10.1145/3313831.3376590; arXiv 2001.02478)
2. Year: 2020 (extended question bank in arXiv v3, 2021)
3. Authors: Q. Vera Liao, Daniel Gruen, Sarah Miller
4. URL: https://arxiv.org/abs/2001.02478
5. What it does: Interviews with 20 UX practitioners. Builds an "algorithm-informed XAI question bank" of prototypical user questions.
6. Overlap: A question-driven explanation design, the same approach as AgentPause's "Why didn't you ask me earlier?" prompts.
7. Difference: Whether the bank contains explicit timing ("why now") questions was not verified here [U]. AgentPause's question set is specific to timing.
8. Direct competitor: No
9. Type: Academic

**A7. Principles of Mixed-Initiative User Interfaces [V]**
1. Name: Horvitz mixed-initiative principles (CHI '99, pp. 159–166, DOI 10.1145/302979.303030)
2. Year: 1999
3. Authors: Eric Horvitz
4. URL: https://www.erichorvitz.com/chi99horvitz.pdf
5. What it does: Lists principles for agents in interfaces. The paper names "poor timing of action" as a key problem. Its principles include weighing the cost and benefit of deferring action to a less distracting time and using dialog to resolve key uncertainties. It also gives an expected-utility analysis of acting versus inaction, with threshold probabilities for action, dialog and inaction (the LookOut system). All of this was confirmed in the PDF text.
6. Overlap: This is the decision-theoretic ancestor of CONTINUE / CLARIFY / ASK_HUMAN / DEFER. Expected-utility thresholds give a natural basis for timing explanations ("the expected value of asking first exceeded that of continuing at step k").
7. Difference: Horvitz does not generate explanations, and in particular no counterfactual timing explanations. Other research tracks cover the gating policy itself.
8. Direct competitor: Partial, for the decision logic. No, for explanations.
9. Type: Academic (LookOut was a research prototype)

### 1.2 Explainable AI planning (XAIP) and contrastive "why not this plan/action"

**B1. Explainable Planning [V]**
1. Name: XAIP roadmap (IJCAI-17 Workshop on Explainable AI; arXiv 1709.10256)
2. Year: 2017
3. Authors: Maria Fox, Derek Long, Daniele Magazzeni
4. URL: https://arxiv.org/abs/1709.10256 (HTML: https://ar5iv.labs.arxiv.org/html/1709.10256)
5. What it does: Lists questions XAIP should answer. Q1: "Why did you do that?" Q2: "Why didn't you do something else…?" Q3: "Why is what you propose… more efficient/safe/cheap…?" Q4: "Why can't you do that?" **Q5: "Why do I need to replan at this point?" Q6: "Why do I not need to replan at this point?"** Q5 and Q6 are tied to plan-execution monitoring, for example filter violations in ROSPlan and dynamic controllability of STNs.
6. Overlap: **High conceptual overlap.** Q5/Q6 ask why an execution-time intervention (replanning) is or is not triggered at this point. That is a "why now / why not now" question about an intervention trigger during execution.
7. Difference: The paper proposes the questions as a research agenda and sketches the techniques that could answer them. The intervention is replanning, not handing control to a human, and there is no "why not earlier or later" counterfactual over a trajectory and no user study. AgentPause makes "at this point" explicit as a contrast against other steps.
8. Direct competitor: Partial (closest conceptual framing)
9. Type: Academic

**B2. Plan Explanations as Model Reconciliation: Moving Beyond Explanation as Soliloquy [V]**
1. Name: Model reconciliation (IJCAI 2017, pp. 156–163, DOI 10.24963/ijcai.2017/23; arXiv 1701.08317)
2. Year: 2017
3. Authors: Tathagata Chakraborti, Sarath Sreedharan, Yu Zhang, Subbarao Kambhampati
4. URL: https://www.ijcai.org/proceedings/2017/23
5. What it does: Treats explanation as updating the human's model so that the agent's plan becomes optimal in it. Explanations depend on the gap between the agent's model and the human's model.
6. Overlap: AgentPause's "why didn't you ask earlier?" often stems from a mismatch between the user's model and the system's: the user thinks the risk was visible earlier. A model-reconciliation framing would explain which fact became available or salient only at step k.
7. Difference: Explains plans in PDDL settings, not intervention timing. AgentPause does not maintain an explicit human model (as far as is known).
8. Direct competitor: No
9. Type: Academic

**B3. Contrastive Explanations of Plans through Model Restrictions [V]**
1. Name: Krarup et al. contrastive XAIP (JAIR 72:533–612, DOI 10.1613/jair.1.12813; arXiv 2103.15575)
2. Year: 2021
3. Authors: Benjamin Krarup, Senka Krivic, Daniele Magazzeni, Derek Long, Michael Cashmore, David E. Smith
4. URL: https://www.jair.org/index.php/jair/article/view/12813
5. What it does: A user study shows that plan questions are mostly contrastive. The authors build a taxonomy and compile each foil into a restricted planning problem (PDDL2.1), solve it, and compare the hypothetical plan with the original. **The taxonomy includes explicitly temporal questions:** FQ4 (reordering: why A before B rather than after), FQ5 and FQ6 (time windows), and **FQ7: "Why is action A used at time T, rather than at least some time T′ after/before T?"** (§5.8 "Delay/Advance an Action"). The worked example asks why a shelf is set up at t = 8.001 rather than at least 8 minutes later. The answer comes from comparing plans: delaying it would delay delivery by 7.5 minutes.
6. Overlap: **Highest formal overlap found.** FQ7 is a temporal counterfactual contrastive question ("why at T rather than earlier/later"), answered by forcing the foil and comparing outcomes. That is the same shape as AgentPause's "Why didn't you ask me earlier/later?".
7. Difference: (a) The object being explained is a plan action chosen by a temporal planner, not a decision to interrupt a human. (b) The mechanism is model compilation plus replanning with a known PDDL model, whereas AgentPause must evaluate a learned or heuristic gating policy on LLM-agent trajectory prefixes or suffixes with no full world model. (c) The audience is planner users, not agent supervisors. (d) There is no notion of human-attention cost or of the trade-off between asking too early and asking too late.
8. Direct competitor: Partial. The question form is prior art and the application is not.
9. Type: Academic

### 1.3 Explanations for reinforcement learning and sequential decisions

**C1. Contrastive Explanations for Reinforcement Learning in terms of Expected Consequences [V]**
1. Name: van der Waa et al. (IJCAI-18 XAI workshop; arXiv 1807.08706)
2. Year: 2018
3. Authors: Jasper van der Waa, Jurriaan van Diggelen, Karel van den Bosch, Mark Neerincx
4. URL: https://arxiv.org/abs/1807.08706
5. What it does: Contrasts the agent's learned policy with a user-specified foil policy in terms of expected consequences, using human-interpretable state and outcome classes. In a pilot survey, users preferred policy-level explanations over single-action ones.
6. Overlap: Consequence-based contrast. AgentPause's "why not later?" can be answered with the expected consequences of continuing, such as an irreversible action executing first.
7. Difference: The foil is an alternative policy or action, not an alternative time for a human intervention.
8. Direct competitor: No
9. Type: Academic

**C2. Explainable Reinforcement Learning Through a Causal Lens [V]**
1. Name: Action-influence causal explanations (AAAI-20, 34(03):2493–2500, DOI 10.1609/aaai.v34i03.5631; arXiv 1905.10958)
2. Year: 2020
3. Authors: Prashan Madumal, Tim Miller, Liz Sonenberg, Frank Vetere
4. URL: https://arxiv.org/abs/1905.10958
5. What it does: Learns a structural causal model during RL and generates explanations through counterfactual analysis. In a 120-participant StarCraft II study, causal explanations outperformed baselines on task prediction, explanation satisfaction and trust. The study used the Hoffman Explanation Satisfaction Scale, which is relevant to Area 2. That the paper answers why and why-not questions is consistent with the paper but was not re-verified here.
6. Overlap: Counterfactual "why / why not action A" for a sequential agent. Its evaluation measures (task prediction plus explanation satisfaction plus trust) are a good template for the AgentPause study.
7. Difference: Explains which action, not when to escalate to a human.
8. Direct competitor: No
9. Type: Academic

**C3. HIGHLIGHTS: Summarizing Agent Behavior to People [V]**
1. Name: HIGHLIGHTS (AAMAS 2018, pp. 1168–1176)
2. Year: 2018
3. Authors: Dan Amir, Ofra Amir
4. URL: https://cris.bgu.ac.il/en/publications/highlights-summarizing-agent-behavior-to-people/
5. What it does: Summarizes agent behavior by extracting "important" states and trajectories from simulations. Users judged agent capabilities better than with baseline summaries.
6. Overlap: Selecting which moments in a trajectory matter is related to explaining why step k was the right moment.
7. Difference: Global summaries for capability assessment, not local timing explanations of an intervention.
8. Direct competitor: No
9. Type: Academic

**C4. Establishing Appropriate Trust via Critical States [V]**
1. Name: Critical states (IROS 2018; arXiv 1810.08174)
2. Year: 2018
3. Authors: Sandy H. Huang, Kush Bhatia, Pieter Abbeel, Anca D. Dragan
4. URL: https://arxiv.org/abs/1810.08174
5. What it does: Critical states are "states in which it is very important to take a certain action." Showing them helps users decide whether to deploy a policy and **when to take control** during execution.
6. Overlap: **Inverse of AgentPause.** Here the system teaches the human when to intervene. AgentPause has the system decide when to request intervention and explain why that moment was critical. The idea of a critical moment (a large action-value gap) is a usable signal for "why step k".
7. Difference: No per-decision timing explanation and no counterfactual "earlier/later". It is policy summarization for trust calibration.
8. Direct competitor: Partial (conceptual)
9. Type: Academic

**C5. Counterfactual Explanations in Sequential Decision Making Under Uncertainty [V]**
1. Name: Tsirtsis et al. (NeurIPS 2021; arXiv 2107.02776)
2. Year: 2021
3. Authors: Stratis Tsirtsis, Abir De, Manuel Gomez-Rodriguez
4. URL: https://arxiv.org/abs/2107.02776
5. What it does: Finds an alternative action sequence that differs in at most k actions and would have led to a better outcome, using finite-horizon MDPs, a Gumbel-Max SCM, and polynomial-time dynamic programming. Evaluated on synthetic and cognitive-behavioral-therapy data.
6. Overlap: Formally, "ask at step j instead of k" is a counterfactual action sequence (ASK moved by one step) in an MDP. This is the closest algorithmic machinery for computing timing counterfactuals under uncertainty.
7. Difference: Targets outcome improvement and recourse for human decision-makers (the clinician example), not explanations of an AI's escalation timing. There is no human-intervention action semantics and no LLM agents.
8. Direct competitor: Partial (methodological)
9. Type: Academic

**C6. Redefining Counterfactual Explanations for Reinforcement Learning: Overview, Challenges and Opportunities [V]**
1. Name: Counterfactual-RL survey (ACM Computing Surveys 56(9):1–33, DOI 10.1145/3648472; arXiv 2210.11846; CC BY 4.0 per Crossref)
2. Year: 2024 (arXiv 2022)
3. Authors: Jasmina Gajcin, Ivana Dusparic
4. URL: https://arxiv.org/abs/2210.11846
5. What it does: Explains why counterfactuals are underused in RL, which is sequential and stochastic, and redefines them for RL.
6. Overlap: Good source for the related-work positioning of temporal counterfactuals.
7. Difference: A survey with no intervention-timing focus.
8. Direct competitor: No
9. Type: Academic

### 1.4 Explaining agent and robot behavior, and when to explain

**D1. Why did my car just do that? Explaining semi-autonomous driving actions to improve driver understanding, trust, and performance [V]**
1. Name: Koo et al. (Int. J. Interactive Design and Manufacturing 9(4):269–275, DOI 10.1007/s12008-014-0227-2; accepted 2014)
2. Year: 2015 (online 2014)
3. Authors: Jeamin Koo, Jungsuk Kwac, Wendy Ju, Martin Steinert, Larry Leifer, Clifford Nass
4. URL: https://www.wendyju.com/publications/WhyDidMyCarJustDoThat.pdf
5. What it does: A simulator study of messages given in advance of auto-braking. "How" messages (the action only) led to poor driving. "Why" messages (the reason) were preferred and improved performance. "How + why" gave the safest driving but more negative feelings.
6. Overlap: Reason-first explanations of an automated intervention.
7. Difference: No timing counterfactual. It is a driving domain.
8. Direct competitor: No
9. Type: Academic

**D2. Look Who's Talking Now: Implications of AV's Explanations on Driver's Trust, AV Preference, Anxiety and Mental Workload [V]**
1. Name: Du et al. (Transportation Research Part C 104:428–442, DOI 10.1016/j.trc.2019.05.025; arXiv 1905.08878)
2. Year: 2019
3. Authors: Na Du, Jacob Haspiel, Qiaoning Zhang, Dawn Tilbury, Anuj K. Pradhan, X. Jessie Yang, Lionel P. Robert Jr.
4. URL: https://arxiv.org/abs/1905.08878
5. What it does: Within-subjects study (N = 32) with four conditions: no explanation, explanation before acting, explanation after acting, and explanation plus an approve/disapprove option. Explanations before acting gave higher trust and preference, with no differences in anxiety or workload.
6. Overlap: Timing of the explanation itself, plus an approve/disapprove condition that resembles ASK_HUMAN.
7. Difference: Studies when to explain, not explanations of why the intervention happened when it did.
8. Direct competitor: No
9. Type: Academic

**D3. Explaining Before or After Acting? How the Timing of Self-Explanations Affects User Perception of Robot Behavior [V]**
1. Name: Stange & Kopp (ICSR 2021, LNCS, pp. 142–153, DOI 10.1007/978-3-030-90525-5_13)
2. Year: 2021
3. Authors: Sonja Stange, Stefan Kopp
4. URL: https://doi.org/10.1007/978-3-030-90525-5_13 (open PDF via https://nbn-resolving.org/urn:nbn:de:0070-pub-29578136)
5. What it does: A pre-registered study of a social robot explaining an undesirable behavior before or after executing it. Explaining before execution made the behavior seem less desirable. Participants felt less uncertain but also less in control, trusted the robot less, and had lower contact intentions.
6. Overlap: Relevant to BLOCK/DEFER explanations and to whether AgentPause explains before pausing or after.
7. Difference: Studies when to explain, not explanations of intervention timing.
8. Direct competitor: No
9. Type: Academic

**D4. Reactive or Proactive? How Robots Should Explain Failures [V]**
1. Name: LeMasurier et al. (HRI '24, pp. 413–422, DOI 10.1145/3610977.3634963)
2. Year: 2024
3. Authors: Gregory LeMasurier, Alvika Gautam, Zhao Han, Jacob W. Crandall, Holly A. Yanco
4. URL: https://faculty.cs.byu.edu/~crandall/papers/LeMasurier_etal_HRI2024.pdf
5. What it does: Compares a reactive system, which explains failures after they occur, with a proactive one that predicts issues (via assumption checkers and behavior trees) and explains them in advance. The proactive version scored higher on perceived intelligence and trust, and its explanations were rated more understandable and timely. It explicitly aims to let people "provide assistance for problems that may prevent a robot from finishing its task."
6. Overlap: **Close in spirit.** A robot predicts a problem, explains it, and enlists human help before failure, which is analogous to ASK_HUMAN before a risky step.
7. Difference: Compares explanation strategies. It does not justify the specific step at which help was requested or offer an earlier/later counterfactual.
8. Direct competitor: Partial
9. Type: Academic

**D5. "Why This Avoidance Maneuver?" Contrastive Explanations in Human-Supervised Maritime Autonomous Navigation [V-meta]**
1. Name: Jose et al. (arXiv 2604.08032; submitted to IEEE ITSC 2026)
2. Year: 2026
3. Authors: Joel Jose, Andreas Madsen, Andreas Brandsæter, Tor A. Johansen, Erlend M. Coates
4. URL: https://arxiv.org/abs/2604.08032
5. What it does: Contrastive explanations (the proposed maneuver against alternatives) for collision-avoidance systems under human supervision. In an exploratory study with 4 marine officers, the explanations helped understanding but increased workload. The authors suggest on-demand or tailored explanations.
6. Overlap: Contrastive explanations for a supervised autonomous agent.
7. Difference: The foil is an alternative maneuver, not an alternative timing. The abstract does not mention timing.
8. Direct competitor: No
9. Type: Academic

### 1.5 "Why now?": explaining the reason or timing of an intervention, request or alert (closest cluster)

**E1. Why Do I Have to Drive Now? Post Hoc Explanations of Takeover Requests [V] (PubMed abstract read)**
1. Name: Körber, Prasch & Bengler (Human Factors 60(3):305–323, DOI 10.1177/0018720817747730, PMID 29283269)
2. Year: 2018 (epub Dec 2017)
3. Authors: Moritz Körber, Lorenz Prasch, Klaus Bengler
4. URL: https://doi.org/10.1177/0018720817747730
5. What it does: Tests whether explaining the reason for an automated vehicle's takeover request (the system handing control to the human) affects trust and acceptance. 40 participants were split into an explanation group and a control group across three takeover scenarios. Explanations did not change trust or acceptance but increased perceived understanding of the system and of the reasons for takeovers. Trust in the explanation group fell after a roadwork-caused takeover.
6. Overlap: **Very close in kind.** An automated system escalates to a human ("ASK_HUMAN") and explains why now. The title literally asks "why now?".
7. Difference: Explains the cause of the request, not counterfactual timing (it does not ask why not earlier or later). It is single-step and driving-specific with no LLM agent. Expected-effect lesson: understanding goes up, trust does not necessarily.
8. Direct competitor: Partial (closest "why now" study for a human-intervention request)
9. Type: Academic

**E2. Explaining an Increase in Predicted Risk for Clinical Alerts [V]**
1. Name: Hardt et al. (ACM CHIL 2020, pp. 80–89, DOI 10.1145/3368555.3384460; arXiv 1907.04911)
2. Year: 2020 (arXiv 2019)
3. Authors: Michaela Hardt, Alvin Rajkomar, Gerardo Flores, Andrew Dai, Michael Howell, Greg Corrado, Claire Cui, Moritz Hardt
4. URL: https://arxiv.org/abs/1907.04911
5. What it does: For a stateful model that produces a time series of risk estimates, it explains why the risk increased, which triggers an alert, by attributing the increase to a few past inputs. This lifts static attribution to dynamics. Experts evaluated it for clinician triage of alerts.
6. Overlap: **Close in mechanism.** It explains why an alert (a request for human intervention) fires now by attributing the change between time steps. AgentPause's "why at step k and not k−1" can use the same idea: attribute the change in gating score between k−1 and k to new trajectory events.
7. Difference: No explicit "why not earlier/later" contrast, no decision categories (CONTINUE/CLARIFY/ASK/DEFER/BLOCK), no agents.
8. Direct competitor: Partial (methodologically closest for "why not one step earlier")
9. Type: Academic

**E3. Time2Stop: Adaptive and Explainable Human-AI Loop for Smartphone Overuse Intervention [V]**
1. Name: Time2Stop (CHI '24, pp. 1–20, DOI 10.1145/3613904.3642747; arXiv 2403.05584)
2. Year: 2024
3. Authors: Adiba Orzikulova, Han Xiao, Zhipeng Li, Yukang Yan, Yuntao Wang, Yuanchun Shi, Marzyeh Ghassemi, Sung-Ju Lee, Anind K. Dey, Xuhai "Orson" Xu
4. URL: https://arxiv.org/abs/2403.05584
5. What it does: A just-in-time adaptive intervention in which ML picks the moment to intervene. Each intervention comes with SHAP-based top-feature explanations at two levels (feature category or simplified feature description), and user feedback updates the model. An 8-week field study (N = 71) found that explanations improved intervention accuracy by a further 53.8% and receptivity by a further 11.4%.
6. Overlap: **Closest deployed system that explains intervention timing.** ML-timed interventions, top-factor explanations attached to each intervention, and a feedback loop. AgentPause's "top factors" output is a near-identical pattern.
7. Difference: Explanations answer why the system thinks the user is overusing now (feature attribution). They give no counterfactual timing ("why not 5 minutes earlier") and no multi-step task semantics. The interventions are behavioral nudges, not oversight of agent actions.
8. Direct competitor: Partial (closest empirical analog for the factor-explanation part)
9. Type: Academic (research system)

**E4. Why and When: Understanding System Initiative during Conversational Collaborative Search [V-meta]**
1. Name: Avula, Choi & Arguello (arXiv 2303.13484)
2. Year: 2023
3. Authors: Sandeep Avula, Bogeum Choi, Jaime Arguello
4. URL: https://arxiv.org/abs/2303.13484
5. What it does: A Wizard-of-Oz study (27 pairs on Slack). Stimulated-recall interviews analyze why and when the human wizard took initiative, including their reasoning about the timing of each intervention.
6. Overlap: Empirical data on how humans justify intervention timing. Usable to design AgentPause's reason codes for timing.
7. Difference: Human wizard rationales, not system-generated explanations shown to users.
8. Direct competitor: No (useful input)
9. Type: Academic

**E5. Exploring the Cost of Interruptions in Human-Robot Teaming [V-meta]**
1. Name: Mannem et al. (IEEE Humanoids 2023; arXiv 2311.00785)
2. Year: 2023
3. Authors: Swathi Mannem, William Macke, Peter Stone, Reuth Mirsky
4. URL: https://arxiv.org/abs/2311.00785
5. What it does: A robot interrupts a human teammate to get information, with timing, content and proximity varied. People rated the interrupting robot as significantly less helpful, while their secondary-task performance dropped only slightly.
6. Overlap: The cost of asking, including its timing. This is motivation for justifying asks.
7. Difference: No explanations.
8. Direct competitor: No
9. Type: Academic

### 1.6 LLM and robot agents that ask for help, clarification or approval

**F1. Robots That Ask For Help: Uncertainty Alignment for Large Language Model Planners (KnowNo) [V]**
1. Name: KnowNo (CoRL 2023, PMLR 229:661–682)
2. Year: 2023
3. Authors: Allen Z. Ren, Anushri Dixit, Alexandra Bodrova, Sumeet Singh, Stephen Tu, Noah Brown, Peng Xu, Leila Takayama, Fei Xia, Jake Varley, Zhenjia Xu, Dorsa Sadigh, Andy Zeng, Anirudha Majumdar
4. URL: https://proceedings.mlr.press/v229/ren23a.html
5. What it does: Uses conformal prediction over LLM-proposed next steps. If the prediction set has more than one option, the robot asks for help. This gives statistical guarantees on task success while minimizing help requests.
6. Overlap: A principled "when to ask" trigger. A prediction set of size greater than 1 is a natural reason code ("multiple plausible actions").
7. Difference: Does not explain to the user why it asks or why at that step (per abstract). There is no DEFER/BLOCK and no explanation interface.
8. Direct competitor: Partial (decision side only)
9. Type: Both (academic, with a project page; code availability [U])

**F2. Learning to Ask: When LLM Agents Meet Unclear Instruction (Ask-when-Needed, NoisyToolBench) [V-meta]**
1. Name: AwN (EMNLP 2025; arXiv 2409.00557)
2. Year: 2024 (arXiv) / 2025 (EMNLP)
3. Authors: Wenxuan Wang, Juluan Shi, Zixuan Ling, Yuk-Kit Chan, Chaozheng Wang, Cheryl Lee, Youliang Yuan, Jen-tse Huang, Wenxiang Jiao, Michael R. Lyu
4. URL: https://arxiv.org/abs/2409.00557
5. What it does: Shows that LLM tool-callers hallucinate missing arguments. The proposed framework has the agent ask the user when instructions are unclear.
6. Overlap: CLARIFY decisions for tool calls.
7. Difference: No explanation of why or when it asked.
8. Direct competitor: Partial (decision side)
9. Type: Academic (benchmark; code [U])

**F3. Ask Early, Ask Late, Ask Right: When Does Clarification Timing Matter for Long-Horizon Agents? [V-meta]**
1. Name: Gulati et al. (arXiv 2605.07937; preprint, CC BY 4.0 paper license)
2. Year: 2026
3. Authors: Anmol Gulati, Hariom Gupta, Elias Lumer, Sahil Sen, Vamse Kumar Subbiah
4. URL: https://arxiv.org/abs/2605.07937
5. What it does: Forced-injection experiments supply ground-truth clarifications at controlled points in agent trajectories (84 task variants, 6,000+ runs, 4 frontier models). Goal clarification loses most of its value after about 10% of execution. Input clarification stays useful until about 50%. Asking after the midpoint is worse than never asking. Across 300 unscripted sessions, no frontier model asked within the optimal window: 52% of sessions over-asked, and the rest never asked. "Code and data will be publicly released" (no repository or license given yet).
6. Overlap: **Very high relevance to the timing problem.** It gives an empirical value-of-asking-over-time curve, which could ground AgentPause's "why not later" explanations ("asking later loses X% of value for goal-type uncertainty").
7. Difference: Measures timing value. It does not explain timing to users and has no oversight middleware.
8. Direct competitor: Partial (timing decision side, not explanation)
9. Type: Academic

**F4. Magentic-UI: Towards Human-in-the-loop Agentic Systems [V]**
1. Name: Magentic-UI (arXiv 2507.22358; GitHub microsoft/magentic-ui, MIT license per repository page)
2. Year: 2025
3. Authors: Hussein Mozannar, Gagan Bansal, Cheng Tan, Adam Fourney, et al. (20 authors)
4. URL: https://arxiv.org/abs/2507.22358 ; https://github.com/microsoft/magentic-ui
5. What it does: An open-source web-agent interface with co-planning, co-tasking, action guards, long-term memory and other mechanisms. Action guards label actions as always, maybe or never irreversible. "Always" actions prompt the user for binary approval. "Maybe" actions go to an LLM judge that decides whether approval is needed.
6. Overlap: **Software competitor on the gating side.** It has a per-action guard with an approval request.
7. Difference: The paper says the user is "prompted to approve or disapprove a binary action decision". Nothing indicates that the judge's reason, top factors, or any timing counterfactual is shown to the user. This is [U] from the first 100k characters of the paper only.
8. Direct competitor: Partial (yes for gating, no for explanation)
9. Type: Both

**F5. Comparing Human Oversight Strategies for Computer-Use Agents [V-meta]**
1. Name: Chen et al. (arXiv 2604.04918)
2. Year: 2026
3. Authors: Chaoran Chen, Zhiping Zhang, Zeya Chen, Eryue Xu, Yinuo Yang, Ibrahim Khalilov, Simret A Gebreegziabher, Yanfang Ye, Ziang Xiao, Yaxing Yao, Tianshi Li, Toby Jia-Jun Li
4. URL: https://arxiv.org/abs/2604.04918
5. What it does: Compares 4 oversight strategies (48 participants, 192 live web sessions). Strategy changed exposure to problematic actions but not users' ability to intervene. The authors attribute this to timing mismatches: control returned too early or too late. Upfront approval inhibited scrutiny at runtime. They conclude that oversight depends on "aligning authority, timing, and attention with decision-critical moments."
6. Overlap: **Strong motivation for AgentPause.** It documents empirically that intervention timing in agent oversight is often wrong.
7. Difference: No explanations of timing. Its findings would support AgentPause's "why now" explanations as a remedy.
8. Direct competitor: No (motivating evidence)
9. Type: Academic

**F6. Proactive AI assistants and timing (related cluster) [V-meta]**
- *Need Help? Designing Proactive AI Assistants for Programming*: Valerie Chen, Alan Zhu, Sebastian Zhao, Hussein Mozannar, David Sontag, Ameet Talwalkar. CHI 2025, DOI 10.1145/3706598.3714002 (CC BY 4.0 per Crossref), arXiv 2410.04596. Studies proactive suggestion design; timing depends on recent editor activity.
- *Assistance or Disruption? … Proactive AI Programming Support (Codellaborator)*: Kevin Pu, Daniel Lazaro, Ian Arawjo, Haijun Xia, Ziang Xiao, Tovi Grossman, Yan Chen. CHI 2025, DOI 10.1145/3706598.3713357, arXiv 2502.18658. Proactive agents raised efficiency but disrupted workflows. Presence indicators and interaction context reduced the disruption.
- *Developer Interaction Patterns with Proactive AI: A Five-Day Field Study*: Nadine Kuo, Agnia Sergeyuk, Valerie Chen, Maliheh Izadi. IUI '26, arXiv 2601.10253. 229 interventions; interventions at workflow boundaries (for example after a commit) got 52% engagement.
- *Anticipatory Human Oversight of Agentic AI: A Philosophical Account*: Kevin Baum, Maximilian Kiener, Markus Langer, Johann Laux. arXiv 2609.24242, 2026. Argues that escalation conditions specified ahead of time should determine when reactive intervention is invoked.
- Overlap and difference for the cluster: all address when to intervene. None generate explanations of intervention timing (per abstracts). Direct competitor: No. Type: Academic.

### 1.7 Do explanations improve appropriate reliance? Evidence and over-trust risks

| # | Work (verified) | Key finding (from abstract or full text) | Implication for AgentPause |
|---|---|---|---|
| G1 | Bansal, Wu, Zhou, Fok, Nushi, Kamar, Ribeiro, Weld. *Does the Whole Exceed its Parts? The Effect of AI Explanations on Complementary Team Performance*. CHI 2021, DOI 10.1145/3411764.3445717, arXiv 2006.14779 | Complementary gains came from AI assistance, but explanations did not add to them. Explanations "increased the chance that humans will accept the AI's recommendation, regardless of its correctness." | An explained ASK_HUMAN may increase rubber-stamp approvals. Measure appropriate reliance, not just approval rate or satisfaction. |
| G2 | Buçinca, Malaya, Gajos. *To Trust or to Think: Cognitive Forcing Functions Can Reduce Overreliance on AI in AI-assisted Decision-making*. PACM HCI 5(CSCW1), DOI 10.1145/3449287, arXiv 2102.09692 | Simple XAI did not reduce overreliance. Cognitive forcing (N = 199) did, but the designs that reduced overreliance most got the least favorable subjective ratings. Benefits were larger for people high in Need for Cognition. | There is a trade-off between explanation formats that force thinking (for example, ask the user first, then reveal factors) and SUS/UEQ ratings. Consider Need for Cognition as a covariate. |
| G3 | Vasconcelos, Jörke, Grunde-McLaughlin, Gerstenberg, Bernstein, Krishna. *Explanations Can Reduce Overreliance on AI Systems During Decision-Making*. PACM HCI 7(CSCW1), DOI 10.1145/3579605, arXiv 2212.06823 | Across 5 studies (N = 731) using a cost-benefit framing, explanations reduce overreliance when they lower the cost of verifying the AI. Task difficulty, explanation difficulty and incentives all matter. | Timing explanations should make verification cheaper (show what changed at step k and what the action will do), not just give rationale. |
| G4 | Zhang, Liao, Bellamy. *Effect of Confidence and Explanation on Accuracy and Trust Calibration in AI-Assisted Decision Making*. FAT* 2020, DOI 10.1145/3351095.3372852, arXiv 2001.02114 | Confidence scores helped calibrate trust. Local explanations had problems. Calibration alone did not improve joint accuracy. | Showing a calibrated risk or uncertainty score may matter more than feature-based "top factors". |
| G5 | Schemmer, Kühl, Benz, Bartos, Satzger. *Appropriate Reliance on AI Advice: Conceptualization and the Effect of Explanations*. IUI 2023, DOI 10.1145/3581641.3584066, arXiv 2302.02187 | Proposes Appropriateness of Reliance (AoR), measured as RAIR and RSR. With N = 200, feature-importance explanations significantly increased RAIR (29.59% to 38.87%), while RSR did not change significantly (full text). | Use AoR-style metrics in the study: approving correct asks (RAIR-like) and rejecting bad agent actions (RSR-like). |
| G6 | Wang & Yin. *Are Explanations Helpful? A Comparative Study of the Effects of Explanations in AI-Assisted Decision-Making*. IUI 2021, DOI 10.1145/3397481.3450650 | Effects depend on domain expertise. Many explanations meet none of the desiderata in low-expertise tasks. Counterfactual explanations did not perform as well as expected (per abstract). | Counterfactual-timing explanations need empirical validation, not assumed benefit. |
| G7 | Poursabzi-Sangdeh, Goldstein, Hofman, Wortman Vaughan, Wallach. *Manipulating and Measuring Model Interpretability*. CHI 2021, DOI 10.1145/3411764.3445315 | In pre-registered experiments (N = 3,800), transparency helped people simulate the model but did not increase following it, and it reduced detection of large model mistakes (information overload). | Keep explanations short. More detail can hurt error detection. |
| G8 | Eiband, Buschek, Kremer, Hussmann. *The Impact of Placebic Explanations on Trust in Intelligent Systems*. CHI EA 2019, DOI 10.1145/3290607.3312787 | In a lab study (N = 30), placebic explanations (justifications with no information) produced perceived trust similar to real explanations. | **Include a placebic or justification-only control condition** in the AgentPause study to separate the effect of content from the effect of merely giving a reason. |
| G9 | Kaur, Nori, Jenkins, Caruana, Wallach, Wortman Vaughan. *Interpreting Interpretability: Understanding Data Scientists' Use of Interpretability Tools for Machine Learning*. CHI 2020, DOI 10.1145/3313831.3376219 | Data scientists over-trusted and misused SHAP and GAM tools, and few could accurately describe their outputs. | Experts are not immune. Developers using AgentPause's factor outputs may over-trust them. |
| G10 | Ehsan & Riedl. *Explainability Pitfalls: Beyond Dark Patterns in Explainable AI*. arXiv 2109.12480 (2021); a journal version in *Patterns* (2024) is [U] | Defines "explainability pitfalls": unintended negative effects such as unwarranted trust in numerical explanations. | Risk register item. Numeric "risk = 0.82" style factors can induce unwarranted trust. |
| G11 | Körber et al. 2018 (E1 above) | Explaining takeover requests raised understanding but not trust or acceptance. | A realistic hypothesis: expect gains in understanding, possibly not in trust. |
| G12 | Stange & Kopp 2021 (D3 above) | Explaining before an undesirable action lowered perceived control and trust. | For BLOCK/DEFER, test explanation placement. |

### 1.8 Critical assessment: has counterfactual explanation of intervention timing already been studied?

**Short answer.** The building blocks are prior art. The specific combination was not found in this investigation. Within the (budget-limited) search, no verified work generates user-facing counterfactual explanations of why a human-intervention request (ask, clarify, defer, block) was issued at step k of a multi-step agent task rather than earlier or later, or evaluates such explanations with users.

**Closest works, ranked by closeness:**

| Rank | Work | What it already covers | Gap that AgentPause fills | Closeness |
|---|---|---|---|---|
| 1 | **Krarup et al., JAIR 2021, FQ7 "Delay/Advance an Action"** | The exact temporal contrastive question form ("why at time T rather than at least T′ earlier or later"), answered by forcing the foil and comparing outcomes; a user study showing questions are contrastive | The object is a planner's action, not a decision to hand control to a human. It requires a full PDDL model, has no attention or interruption cost, and has no LLM agents. | **High in form, low in application.** Must be cited as prior art for the question form. |
| 2 | **Fox, Long & Magazzeni 2017, Q5/Q6** "Why do I (not) need to replan at this point?" | Names why-now and why-not-now questions for an execution-time intervention trigger | A roadmap only (no generator, no user study). The intervention is replanning, not a human request. There is no earlier/later contrast across steps. | **Medium–high conceptually** |
| 3 | **Körber, Prasch & Bengler 2018** (takeover-request explanations) | Explains to users why the automation requests a human takeover now; a user study | Explains the cause only, with no counterfactual timing. Single-step, driving domain. | **Medium** (same decision type, ASK_HUMAN, different explanation type) |
| 4 | **Hardt et al. 2020** (explaining risk increases for alerts) | Explains why an alert fires now by attributing the change across time steps | Not contrastive against other times. Clinical prediction rather than agent oversight. | **Medium** (best mechanism for "why not at k−1") |
| 5 | **Time2Stop (CHI 2024)** | ML-timed interventions plus top-factor (SHAP) explanations plus a feedback loop; field-study evidence that explanations improve receptivity | Factors only, with no earlier/later counterfactual and no multi-step task actions | **Medium** (closest empirical system) |
| 6 | Gulati et al. 2026; Chen et al. 2026 (computer-use agent oversight); Horvitz 1999 | Show that ask and intervention timing matters and is often wrong, and give a decision-theoretic basis for deferral | No explanations to users | Low–medium (motivation and decision side) |
| 7 | Tsirtsis et al. 2021; Huang et al. 2018 | Counterfactual action sequences in MDPs; critical states for deciding when to take over | Not about explaining an AI's escalation timing | Low–medium (method) |

**Defensible novelty framing.** Do not claim that counterfactual or contrastive temporal explanation is new: Krarup FQ7 and Fox Q5/Q6 predate it. A defensible claim is: "the first middleware that (a) produces temporal contrastive explanations (why step k rather than earlier or later) for intervention-gating decisions of LLM agents, (b) grounds them in the actual gating policy's evaluations on trajectory prefixes and suffixes, and (c) evaluates them in a configurable user study." The search should be repeated before submission because 2025–2026 LLM-agent HCI work (CHI 2026, UIST 2026, arXiv) moves fast. Suggested queries: "temporal contrastive explanation agent", "why now explanation intervention", "explain clarification timing", "explaining deferral timing", "why did the agent ask me now", and "explanations for approval requests in computer-use agents".

**Design implications drawn from this literature:**
1. **Faithfulness.** Compute "why not earlier" by re-running the real gating policy on the state at k−1, k−2 and so on, and report which factor crossed its threshold at k (in the style of Hardt). Compute "why not later" from an estimated consequence of deferral: an irreversible action at k, or the decay in value of asking (Gulati). Avoid post-hoc LLM rationalizations; see Ehsan & Riedl's pitfalls and Eiband's placebic explanations.
2. **Why-not formats can lower understanding** (Lim et al. 2009). Lead with "why now", put the earlier/later contrast second and keep it short (Poursabzi-Sangdeh).
3. **Study controls.** Include no explanation, a placebic justification, factors only, and factors plus timing counterfactuals. Measure appropriate reliance (AoR or RAIR/RSR-style), not just trust and satisfaction (Bansal; Schemmer; Vasconcelos).
4. **Expected effects** (Körber 2018; Stange & Kopp 2021). Understanding should rise more reliably than trust. Explanations given before blocking may reduce perceived control, so treat that as a measured outcome.

---

## AREA 2: Validated questionnaires for the user-study mode

Item text is deliberately not reproduced here. A verdict of "Ship items?" means whether the item text can be bundled in an open-source repository. Even where a license allows it, keep instruments in a separate `instruments/` folder with their own LICENSE or NOTICE and citation. Do not put them under the code license (MIT or Apache), especially for CC BY-SA material.

### 2.1 System Usability Scale (SUS) [V]
- **Original citation:** Brooke, J. (1996). SUS: A "quick and dirty" usability scale. In P. W. Jordan, B. Thomas, B. A. Weerdmeester & I. L. McClelland (Eds.), *Usability Evaluation in Industry* (pp. 189–194). Taylor & Francis. The CRC Press re-issue has DOI 10.1201/9781498710411-35, listed by Crossref as pp. 207–212. The editor names are [U] (standard citation, not re-verified). Retrospective: Brooke, J. (2013). SUS: A retrospective. *Journal of Usability Studies* 8(2), 29–40 (bibliographic data from a search snippet; the JUS site returned 404).
- **URL:** The author's chapter manuscript is hosted at https://hell.meiert.org/core/pdf/sus.pdf (a third-party host, text read directly). Background: https://meiert.com/en/blog/revitalizing-sus-the-system-usability-scale
- **Usage terms as stated by the source** (chapter text): "SUS has been made freely available for use in usability assessment … the only prerequisite for its use is that any published report should acknowledge the source of the measure." The form carries "© Digital Equipment Corporation, 1986." The meiert.com post notes that HP later acquired DEC and that the current rights holder is unclear.
- **Items / format:** 10 items, 5-point agreement scale (strongly disagree to strongly agree), scored 0–100.
- **Ship items?** **Yes, with attribution (low risk).** The author's free-use statement covers use. It is not an open license and the copyright notice remains, so add a NOTICE that cites Brooke (1996), say that the items are used under the author's free-use statement, and exclude them from the code license.

### 2.2 NASA-TLX and Raw TLX [V]
- **Original citation:** Hart, S. G., & Staveland, L. E. (1988). Development of NASA-TLX (Task Load Index): Results of empirical and theoretical research. In P. A. Hancock & N. Meshkati (Eds.), *Human Mental Workload* (Advances in Psychology), pp. 139–183. North-Holland/Elsevier. DOI 10.1016/S0166-4115(08)62386-9. The editors and book title are the standard citation; Crossref confirms title, pages and series. **Raw TLX:** Hart, S. G. (2006). NASA-Task Load Index (NASA-TLX); 20 years later. *Proceedings of the HFES Annual Meeting* 50(9), 904–908. DOI 10.1177/154193120605000909. Wikipedia cites Hart (2006) for Raw TLX; the content was not read in the original.
- **URL:** https://www.nasa.gov/human-systems-integration-division/nasa-task-load-index-tlx/ (the legacy humansystems.arc.nasa.gov pages refused connections)
- **Usage terms (NASA page, quoted):** "The NASA TLX tool is 'open source', and is therefore available for immediate use by any person or organization (worldwide)." "It is not necessary to obtain permission from NASA to use TLX, nor is permission needed to make modifications to the tool itself." No specific license or public-domain statement is given.
- **Items / format:** 6 subscales (mental, physical and temporal demand; performance; effort; frustration). Each is rated 0–100 in 5-point steps (21 gradations). The weighted version uses 15 pairwise comparisons. **Raw TLX** skips the weighting and averages the subscales. Format per Wikipedia, which cites Hart (2006).
- **Notes:** Per Wikipedia, unofficial computerized versions that collect personally identifiable information conflict with NASA's human-subjects guidelines ([U] on the NASA page itself). Do not imply NASA endorsement.
- **Ship items?** **Yes.** NASA explicitly permits use and modification without permission. Cite Hart & Staveland (1988) and Hart (2006). The frustration subscale is a useful partial proxy for annoyance (§2.10).

### 2.3 Trust in Automation scale (Jian, Bisantz & Drury) [V-meta]
- **Original citation:** Jian, J.-Y., Bisantz, A. M., & Drury, C. G. (2000). Foundations for an empirically determined scale of trust in automated systems. *International Journal of Cognitive Ergonomics* 4(1), 53–71. DOI 10.1207/S15327566IJCE0401_04 (Informa/Taylor & Francis).
- **URL:** https://doi.org/10.1207/S15327566IJCE0401_04. Semantic Scholar points to a DTIC technical-report version (ADA388787); the DTIC page returned 403, so its distribution statement is [U].
- **Usage terms:** **No license or usage statement found.** Crossref lists no license. Hoffman et al. (2018) note it is one of the most widely used scales and reproduce it in an appendix, but criticize items 1–4 as redundant and the "integrity" item as problematic.
- **Items / format:** Commonly reported as 12 items on a 7-point scale ([U] against the paywalled original).
- **Ship items?** **Reference or placeholder only**, unless the DTIC report proves to be "approved for public release" (US-government work) or permission is obtained. The items are widely reprinted, but no explicit grant was found.

### 2.4 Trust in Automation questionnaire (TiA, Körber) [V]
- **Original citation:** Körber, M. (2019). Theoretical considerations and development of a questionnaire to measure trust in automation. In S. Bagnara et al. (Eds.), *Proceedings of the 20th Congress of the International Ergonomics Association (IEA 2018)*, Vol. VI, pp. 13–30. Springer (Advances in Intelligent Systems and Computing). DOI 10.1007/978-3-319-96074-6_2. Crossref lists the year as 2018 (online); the author cites it as 2019.
- **URL:** https://github.com/moritzkoerber/TiA_Trust_in_Automation_Questionnaire (paper download: https://osf.io/y3jn5/)
- **License (stated):** "licensed under a Creative Commons Attribution-ShareAlike 4.0 International License" (README). The manual says: "Feel free to use the questionnaire abiding by the license (CC BY-SA 4.0) and to develop the questionnaire further."
- **Items / format:** 19 items in 6 subscales: Reliability/Competence, Understanding/Predictability, Familiarity, Intention of Developers, Propensity to Trust, Trust in Automation (2 items). Items 5, 7, 10, 15 and 16 are inverted. 5-point agreement scale plus a "no response" option. The manual recommends analyzing subscales separately rather than as a total score. Available in German and English; **the English version is not yet validated** (README).
- **Ship items?** **Yes (CC BY-SA 4.0).** Attribution is required. Adapted wording (for example, "the agent" instead of "the system") must be shared under CC BY-SA, so keep it out of an MIT/Apache code tree or license that folder separately. Note the English-validation caveat in study reports.

### 2.5 Hoffman et al. XAI measures: Explanation Satisfaction Scale, XAI Trust Scale, Explanation Goodness Checklist [V]
- **Citations:** (a) Hoffman, R. R., Mueller, S. T., Klein, G., & Litman, J. (2018). *Metrics for Explainable AI: Challenges and Prospects*. arXiv:1812.04608 (v2 2019; arXiv non-exclusive distribution license). (b) Hoffman, R. R., Mueller, S. T., Klein, G., & Litman, J. (2023). Measures for explainable AI: Explanation goodness, user satisfaction, mental models, curiosity, trust, and human-AI performance. *Frontiers in Computer Science* 5. DOI 10.3389/fcomp.2023.1096257.
- **URLs:** https://arxiv.org/abs/1812.04608 ; https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2023.1096257/full
- **License:** The 2023 article states "Copyright © 2023 Hoffman, Mueller, Klein and Litman … distributed under the terms of the Creative Commons Attribution License (CC BY)" (CC BY 4.0 per Crossref), and "This material is approved for public release. Distribution is unlimited." The 2018 arXiv version carries only arXiv's non-exclusive license.
- **Explanation Satisfaction Scale:** 8 items in the 2018 Appendix C, 5-point agreement scale. The 2018 paper reports a content-validity (CVR) analysis, Cronbach's α = 0.86, and discriminant validity (good versus bad explanations). The 2023 Table 3 version uses a 1–5 scale; an automated read counted 7 items there, so check the exact count [U]. The 2023 article itself says "Psychometric research pursuing this for XAI scales would be valuable."
- **XAI Trust Scale (2023):** 8 items, 1–5 agreement. Mostly adapted from the Cahour–Fourzy scale, with items from Jian et al., Wang et al., Schaefer, and Madsen–Gregor. Psychometric validation as a whole is [U].
- **Explanation Goodness Checklist (2023):** 7 yes/no items, intended for researchers or experts rather than end users.
- **Ship items?** **Yes, from the 2023 Frontiers version (CC BY 4.0) with attribution.** Some items adapt third-party scales; the risk is low, but credit the sources Hoffman cites. **Do not ship the 2018 arXiv wording** (no reuse license). Note the limited validation in study reports.

### 2.6 Trust of Automated Systems Test (TOAST) [V-meta]
- **Citation:** Wojton, H. M., Porter, D., Lane, S. T., Bieber, C., & Madhavan, P. (2020). Initial validation of the trust of automated systems test (TOAST). *The Journal of Social Psychology* 160(6), 735–750. DOI 10.1080/00224545.2020.1749020. PMID 32297844. Authors at the Institute for Defense Analyses.
- **URL:** https://doi.org/10.1080/00224545.2020.1749020
- **Usage terms:** **None found.** It is a Taylor & Francis article and Crossref lists no license. Whether IDA published a public-release version is [U].
- **Items / format:** Two-factor structure, Understanding and Performance (abstract, verified). Commonly described as 9 items on a 7-point scale [U].
- **Ship items?** **Reference or placeholder only**, unless permission is obtained or a public-release version with clear terms is located.

### 2.7 Merritt (2011) trust scale [V-meta]
- **Citation:** Merritt, S. M. (2011). Affective processes in human–automation interactions. *Human Factors* 53(4), 356–370. DOI 10.1177/0018720811411912. PMID 21901933.
- **URL:** https://doi.org/10.1177/0018720811411912
- **Usage terms:** **None found** (SAGE; text-and-data-mining license only).
- **Items / format:** Hoffman et al. (2018, Appendix D) list 6 trust items and report Cronbach's α of .87–.92. The response format is [U]. The study also measured liking and propensity to trust machines (abstract).
- **Ship items?** **Reference or placeholder only.**

### 2.8 Sense of agency and perceived control
- **Sense of Agency Scale (SoAS) [V]:** Tapal, A., Oren, E., Dar, R., & Eitam, B. (2017). The Sense of Agency Scale: A measure of consciously perceived control over one's mind, body, and the immediate environment. *Frontiers in Psychology* 8, 1552. DOI 10.3389/fpsyg.2017.01552. URL https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2017.01552/full. **License: CC BY** (article statement "© 2017 Tapal, Oren, Dar and Eitam … Creative Commons Attribution License (CC BY)"). Format: 7-point agreement scale with two factors, Sense of Positive Agency (SoPA) and Sense of Negative Agency (SoNA). Study 1 selected 13 items, and Study 2 removed two cross-loading items before CFA. Whether the recommended final instrument has 13 or 11 items is **[U]**; check Table 1 and the text. **Construct caveat:** it is a general, cross-situational (trait-like) measure with two-month test–retest stability, **not** a measure of control over a specific AI system. **Ship items?** Yes under CC BY with attribution, but it is a poor fit as the main dependent variable for "control over the agent."
- **Sense of Agency Rating Scale (SOARS) [V-meta]:** Polito, V., Barnier, A. J., & Woody, E. Z. (2013). *Consciousness and Cognition* 22(3), 684–696. DOI 10.1016/j.concog.2013.04.003. Developed for agency disruption in **hypnosis**, so it is not a fit. Crossref metadata lists an Elsevier user license and CC BY-NC-SA 3.0 (an open-archive license); applicability is [U].
- **HCI caution [V]:** Bergström, J., Knibbe, J., Pohl, H., & Hornbæk, K. (2022). Sense of Agency and User Experience: Is There a Link? *ACM TOCHI* 29(4), 1–22. DOI 10.1145/3490493. Subjective "experienced control" ratings did not track low-level sense of agency in a simple way: "other factors of user experience spill over to the experienced control." This is a reason to pair any control questionnaire with behavioral measures such as override rate and time to intervene.
- **Validated perceived-control-over-AI scale:** **Not found within this investigation** (the search budget was exhausted, so this is [U] rather than a confirmed absence). Recommendation: use TiA "Understanding/Predictability" (CC BY-SA) plus clearly labelled ad hoc control items, and report them as non-validated.

### 2.9 UEQ, UEQ-S and UMUX-Lite
- **UEQ [V]:** Laugwitz, B., Held, T., & Schrepp, M. (2008). Construction and evaluation of a user experience questionnaire. In *HCI and Usability for Education and Work (USAB 2008)*, LNCS 5298, pp. 63–76. Springer. DOI 10.1007/978-3-540-89350-9_6. The volume title is the standard citation; Crossref confirms LNCS and pages. URL: https://www.ueq-online.org/ (handbook: https://www.ueq-online.org/Material/Handbook.pdf, version 11, 2023). **Terms:** the site says "Everything is completely free of charge" and "Copyrights © 2024 All Rights Reserved by UEQ Team". No redistribution license is stated. Translations are invited to be sent to the UEQ team for publication. **Format:** 26 items in 6 scales, 7-point semantic differential (handbook). **Ship items?** **Placeholder plus link to the official download** (free to use in studies, but "All Rights Reserved" with no grant to redistribute). Alternatively, request written permission to bundle.
- **UEQ-S [V-meta]:** Schrepp, M., Hinderks, A., & Thomaschewski, J. (2017). Design and evaluation of a short version of the User Experience Questionnaire (UEQ-S). *IJIMAI* 4(6), 103–108. DOI 10.9781/ijimai.2017.09.001. 8 items (UEQ site), 7-point semantic differential. The same terms as the UEQ apply; the IJIMAI article license is [U]. **Ship items?** Placeholder plus link.
- **UMUX-LITE [V-meta]:** Lewis, J. R., Utesch, B. S., & Maher, D. E. (2013). UMUX-LITE: When there's no time for the SUS. *CHI '13*, pp. 2099–2102. DOI 10.1145/2470654.2481287 (ACM copyright). Based on UMUX: Finstad, K. (2010). The Usability Metric for User Experience. *Interacting with Computers* 22(5), 323–327. DOI 10.1016/j.intcom.2010.04.004. UMUX-LITE is commonly described as 2 items on a 7-point scale [U]; the ACM page returned 403. **Usage terms: none found.** **Ship items?** **Reference or placeholder** until the terms are confirmed. Practical risk is low, but there is no explicit grant.

### 2.10 Interruption annoyance and disruption
- **No dedicated, validated interruption-annoyance scale was identified** in this investigation. This is [U] because the search budget ran out before a full search.
- Related instruments and studies: Bailey, B. P., & Konstan, J. A. (2006). On the need for attention-aware systems: Measuring effects of interruption on task performance, error rate, and affective state. *Computers in Human Behavior* 22(4), 685–708. DOI 10.1016/j.chb.2005.12.009. It measured affective state (annoyance and anxiety) under interruptions; the instrument details are [U]. Mehrotra, A., Pejovic, V., Vermeulen, J., Hendley, R., & Musolesi, M. (2016). *My Phone and Me* (CHI 2016, pp. 1021–1032, DOI 10.1145/2858036.2858566) studied receptivity to and perceived disruption from notifications; the instrument details are [U].
- **Recommendation:** use the NASA-TLX frustration subscale (shippable) and Raw TLX for workload, plus ad hoc single items such as "annoyance", "was this the right moment to be asked?" and "should I have been asked earlier or later?". Label these as non-validated and pre-register them. The earlier/later item also gives a direct behavioral and attitudinal check on AgentPause's timing counterfactuals.

### 2.11 Summary table: license verdicts

| Scale | Original citation | Items / format | Terms as stated by source | Ship item text in OSS repo? |
|---|---|---|---|---|
| SUS | Brooke 1996 (Usability Evaluation in Industry, pp. 189–194) | 10 items, 5-point; 0–100 | "freely available … only prerequisite … acknowledge the source"; form © DEC 1986 | **Yes, with attribution** (not an open license; separate NOTICE) |
| NASA-TLX / Raw TLX | Hart & Staveland 1988; Hart 2006 | 6 subscales, 0–100 (21 steps); weighted via 15 pairs, or Raw TLX | NASA: "open source"; no permission needed to use or modify | **Yes** (cite; no NASA endorsement) |
| Jian et al. trust | Jian, Bisantz & Drury 2000, IJCE 4(1):53–71 | 12 items, 7-point [U] | No license found | **No: reference/placeholder** (unless the DTIC public-release status is confirmed) |
| Körber TiA | Körber 2019 (IEA 2018, AISC 823, pp. 13–30) | 19 items, 6 subscales, 5-point + "no response"; English version not validated | **CC BY-SA 4.0** (GitHub) | **Yes** (attribution, ShareAlike; separate folder license) |
| Hoffman Explanation Satisfaction Scale | Hoffman et al. 2018 (arXiv); 2023 (Frontiers 5:1096257) | 8 items (2018) / Table 3 (2023), 5-point; α = .86 (2018) | 2023 article: **CC BY 4.0**; 2018 arXiv: non-exclusive license | **Yes, from the 2023 version** (attribution) |
| Hoffman XAI Trust Scale | Hoffman et al. 2023 | 8 items, 5-point | **CC BY 4.0** (items adapted from other scales) | **Yes** (attribution; credit the source scales) |
| Hoffman Explanation Goodness Checklist | Hoffman et al. 2023 | 7 items, yes/no | **CC BY 4.0** | **Yes** (attribution) |
| TOAST | Wojton et al. 2020, J. Soc. Psychol. 160(6):735–750 | 2 factors (Understanding, Performance); 9 items, 7-point [U] | None found | **No: reference/placeholder** |
| Merritt 2011 | Human Factors 53(4):356–370 | 6 trust items (per Hoffman 2018); format [U] | None found | **No: reference/placeholder** |
| Sense of Agency Scale | Tapal et al. 2017, Front. Psychol. 8:1552 | 13 items developed, 11 vs 13 in final [U]; 7-point; SoPA/SoNA; trait-like | **CC BY** | **Yes** (attribution), but construct mismatch for "control over AI" |
| SOARS | Polito et al. 2013, Conscious. Cogn. 22(3) | Hypnosis-specific | Elsevier / CC BY-NC-SA 3.0 per Crossref [U] | Not recommended (wrong construct) |
| UEQ | Laugwitz, Held & Schrepp 2008, LNCS 5298:63–76 | 26 items, 6 scales, 7-point semantic differential | "completely free of charge"; "All Rights Reserved by UEQ Team" | **No: placeholder plus official link** (or ask permission) |
| UEQ-S | Schrepp, Hinderks & Thomaschewski 2017, IJIMAI 4(6):103–108 | 8 items, 7-point | Same as UEQ | **No: placeholder plus official link** |
| UMUX-LITE | Lewis, Utesch & Maher 2013, CHI '13 pp. 2099–2102 | 2 items, 7-point [U] | None found (ACM copyright) | **No: reference/placeholder** (low practical risk, but no grant) |
| UMUX | Finstad 2010, Interact. Comput. 22(5):323–327 | 4 items, 7-point [U] | None found | **No: reference/placeholder** |
| Interruption annoyance | None validated found [U] | Use TLX frustration plus ad hoc items | — | Ad hoc items are your own (ship freely) |

**Implementation suggestion for the user-study mode:** store each instrument as a declarative definition with fields `id`, `citation`, `doi`, `license`, `redistributable: true/false`, `items[]`, `scale`, `scoring` and `reverse_items`. For non-redistributable instruments, ship `items: []` with a `source_url` and a loader that reads a locally supplied file. The study config can reference them by `id` and validate at startup that the item text is present.

---

## Key takeaways

1. **The question form is not new; its application to intervention timing appears to be.** Krarup et al. (JAIR 2021) already formalize and answer "Why is action A used at time T rather than at least T′ earlier/later?" (FQ7), and Fox et al. (2017) list "Why do I (not) need to replan at this point?". Within this (budget-limited) search, no verified work generates and evaluates user-facing "why ask/clarify/defer/block at step k rather than earlier or later" explanations for LLM-agent oversight. AgentPause's novelty claim should be scoped to that combination, with FQ7 and Q5/Q6 cited as prior art.
2. **The closest "why now" precedents** are Körber et al. 2018 (explaining takeover requests: understanding up, trust unchanged), Hardt et al. 2020 (attributing the rise in risk that triggers an alert), and Time2Stop (CHI 2024: SHAP factors on ML-timed interventions improved receptivity and accuracy). None offers counterfactual timing.
3. **Timing matters and is often wrong in agent oversight.** Chen et al. 2026 found control returned too early or too late in computer-use-agent oversight. Gulati et al. 2026 found that clarification value decays fast and that frontier models ask outside the optimal window. This motivates AgentPause and can ground its "why not later" explanations.
4. **Explanations can backfire.** They can increase acceptance regardless of correctness (Bansal 2021). Placebic reasons raise trust as much as real ones (Eiband 2019). Why-not explanations lowered understanding (Lim 2009). Explaining before an undesirable act lowered perceived control and trust (Stange & Kopp 2021). The study should therefore include a placebic-justification control, measure appropriate reliance (RAIR/RSR), and aim explanations at lowering the cost of verification (Vasconcelos 2023).
5. **Make timing counterfactuals faithful.** Compute them by re-evaluating the real gating policy on neighbouring steps (Hardt-style attribution of change), not with LLM-generated rationales.
6. **Questionnaire licensing:**
   - Shippable: NASA-TLX/Raw TLX (NASA: no permission needed), Körber TiA (CC BY-SA 4.0), Hoffman 2023 XAI scales (CC BY 4.0), and the Sense of Agency Scale (CC BY, but a construct mismatch).
   - SUS can ship with attribution under the author's free-use statement (copyright © DEC 1986 remains).
   - Ship as reference or placeholder only: Jian et al. 2000, TOAST, Merritt 2011, UMUX/UMUX-LITE (no license found), and UEQ/UEQ-S (free of charge but "All Rights Reserved").
7. **Gaps to close before relying on this report:**
   - Item counts for TOAST, UMUX-LITE and Jian, the final SoAS item count, and the 2023 ESS item count.
   - Whether a validated "perceived control over AI" or "interruption annoyance" scale exists.
   - Whether Magentic-UI shows the reason for its approval prompts.
   - A fresh 2025–2026 literature sweep for "why now" explanations in LLM agents.

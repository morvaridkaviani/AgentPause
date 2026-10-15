# B. Prior art (academic ML / NLP / robotics / AI safety): agents deciding when to ask, defer, abstain or escalate

Research area B for **AgentPause: Adaptive Human Intervention Timing for AI Agents**.
AgentPause in brief: middleware that takes a proposed agent action plus context (uncertainty, severity, reversibility/recoverability, intent ambiguity, task progress, interruption cost, cognitive load, user preferences, decision history). It outputs CONTINUE / CLARIFY / ASK_HUMAN / DEFER / BLOCK with explanations, including counterfactual "why not earlier / why not later" ones. It compares five policies: full autonomy, always confirm, fixed risk threshold, adaptive expected-value-of-asking, and user-customized.

**How this was checked (as of 2026-10-14).** Every item below was opened on its arXiv abstract or HTML page, ACL Anthology, JAIR, PMLR/NeurIPS proceedings, conference virtual page, or author PDF. For a few key items I read the full text (HTML, or text pulled out of the PDF). "Venue" is the venue the fetched page shows. Where the page showed no venue I write "arXiv" and, if I know the venue, add "(venue per my knowledge)". Code links are given only when a fetched page showed them. The session's shared web-search budget ran out late in the work, so some leads are listed under "Could not verify" at the end instead of in the catalogue.

**Competitor ratings.** "Yes" means it makes the same core decision AgentPause makes: whether or when to interrupt a human about a proposed agent action, with an adaptive or learned policy. "Partial" means it shares a major mechanism or signal. "No" means background only.

---

## 0. Quick map (most relevant first)

| # | Work | Year | Competitor? | Why it matters |
|---|---|---|---|---|
| 1 | Value of Information: A Framework for Human–Agent Communication (Dong et al., ACL 2026) | 2026 | **Yes** | Asks when VoI − c > 0. Stakes enter through utility, user effort is the cost, compared against always/never/threshold baselines |
| 2 | Modeling Distinct Human Interaction in Web Agents: CowCorpus / PlowPilot (Huq et al., CMU) | 2026 | **Yes** | Per proposed action, predicts `<ask_user>` vs `<agent_continue>` from the user's intervention style; deployed live |
| 3 | Magentic-UI action guards (Mozannar et al., Microsoft) | 2025 | **Yes (system level)** | Irreversibility heuristic (always/maybe/never) plus an LLM judge decides whether a human must approve an action |
| 4 | Ask Early, Ask Late, Ask Right (Gulati et al., PwC) | 2026 | Partial (timing evidence) | Measures how much a clarification is worth at each point in a long trajectory |
| 5 | Ask4Help (Singh et al., NeurIPS 2022) | 2022 | Partial (strong) | Learned asking policy conditioned on an embedding of the **user's preferred** cost of asking and of failure |
| 6 | SAGE-Agent / Structured Uncertainty guided Clarification (Suri et al., ACL Findings 2026) | 2025/26 | Partial (strong) | EVPI minus aspect-based cost over tool arguments, with a stopping rule |
| 7 | Self-Regulation and Requesting Interventions (Min et al., CMU) | 2025 | Partial (strong) | Dynamic-programming rule: help iff cost r < Δsuccess/Δusage; r tuned to a budget |
| 8 | ReHAC (Feng et al.) | 2024 | Partial | RL collaboration policy per step, reward = task − λ·(#human interventions) |
| 9 | Horvitz, Principles of Mixed-Initiative UIs (CHI 1999) | 1999 | Partial (foundational) | Expected-utility thresholds p* for act / dialog / no-act; deferring service timing; learned per-user timing |
| 10 | Scerri, Pynadath & Tambe, Adjustable Autonomy (JAIR 2002) | 2002 | Partial (foundational on timing) | MDP over transfer-of-control strategies: when to ask, how long to wait, when to act or delay |
| 11 | KnowNo (Ren et al., CoRL 2023) and Introspective Planning (Liang et al., NeurIPS 2024) | 2023–24 | Partial | Conformal prediction sets; ask when the set is not a single option, with a statistical success guarantee |
| 12 | ProbGuard (Wang et al., ASE 2026) and AgentSpec (ICSE 2026) | 2025–26 | Partial | Runtime enforcement with `user_inspection`; ProbGuard intervenes **early**, from predicted violation probability |
| 13 | InferAct (Fang et al., EMNLP 2025) | 2024–25 | Partial | Before critical (irreversible) actions, infers intent and alerts the human under a review budget |
| 14 | Oversight Has a Capacity (Turan) | 2026 | Partial | Escalation under reviewer fatigue; safety is an inverted U in escalation rate |
| 15 | PAINT (Xie et al., NeurIPS 2022); Plaut et al. (ICML 2025, JMLR) | 2022–25 | Partial | Ask for help to avoid or escape irreversible states |
| 16 | ThriftyDAgger / LazyDAgger / Fleet-DAgger (Hoque et al.) | 2021–22 | Partial | Gating on risk and novelty under an intervention budget; reducing context switches; allocating human attention |
| 17 | Sequential Learning-to-Defer (Joshi et al.) | 2021 | Partial (timing) | Decides whether deferring **now** beats waiting one more step |

---

## 1. Foundations: decision-theoretic asking, adjustable / sliding autonomy, assistance games

### 1.1 Principles of Mixed-Initiative User Interfaces
- **Year:** 1999 (CHI '99, pp. 159–166)
- **Authors / affiliation:** Eric Horvitz, Microsoft Research
- **URL:** https://www.erichorvitz.com/chi99horvitz.pdf (also https://www.microsoft.com/en-us/research/publication/principles-mixed-initiative-user-interfaces/)
- **What it does:** The LookOut calendaring agent infers p(goal | evidence) and computes the expected utility of acting, not acting, and asking (dialog). Action follows a threshold p*; with dialog as an option there are two thresholds, p*(no-action, dialog) and p*(dialog, action). The utilities depend on context: for example, deeper user focus on another task makes unwanted action worse, which raises the threshold. A section on "User attention and the timing of service" defers the offer until the user is likely ready. It uses a default timing model, and the system "can also be instructed to build a custom-tailored timing model" from watching the user. Timeouts scale with the inferred probability. The paper also lists the principle "minimizing the cost of poor guesses about action and timing."
- **Overlap with AgentPause:** Very high in concept. It has an expected-utility choice between act, ask and no-act; thresholds that shift with attention and context; deferral to a better time; and per-user learned timing. This is the canonical prior art for "expected value of asking minus interruption cost" and for DEFER.
- **AgentPause would differ by:** Targeting multi-step, tool-using LLM agents whose actions have real side effects. Adding reversibility and recoverability, severity, BLOCK, and a separate CLARIFY (intent) vs ASK_HUMAN (approval). Learning from a history of user decisions on agent actions. Generating counterfactual timing explanations. Benchmarking five policies against each other.
- **Direct competitor?** Partial. It is foundational: any claim that "EV of asking with attention-dependent cost and deferral" is new must cite and go beyond it.
- **Type:** Academic (research prototype; no code released).

### 1.2 Towards Adjustable Autonomy for the Real World
- **Year:** 2002 (JAIR vol. 17)
- **Authors / affiliation:** Paul Scerri, David V. Pynadath, Milind Tambe (USC / ISI)
- **URL:** https://jair.org/index.php/jair/article/view/10312 (arXiv copy: https://arxiv.org/abs/1106.4573; DOI 10.1613/jair.1037)
- **What it does:** Criticizes "rigid one-shot transfers of control" and proposes **transfer-of-control strategies**: conditional sequences of (i) handing decision control to a person or agent and (ii) changing coordination constraints, such as delaying a team commitment, to buy time. MDPs pick the best strategy given an uncertain environment, the probability and timing of a human response, and costs to the individual and team, such as time delays and miscoordination. It was deployed in the Electric Elves office-assistant system.
- **Overlap with AgentPause:** Timing is an explicit decision variable: whom to ask, how long to wait, and when to fall back to autonomy. Delaying a commitment is close to DEFER, and the cost of waiting is modelled.
- **AgentPause would differ by:** Handling single-user LLM agents and their side-effecting tool calls rather than team coordination. Using rich per-action signals (uncertainty, reversibility, severity, cognitive load). Producing explanations. Learning a cost model from user decisions.
- **Direct competitor?** Partial. It is the key older foundation for intervention timing and deadlines.
- **Type:** Academic.

### 1.3 Coordinated Multi-Agent Teams and Sliding Autonomy for Large-Scale Assembly
- **Year:** 2006 (Proceedings of the IEEE 94(7):1425–1444)
- **Authors / affiliation:** Brennan Sellner, Frederik Heger, Laura Hiatt, Reid Simmons, Sanjiv Singh (CMU Robotics Institute)
- **URL:** https://publications.ri.cmu.edu/coordinated-multi-agent-teams-and-sliding-autonomy-for-large-scale-assembly
- **What it does:** In sliding autonomy, agents model their own and the human operator's performance on each subtask and use this to decide when to request operator help. The operator can join or leave the team, and the paper studies how fast the operator regains situational awareness, which is the switching cost.
- **Overlap with AgentPause:** Asking is driven by expected performance gaps, and the human's cost of re-entering context is treated as real.
- **AgentPause would differ by:** Working in LLM-agent settings, adding reversibility and preference signals, offering DEFER/BLOCK, and explaining decisions.
- **Direct competitor?** No. Historical foundation.
- **Type:** Academic.

### 1.4 The Off-Switch Game
- **Year:** 2016 arXiv; IJCAI 2017 (venue per my knowledge; the arXiv page lists none)
- **Authors / affiliation:** Dylan Hadfield-Menell, Anca Dragan, Pieter Abbeel, Stuart Russell (UC Berkeley)
- **URL:** https://arxiv.org/abs/1611.08219
- **What it does:** A game-theoretic model. A robot that is uncertain about the utility of its action, and treats the human's choice as evidence about that utility, has an incentive to defer, meaning it lets the human switch it off. The incentive shrinks as the robot grows confident or as the human becomes less rational.
- **Overlap with AgentPause:** Gives the theoretical reason to defer when uncertain about the user's utility. Also shows that the value of asking depends on how reliable the human's answer is.
- **AgentPause would differ by:** Being an operational middleware with practical signals, rather than a normative model. AgentPause could include "human reliability or fatigue" in the value of asking, which this paper motivates.
- **Direct competitor?** No. Theory.
- **Type:** Academic.

### 1.5 Cooperative Inverse Reinforcement Learning (CIRL)
- **Year:** 2016 (NeurIPS 2016, venue per my knowledge)
- **Authors / affiliation:** Dylan Hadfield-Menell, Anca Dragan, Pieter Abbeel, Stuart Russell (UC Berkeley)
- **URL:** https://arxiv.org/abs/1606.03137
- **What it does:** Value alignment as a two-player cooperative game in which only the human knows the reward. Optimal joint policies come from a reduction to a POMDP, and information-gathering behaviour emerges from the formulation.
- **Overlap with AgentPause:** It is the assistance-game framing that underlies "query the human when it is informative".
- **AgentPause would differ by:** Making the query a discrete, explicitly costed intervention at run time, using engineering signals and offering explanations.
- **Direct competitor?** No.
- **Type:** Academic.

### 1.6 Should Robots be Obedient?
- **Year:** 2017 (IJCAI 2017)
- **Authors / affiliation:** Smitha Milli, Dylan Hadfield-Menell, Anca Dragan, Stuart Russell (UC Berkeley)
- **URL:** https://arxiv.org/abs/1705.09990
- **What it does:** Studies the tradeoff between obeying literal orders and inferring preferences. The robot should decide intelligently when to obey, with a lean toward obedience, and should detect when its model of the human is wrong.
- **Overlap with AgentPause:** Concerns when to defer to the human versus act on the agent's own judgment.
- **AgentPause would differ by:** Same contrast as 1.4: theory versus a run-time system.
- **Direct competitor?** No.
- **Type:** Academic.

---

## 2. Value of information, EVPI and Bayesian experimental design for asking

### 2.1 Value of Information: A Framework for Human–Agent Communication
- **Year:** 2026 (arXiv Jan 2026; ACL 2026 main conference, Long, pp. 42879–42896)
- **Authors / affiliation:** Yijiang River Dong, Tiancheng Hu, Zheng Hui, Caiqi Zhang, Ivan Vulić, Andreea Bobu, Nigel Collier (University of Cambridge; Bobu at MIT)
- **URL:** https://aclanthology.org/2026.acl-long.1987/ ; https://arxiv.org/abs/2601.06407
- **What it does:** At each turn it computes NetVoI(q) = VoI(q) − c, where VoI(q) = V_post(b, q) − V(b). It asks the question with the highest positive net value and commits to an action when none is positive. The cost is linear in the number of turns (c from 0.01 to 0.20), standing for user time and effort. Stakes enter only through the utility; in Mixed 20Q, for example, a correct medical diagnosis is worth 10 and an animal guess 1. It is myopic (one step ahead) but multi-turn, needs no hyperparameter tuning, and runs at inference time. Baselines are no-question, fixed number of rounds, adaptive prompting, and a verbalized-confidence threshold. It matches or beats the best tuned baselines on 20Q, medical diagnosis, flight recommendation and e-commerce. Personalization appears only as an inferred latent reward per user in the flight task.
- **Overlap with AgentPause:** This is the closest formal match to AgentPause's "adaptive (expected-value-of-asking)" policy. Its baselines line up with AgentPause's "always confirm", "full autonomy" and "fixed threshold" policies.
- **AgentPause would differ by:** (i) Gating **side-effecting actions in multi-step trajectories**, not just clarify-or-commit before answering. (ii) Making reversibility and recoverability first-class parts of the loss of acting wrongly, instead of folding stakes into the utility. (iii) Letting the cost of interruption depend on cognitive load and task phase and **learning it from the user's decision history**, rather than using a constant c. (iv) Treating **timing** (DEFER to a breakpoint) as a decision; the paper's limitations say it addresses whether to communicate, not when in a trajectory. (v) Adding BLOCK and a separate ASK_HUMAN for approval. (vi) Producing counterfactual explanations.
- **Direct competitor?** **Yes**, on the expected-value-of-asking core. AgentPause should use it as a baseline and position against it.
- **Type:** Both (academic; code announced at https://github.com/dong-river/VOI_communication, marked "will be available").

### 2.2 Structured Uncertainty guided Clarification for LLM Agents (SAGE-Agent, ClarifyBench)
- **Year:** 2025 arXiv (v1 Nov 2025); Findings of ACL 2026 (pp. 40811–40838)
- **Authors / affiliation:** Manan Suri, Puneet Mathur, Nedim Lipka, Franck Dernoncourt, Ryan A. Rossi, Dinesh Manocha (University of Maryland; Adobe Research)
- **URL:** https://arxiv.org/abs/2511.08798 ; https://aclanthology.org/2026.findings-acl.2028/
- **What it does:** Models clarification over **tool-call parameters** as a POMDP. EVPI(q) is the expected gain in the probability of the best candidate tool call after hearing the answer. Cost(q, t) = λ·Σ (number of times each targeted aspect has already been asked about), so repeated questions cost more. Score = EVPI − Cost. The agent asks only if uncertainty is above τ, and stops when the best net score falls below α times the current best-candidate probability, or when the top candidate's probability reaches τ_exec. The selection is greedy and myopic, re-evaluated at every step. It reports 7–39% more coverage while asking 1.5–2.7× fewer questions.
- **Overlap with AgentPause:** Expected value of asking net of cost, applied to tool-using agents, with a stopping rule. This is AgentPause's CLARIFY branch.
- **AgentPause would differ by:** Covering approval of risky actions as well as filling in missing arguments. Using a cost that reflects interruption, load and preference rather than only redundancy. Adding reversibility, severity, timing/DEFER, BLOCK and explanations.
- **Direct competitor?** Partial, and strong for the CLARIFY component.
- **Type:** Academic (no code link found).

### 2.3 Learning to Ask Good Questions: Ranking Clarification Questions using Neural Expected Value of Perfect Information
- **Year:** 2018 (ACL 2018, pp. 2737–2746)
- **Authors / affiliation:** Sudha Rao, Hal Daumé III (University of Maryland)
- **URL:** https://aclanthology.org/P18-1255/
- **What it does:** Ranks candidate clarification questions on StackExchange by a neural estimate of EVPI: a question scores higher when its likely answer is useful.
- **Overlap with AgentPause:** Early NLP use of EVPI for clarifying questions.
- **AgentPause would differ by:** Deciding whether and when to interrupt at all, not ranking questions. It has no cost or timing model.
- **Direct competitor?** No.
- **Type:** Academic (code released per the paper; not checked here).

### 2.4 Uncertainty of Thoughts (UoT)
- **Year:** 2024 (NeurIPS 2024)
- **Authors / affiliation:** Zhiyuan Hu, Chumin Liu, Xidong Feng, Yilun Zhao, See-Kiong Ng, Anh Tuan Luu, Junxian He, Pang Wei Koh, Bryan Hooi (NUS et al.)
- **URL:** https://arxiv.org/abs/2402.03271
- **What it does:** Simulates possible future answers and scores questions by information gain, propagated through a lookahead tree, to choose which question to ask. Applied to 20Q, medical diagnosis and troubleshooting.
- **Overlap with AgentPause:** An information-gain criterion for asking, with lookahead (non-myopic).
- **AgentPause would differ by:** Including interruption cost, action risk and reversibility, and timing.
- **Direct competitor?** No.
- **Type:** Both (code: https://github.com/zhiyuanhubj/UoT).

### 2.5 Active Task Disambiguation with LLMs
- **Year:** 2025 (arXiv)
- **Authors / affiliation:** Katarzyna Kobalczyk, Nicolas Astorga, Tennison Liu, Mihaela van der Schaar (University of Cambridge)
- **URL:** https://arxiv.org/abs/2502.04485
- **What it does:** Frames disambiguation as Bayesian experimental design: choose clarifying questions that maximize information gain over the set of viable solutions.
- **Overlap with AgentPause:** Selecting clarifications in a principled way.
- **AgentPause would differ by:** Same contrast as 2.4.
- **Direct competitor?** No.
- **Type:** Academic.

### 2.6 Eliciting Human Preferences with Language Models (GATE)
- **Year:** 2023 (arXiv)
- **Authors / affiliation:** Belinda Z. Li, Alex Tamkin, Noah Goodman, Jacob Andreas (MIT / Anthropic / Stanford)
- **URL:** https://arxiv.org/abs/2310.11589
- **What it does:** Generative Active Task Elicitation: the LM interviews the user to elicit the intended behaviour. Users found this less effortful and more informative than writing prompts.
- **Overlap with AgentPause:** Upfront elicitation of preferences, which AgentPause could use to initialize its user-customized policy.
- **AgentPause would differ by:** Making run-time, per-action intervention decisions.
- **Direct competitor?** No.
- **Type:** Academic.

### 2.7 Uncertainty-Aware Clarification in LLM Agents with Information Gain
- **Year:** 2026 (ICML 2026, per the arXiv journal-ref)
- **Authors / affiliation:** Mengyi Deng, Zhiwei Li, Xin Li, Tingyu Zhu, Ying Zhao, Zhijiang Guo, Wei Wang
- **URL:** https://arxiv.org/abs/2606.03135
- **What it does:** Trains a clarifier LLM with an "Information Gain Reward": how much a question moves the Bayesian belief toward the true goal. Evaluated on a clarification-enhanced τ-bench; +3.7% success for +0.3 interaction steps.
- **Overlap with AgentPause:** Clarification for tool-using agents, rewarded by information gain.
- **AgentPause would differ by:** Including an explicit interruption cost, risk and reversibility, timing, and non-clarification interventions.
- **Direct competitor?** Partial (CLARIFY component).
- **Type:** Academic.

### 2.8 When and How Should an Agent Clarify? CIGAsk
- **Year:** 2026 (EMNLP 2026 Findings)
- **Authors / affiliation:** Yunxiang Li, Xixin Wu, Helen Meng (CUHK)
- **URL:** https://arxiv.org/abs/2609.24290
- **What it does:** Multi-turn RL (GRPO) with a Counterfactual Information Gain reward (did the question recover the missing information?) plus an "Asymmetric Ambiguity Bonus" that teaches when to ask.
- **Overlap with AgentPause:** A learned "when to clarify" policy.
- **AgentPause would differ by:** Same contrast as 2.7.
- **Direct competitor?** Partial (CLARIFY).
- **Type:** Academic.

### 2.9 Modeling Future Conversation Turns to Teach LLMs to Ask Clarifying Questions
- **Year:** 2024 arXiv; ICLR 2025
- **Authors / affiliation:** Michael J.Q. Zhang, W. Bradley Knox, Eunsol Choi (UT Austin / NYU)
- **URL:** https://arxiv.org/abs/2410.13788
- **What it does:** Labels preferences by simulating how later turns play out, which teaches the model when a clarifying question beats a direct answer.
- **Overlap with AgentPause:** Lookahead on downstream value as the basis for deciding to clarify.
- **AgentPause would differ by:** Handling action gating, reversibility, interruption cost, and DEFER.
- **Direct competitor?** No.
- **Type:** Academic.

---

## 3. Uncertainty-triggered asking for help (robots and LLM planners/agents)

### 3.1 Robots That Ask For Help: Uncertainty Alignment for Large Language Model Planners (KnowNo)
- **Year:** 2023 (CoRL 2023, oral; PMLR v229)
- **Authors / affiliation:** Allen Z. Ren, Anushri Dixit, Alexandra Bodrova, Sumeet Singh, Stephen Tu, Noah Brown, Peng Xu, Leila Takayama, Fei Xia, Jake Varley, Zhenjia Xu, Dorsa Sadigh, Andy Zeng, Anirudha Majumdar (Princeton / Google DeepMind)
- **URL:** https://arxiv.org/abs/2307.01928 ; https://proceedings.mlr.press/v229/ren23a.html
- **What it does:** The LLM scores multiple-choice candidate next steps. Conformal prediction, calibrated to a target success level 1−ε, forms a prediction set. **If the set contains more than one option, the robot asks the human to choose.** This gives a statistical guarantee on task completion while keeping help to a minimum, and extends to multi-step plans. It covers spatial, numeric, preference and Winograd-style ambiguity.
- **Overlap with AgentPause:** Uncertainty-gated ASK with a calibrated threshold. This is the principled version of AgentPause's "fixed risk threshold" policy.
- **AgentPause would differ by:** Weighing consequences (severity, reversibility) and interruption cost rather than ambiguity alone. Choosing when to ask. Adding DEFER/BLOCK. Adapting per user. Explaining decisions.
- **Direct competitor?** Partial. It is the canonical uncertainty-only baseline; AgentPause should include a KnowNo-style conformal baseline.
- **Type:** Both (project page https://robot-help.github.io).

### 3.2 Introspective Planning: Aligning Robots' Uncertainty with Inherent Task Ambiguity
- **Year:** 2024 (NeurIPS 2024)
- **Authors / affiliation:** Kaiqu Liang, Zixu Zhang, Jaime Fernández Fisac (Princeton)
- **URL:** https://arxiv.org/abs/2402.06529
- **What it does:** Builds a knowledge base of introspective rationales for human-selected safe and compliant plans, retrieves them at deployment, and combines this with conformal prediction. The result is tighter prediction sets, fewer unnecessary clarification requests, and better safety, including on a safe mobile-manipulation benchmark.
- **Overlap with AgentPause:** Reduces over-asking while keeping guarantees, and explicitly considers safety and compliance.
- **AgentPause would differ by:** Same contrast as 3.1, plus a model of user preferences and history.
- **Direct competitor?** Partial.
- **Type:** Both (https://introplan.github.io).

### 3.3 Explore until Confident: Efficient Exploration for Embodied Question Answering
- **Year:** 2024 (RSS 2024)
- **Authors / affiliation:** Allen Z. Ren, Jaden Clark, Anushri Dixit, Masha Itkina, Anirudha Majumdar, Dorsa Sadigh (Princeton / Stanford / TRI)
- **URL:** https://arxiv.org/abs/2403.15941
- **What it does:** Uses conformal calibration of VLM confidence to decide **when to stop** gathering information and answer.
- **Overlap with AgentPause:** A calibrated stopping time, which is related to timing.
- **AgentPause would differ by:** Deciding about the human rather than more exploration.
- **Direct competitor?** No.
- **Type:** Academic.

### 3.4 CLARA: Classifying and Disambiguating User Commands for Reliable Interactive Robotic Agents
- **Year:** 2023 (arXiv; v6 2024)
- **Authors / affiliation:** Jeongeun Park, Seungwon Lim, Joonhyung Lee, Sangbeom Park, Minsuk Chang, Youngjae Yu, Sungjoon Choi (Korea University / Yonsei / NAVER)
- **URL:** https://arxiv.org/abs/2306.10376
- **What it does:** Classifies each command as certain, ambiguous or infeasible using LLM uncertainty and scene context. Ambiguous commands trigger clarifying questions.
- **Overlap with AgentPause:** A three-way outcome much like CONTINUE / CLARIFY / BLOCK.
- **AgentPause would differ by:** Adding consequence-aware gating of actions mid-trajectory, timing, and preferences.
- **Direct competitor?** Partial (weak).
- **Type:** Academic (project page).

### 3.5 Towards Uncertainty-Aware Language Agent (UALA)
- **Year:** 2024 (ACL 2024 Findings)
- **Authors / affiliation:** Jiuzhou Han, Wray Buntine, Ehsan Shareghi (Monash University; VinUniversity)
- **URL:** https://arxiv.org/abs/2401.14016
- **What it does:** Measures uncertainty from token log-probabilities (single inference) or from sample disagreement (multi inference). Thresholds are calibrated on correctly answered training questions (for example the 0.9 quantile). Above the threshold the agent calls a tool; if it is still uncertain it can **defer to a human** (simulated with gold answers in the UALA-S+Oracle setting). Verbalized confidence is reported as unreliable.
- **Overlap with AgentPause:** An escalation cascade based on calibrated uncertainty: act, then tool, then human.
- **AgentPause would differ by:** Adding consequence, reversibility and interruption cost; using the human for action approval rather than as an answer oracle; adding timing and explanations.
- **Direct competitor?** Partial.
- **Type:** Both (https://uala-agent.github.io).

### 3.6 SAUP: Situation Awareness Uncertainty Propagation on LLM Agent
- **Year:** 2024 (arXiv)
- **Authors / affiliation:** Qiwei Zhao, Xujiang Zhao, Yanchi Liu, Wei Cheng, Yiyou Sun, Mika Oishi, Takao Osaki, Katsushi Matsuda, Huaxiu Yao, Haifeng Chen (NEC Labs America / UNC et al.)
- **URL:** https://arxiv.org/abs/2412.01033
- **What it does:** Propagates uncertainty across all of an agent's steps, with situational weights, instead of scoring only the final output.
- **Overlap with AgentPause:** Could supply AgentPause's "agent uncertainty" signal at trajectory level.
- **AgentPause would differ by:** Being the consumer of such a signal, with decisions and costs on top.
- **Direct competitor?** No (signal provider).
- **Type:** Academic.

### 3.7 MediQ: Question-Asking LLMs and a Benchmark for Reliable Interactive Clinical Reasoning
- **Year:** 2024 (arXiv; NeurIPS 2024 per my knowledge)
- **Authors / affiliation:** Shuyue Stella Li, Vidhisha Balachandran, Shangbin Feng, Jonathan S. Ilgen, Emma Pierson, Pang Wei Koh, Yulia Tsvetkov (UW / Cornell et al.)
- **URL:** https://arxiv.org/abs/2406.00922
- **What it does:** An abstention module estimates confidence and decides whether to ask a follow-up question or answer; diagnostic accuracy improves 22.3%.
- **Overlap with AgentPause:** A confidence-gated choice between asking and acting in a high-stakes domain.
- **AgentPause would differ by:** Same contrast as 3.5.
- **Direct competitor?** No.
- **Type:** Academic + benchmark.

---

## 4. Learning when (and what) to ask

### 4.1 Vision-based Navigation with Language-based Assistance via Imitation Learning with Indirect Intervention (VNLA)
- **Year:** 2018 arXiv; CVPR 2019
- **Authors / affiliation:** Khanh Nguyen, Debadeepta Dey, Chris Brockett, Bill Dolan (University of Maryland / Microsoft Research)
- **URL:** https://arxiv.org/abs/1812.04155
- **What it does:** A navigation agent learns to ask an advisor for language subgoals when it senses it is lost.
- **Overlap with AgentPause:** A learned help-request policy.
- **AgentPause would differ by:** Including action consequences, interruption cost and timing.
- **Direct competitor?** No.
- **Type:** Academic (code released per the paper; not checked).

### 4.2 Help, Anna! Visual Navigation with Natural Multimodal Assistance via Retrospective Curiosity-Encouraging Imitation Learning
- **Year:** 2019 (EMNLP 2019)
- **Authors / affiliation:** Khanh Nguyen, Hal Daumé III (University of Maryland)
- **URL:** https://arxiv.org/abs/1909.01871
- **What it does:** A hierarchical memory-augmented agent learns when to request help from simulated humans. It estimates its own chance of making future progress and learns from past mistakes.
- **Overlap with AgentPause:** Uses a progress estimate as a trigger for asking, which corresponds to AgentPause's task-progress signal.
- **AgentPause would differ by:** Same contrast as 4.1.
- **Direct competitor?** No.
- **Type:** Both (https://github.com/khanhptnk/hanna).

### 4.3 A Framework for Learning to Request Rich and Contextually Useful Information from Humans (first circulated as "Learning When and What to Ask: a Hierarchical Reinforcement Learning Framework")
- **Year:** 2021 arXiv; ICML 2022
- **Authors / affiliation:** Khanh Nguyen, Yonatan Bisk, Hal Daumé III (UMD / CMU / Microsoft)
- **URL:** https://arxiv.org/abs/2110.08258
- **What it does:** Hierarchical RL. The agent learns when to request help and **what type** of information to request (for example current state, goal, or subgoal), then interprets the reply. The assistant may recursively decompose tasks.
- **Overlap with AgentPause:** Choosing among types of request mirrors CLARIFY (goal) versus ASK_HUMAN.
- **AgentPause would differ by:** Including an explicit cost and risk model, reversibility, DEFER, and explanations.
- **Direct competitor?** Partial (weak).
- **Type:** Academic.

### 4.4 Ask4Help: Learning to Leverage an Expert for Embodied Tasks
- **Year:** 2022 (NeurIPS 2022)
- **Authors / affiliation:** Kunal Pratap Singh, Luca Weihs, Alvaro Herrasti, Jonghyun Choi, Aniruddha Kembhavi, Roozbeh Mottaghi (AI2 / Yonsei)
- **URL:** https://arxiv.org/abs/2211.09960 ; https://proceedings.neurips.cc/paper_files/paper/2022/hash/674ad201bc8fa74b3c9979230aa0c63b-Abstract.html
- **What it does:** A separate GRU policy, trained with RL on top of a **frozen** agent, decides when to ask an expert. Rewards are r_fail, r_init_ask and r_step_ask. Section 3.3, "Adapting to User Preferences at Inference Time", argues that "some users might be happy to provide feedback during the day while others might find such requests highly disruptive". The authors therefore sample 30 reward configurations (r_fail from −1 to −30), embed the configuration as a 12-dimensional vector, and feed it to the policy. One policy can then adjust how often it asks to match a stated user preference without retraining. Results: ObjectNav success rises from 52% to 86% with 13% help.
- **Overlap with AgentPause:** Very close to AgentPause's **user-customized policy**. Asking is costed, the cost is set per user, the base agent is untouched (like middleware), and the trade-off between task performance and amount of help is explicit.
- **AgentPause would differ by:** Using explicit, interpretable signals (reversibility, severity, cognitive load) rather than an opaque GRU over agent belief. Learning preferences from decision history rather than a fixed dial. Adding DEFER timing, BLOCK, and explanations. Targeting LLM agents.
- **Direct competitor?** Partial (strong): the closest prior art for preference-conditioned asking.
- **Type:** Both (https://github.com/allenai/ask4help).

### 4.5 Asking Before Acting: Gather Information in Embodied Decision Making with Language Models (ABA)
- **Year:** 2023 (arXiv; v2 2024)
- **Authors / affiliation:** Xiaoyu Chen, Shenao Zhang, Pushi Zhang, Li Zhao, Jianyu Chen (Tsinghua / Microsoft Research Asia)
- **URL:** https://arxiv.org/abs/2305.15695
- **What it does:** LLM embodied agents ask external sources in natural language for missing information before acting; a fine-tuned variant (ABA-FT) improves this further.
- **Overlap with AgentPause:** Asking before acting.
- **AgentPause would differ by:** Including a cost, risk and timing model.
- **Direct competitor?** No.
- **Type:** Academic.

---

## 5. Clarification for LLMs and agents; intent-ambiguity benchmarks; user simulation

### 5.1 CLAM: Selective Clarification for Ambiguous Questions with Generative Language Models
- **Year:** 2022 (arXiv)
- **Authors / affiliation:** Lorenz Kuhn, Yarin Gal, Sebastian Farquhar (University of Oxford)
- **URL:** https://arxiv.org/abs/2212.07769
- **What it does:** First detects whether a question is ambiguous, asks a clarifying question only in that case, then answers.
- **Overlap with AgentPause:** Selective (not always-on) clarification.
- **AgentPause would differ by:** Handling actions, consequences, cost and timing.
- **Direct competitor?** No.
- **Type:** Academic.

### 5.2 Clarify When Necessary: Resolving Ambiguity Through Interaction with LMs
- **Year:** 2023 (arXiv)
- **Authors / affiliation:** Michael J.Q. Zhang, Eunsol Choi (UT Austin)
- **URL:** https://arxiv.org/abs/2311.09469
- **What it does:** Splits the problem into deciding whether to clarify, choosing the question, and answering. Its "intent-sim" method estimates entropy over simulated user intents to decide whether clarification is worthwhile, and beats other uncertainty estimators.
- **Overlap with AgentPause:** Gives AgentPause an "intent ambiguity" signal (entropy over intents).
- **AgentPause would differ by:** Combining ambiguity with consequence, cost and timing.
- **Direct competitor?** Partial (signal plus CLARIFY trigger).
- **Type:** Academic.

### 5.3 STaR-GATE: Teaching Language Models to Ask Clarifying Questions
- **Year:** 2024 (arXiv; COLM 2024 per my knowledge)
- **Authors / affiliation:** Chinmaya Andukuri, Jan-Philipp Fränken, Tobias Gerstenberg, Noah D. Goodman (Stanford)
- **URL:** https://arxiv.org/abs/2403.19154
- **What it does:** Self-improvement training that rewards questions which reveal a simulated user's hidden preferences (25.5k persona-task prompts).
- **Overlap with AgentPause:** Elicitation of preferences.
- **AgentPause would differ by:** Making the decision about when to interrupt, rather than how to ask.
- **Direct competitor?** No.
- **Type:** Academic.

### 5.4 CLAMBER: A Benchmark of Identifying and Clarifying Ambiguous Information Needs in LLMs
- **Year:** 2024 (ACL 2024)
- **Authors / affiliation:** Tong Zhang, Peixin Qin, Yang Deng, Chen Huang, Wenqiang Lei, Junhong Liu, Dingnan Jin, Hongru Liang, Tat-Seng Chua (Sichuan University / NUS et al.)
- **URL:** https://arxiv.org/abs/2405.12063
- **What it does:** About 12k examples organized by an ambiguity taxonomy. Finds LLMs poor at spotting ambiguity, with CoT and few-shot prompting fostering overconfidence.
- **Overlap with AgentPause:** Usable for evaluating the ambiguity signal.
- **AgentPause would differ by:** Not applicable (benchmark).
- **Direct competitor?** No.
- **Type:** Academic + benchmark.

### 5.5 Tell Me More! Towards Implicit User Intention Understanding of Language Model Driven Agents (IN3, Mistral-Interact)
- **Year:** 2024 (arXiv)
- **Authors / affiliation:** Cheng Qian, Bingxiang He, Zhong Zhuang, Jia Deng, Yujia Qin, Xin Cong, Zhong Zhang, Jie Zhou, Yankai Lin, Zhiyuan Liu, Maosong Sun (Tsinghua / Renmin)
- **URL:** https://arxiv.org/abs/2402.09205
- **What it does:** The IN3 benchmark covers vague agent tasks. Mistral-Interact detects vagueness, asks, and turns the answers into concrete goals before the agent (XAgent) executes.
- **Overlap with AgentPause:** An upfront CLARIFY stage in front of an agent.
- **AgentPause would differ by:** Making decisions mid-trajectory, covering action risk, and choosing timing.
- **Direct competitor?** Partial (weak).
- **Type:** Both (data and code stated as released).

### 5.6 Ask-before-Plan: Proactive Language Agents for Real-World Planning
- **Year:** 2024 (EMNLP 2024 Findings)
- **Authors / affiliation:** Xuan Zhang, Yang Deng, Zifeng Ren, See-Kiong Ng, Tat-Seng Chua (NUS)
- **URL:** https://arxiv.org/abs/2406.12639
- **What it does:** A Clarification-Execution-Planning multi-agent framework. A trajectory-tuned clarification agent predicts whether clarification is needed from the conversation **and the environment interactions**, then tools gather information before planning.
- **Overlap with AgentPause:** A learned "need to clarify" predictor that conditions on environment feedback.
- **AgentPause would differ by:** Adding a cost model, consequences, and DEFER/BLOCK.
- **Direct competitor?** Partial (weak).
- **Type:** Academic.

### 5.7 AskToAct: Enhancing LLMs Tool Use via Self-Correcting Clarification
- **Year:** 2025 (arXiv)
- **Authors / affiliation:** Xuan Zhang, Yongliang Shen, Zhe Zheng, Linjuan Wu, Wenqi Zhang, Yuchen Yan, Qiuying Peng, Jun Wang, Weiming Lu (Zhejiang University et al.)
- **URL:** https://arxiv.org/abs/2503.01940
- **What it does:** Builds clarification training data by removing key tool parameters from queries, and trains with error correction so models detect and fix mistakes during multi-turn clarification.
- **Overlap with AgentPause:** Clarifying missing tool arguments.
- **AgentPause would differ by:** Same contrast as 5.6.
- **Direct competitor?** No.
- **Type:** Academic.

### 5.8 Learning to Ask: When LLM Agents Meet Unclear Instruction (Ask-when-Needed, NoisyToolBench)
- **Year:** 2024 arXiv; EMNLP 2025
- **Authors / affiliation:** Wenxuan Wang, Juluan Shi, Zixuan Ling, Yuk-Kit Chan, Chaozheng Wang, Cheryl Lee, Youliang Yuan, Jen-tse Huang, Wenxiang Jiao, Michael R. Lyu (CUHK et al.)
- **URL:** https://arxiv.org/abs/2409.00557
- **What it does:** Shows that tool agents invent missing arguments. Ask-when-Needed prompts the agent to ask when instructions are unclear; ToolEvaluator automates evaluation.
- **Overlap with AgentPause:** Prompt-level CLARIFY in tool agents.
- **AgentPause would differ by:** Being an external policy with cost and risk modelling.
- **Direct competitor?** No.
- **Type:** Academic (code promised).

### 5.9 When2Call: When (not) to Call Tools
- **Year:** 2025 (NAACL 2025)
- **Authors / affiliation:** Hayley Ross, Ameya Sunil Mahabaleshwarkar, Yoshi Suhara (NVIDIA / Harvard)
- **URL:** https://arxiv.org/abs/2504.18851
- **What it does:** A benchmark and training set for choosing between calling a tool, asking a follow-up question, and abstaining.
- **Overlap with AgentPause:** Its decision space (act / clarify / abstain) is a subset of AgentPause's.
- **AgentPause would differ by:** Adding human approval, DEFER, consequence modelling, and user adaptivity.
- **Direct competitor?** Partial (evaluation resource).
- **Type:** Both (https://github.com/NVIDIA/When2Call).

### 5.10 When and What to Ask: AskBench and Rubric-Guided RLVR for LLM Clarification
- **Year:** 2026 (arXiv)
- **Authors / affiliation:** Jiale Zhao, Ke Fang, Lu Cheng
- **URL:** https://arxiv.org/abs/2602.11199
- **What it does:** Turns QA pairs into multi-turn interactions with checkpoints, covering underspecified queries (AskMind) and false premises (AskOverconfidence), and trains clarification with rubric-guided RLVR.
- **Overlap with AgentPause:** Learned "when to ask".
- **AgentPause would differ by:** Same contrast as 5.6.
- **Direct competitor?** No.
- **Type:** Academic.

### 5.11 Ambig-SWE: Interactive Agents to Overcome Underspecificity in Software Engineering
- **Year:** 2025 arXiv; ICLR 2026
- **Authors / affiliation:** Sanidhya Vijayvargiya, Xuhui Zhou, Akhila Yerukola, Maarten Sap, Graham Neubig (CMU)
- **URL:** https://arxiv.org/abs/2502.13069
- **What it does:** Shows that agents struggle to tell underspecified tasks from well-specified ones, but gain up to 74% when they do interact.
- **Overlap with AgentPause:** Evidence that detecting the need to ask is the bottleneck.
- **AgentPause would differ by:** Supplying the decision policy itself.
- **Direct competitor?** No (benchmark and analysis).
- **Type:** Academic.

### 5.12 Ask or Assume? Uncertainty-Aware Clarification-Seeking in Coding Agents
- **Year:** 2026 (EMNLP 2026 camera-ready)
- **Authors / affiliation:** Nicholas Edwards, Sebastian Schuster
- **URL:** https://arxiv.org/abs/2603.26233
- **What it does:** An uncertainty-aware multi-agent scaffold that separates detecting underspecification from executing code. It saves queries on simple tasks and seeks information on complex ones, reaching a 69.40% resolve rate on an underspecified SWE-bench Verified.
- **Overlap with AgentPause:** Architecture: a separate detector that sits beside the executor, like middleware.
- **AgentPause would differ by:** Adding consequence and reversibility, interruption cost, timing, and approvals.
- **Direct competitor?** Partial.
- **Type:** Academic.

### 5.13 τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains
- **Year:** 2024 (arXiv)
- **Authors / affiliation:** Shunyu Yao, Noah Shinn, Pedram Razavi, Karthik Narasimhan (Sierra)
- **URL:** https://arxiv.org/abs/2406.12045
- **What it does:** An LLM-simulated user and domain tools with policies; success is the final database state; pass^k measures reliability. Domain policies require explicit user confirmation before consequential actions (per my knowledge of the benchmark's policies).
- **Overlap with AgentPause:** A user-simulation testbed for AgentPause policies.
- **AgentPause would differ by:** Not applicable (benchmark).
- **Direct competitor?** No.
- **Type:** Both (https://github.com/sierra-research/tau-bench; the repo notes its tasks are outdated and points to τ³-bench).

### 5.14 τ²-Bench: Evaluating Conversational Agents in a Dual-Control Environment
- **Year:** 2025 (arXiv)
- **Authors / affiliation:** Victor Barres, Honghua Dong, Soham Ray, Xujie Si, Karthik Narasimhan (Sierra et al.)
- **URL:** https://arxiv.org/abs/2506.07982
- **What it does:** Both agent and user act on a shared environment (Telecom domain). Performance drops sharply in the dual-control setting.
- **Overlap with AgentPause:** A testbed where the timing of human involvement matters.
- **AgentPause would differ by:** Not applicable.
- **Direct competitor?** No.
- **Type:** Academic + benchmark.

### 5.15 Training Proactive and Personalized LLM Agents (PPP, UserVille)
- **Year:** 2025 arXiv; COLM 2026
- **Authors / affiliation:** Weiwei Sun, Xuhui Zhou, Weihua Du, Xingyao Wang, Sean Welleck, Graham Neubig, Maarten Sap, Yiming Yang (CMU et al.)
- **URL:** https://arxiv.org/abs/2511.02208
- **What it does:** Multi-objective RL over Productivity, Proactivity (asking, rewarded with a **question-effort** term) and Personalization (following user preferences), using configurable LLM user simulators. PPP agents beat GPT-5 by 16.7 points on average on SWE-Bench and BrowseComp-Plus.
- **Overlap with AgentPause:** Learned asking with a user-effort cost and per-user preferences.
- **AgentPause would differ by:** Being model-agnostic middleware rather than fine-tuning the agent. Adding risk, reversibility and DEFER/BLOCK, explicit timing, and explanations.
- **Direct competitor?** Partial.
- **Type:** Academic.

### 5.16 Ask Now, Use Later: Benchmarking the Proactivity Gap in Long-Lived LLM Agents (ATRBench)
- **Year:** 2026 (EMNLP 2026 Main)
- **Authors / affiliation:** Bin Wu, Guanyun Zou, Bingbing Wang, Huan Zhao, Chuan Shi (BUPT et al.)
- **URL:** https://arxiv.org/abs/2605.28108
- **What it does:** "Ask-to-Remember": an agent should ask **now** for a reusable preference that only a later session will need. Frontier agents trail an oracle by at least 62 points.
- **Overlap with AgentPause:** The timing of asking across sessions: ask while the user is available, use the answer later.
- **AgentPause would differ by:** Making the within-trajectory decision to interrupt for an action. It could reuse ATR's idea to front-load questions so that asks are DEFERred less often.
- **Direct competitor?** Partial (timing angle).
- **Type:** Academic + benchmark.

---

## 6. Timing of the ask as the decision variable

### 6.1 Ask Early, Ask Late, Ask Right: When Does Clarification Timing Matter for Long-Horizon Agents?
- **Year:** 2026 (arXiv, May 2026)
- **Authors / affiliation:** Anmol Gulati, Hariom Gupta, Elias Lumer, Sahil Sen, Vamse Kumar Subbiah (PricewaterhouseCoopers U.S.)
- **URL:** https://arxiv.org/abs/2605.07937
- **What it does:** A "forced injection" framework. Ground-truth clarifications are inserted at 10/30/50/70/90% of an oracle-calibrated action budget, with `ask_user` disabled. It covers four kinds of missing information (goal, input, constraint, context), three benchmarks (MCP-Atlas, TheAgentCompany, SWE-Bench Pro), four models, 84 variants and 6,000+ runs. Findings: **goal clarification loses almost all value after about 10% of execution**; input clarification stays useful to about 50%; constraint clarification is best before execution starts; **asking any type after mid-trajectory is worse than never asking**. Timing profiles are largely intrinsic to the task (cross-model Kendall τ 0.78–0.87). In 300 unscripted sessions no frontier model asks inside the optimal window, and 52% of sessions over-ask. No policy is proposed; the demand curves are offered as design targets.
- **Overlap with AgentPause:** It directly measures AgentPause's core premise that **when** to ask matters, by information type. It also gives empirical grounding for "why not later" explanations.
- **AgentPause would differ by:** Supplying the missing **policy**. AgentPause would decide online when to ask, and would cover approval of irreversible steps, not only clarifications. Caution: these results suggest DEFER is harmful for goal and constraint questions, so AgentPause should only defer questions that can safely wait (for example approval right before an irreversible commit), not ambiguity about the goal.
- **Direct competitor?** Partial. It is evidence and a benchmark more than a system, and it is the strongest citation for timing.
- **Type:** Academic (code and data "will be publicly released").

### 6.2 Learning-to-defer for sequential medical decision-making under uncertainty (SLTD)
- **Year:** 2021 (arXiv; v2 2022)
- **Authors / affiliation:** Shalmali Joshi, Sonali Parbhoo, Finale Doshi-Velez (Harvard)
- **URL:** https://arxiv.org/abs/2109.06312
- **What it does:** Treats deferral to an expert as model-based RL over long-term outcomes. At each step it estimates whether **deferring now beats waiting until the next step**, and can defer early when the ML policy is likely to worsen long-term outcomes.
- **Overlap with AgentPause:** Treats timing explicitly; this is the closest formal analogue of DEFER versus ASK_HUMAN now.
- **AgentPause would differ by:** Operating in LLM-agent action spaces, with interruption cost, user preferences, and explanations.
- **Direct competitor?** Partial (formal timing precedent).
- **Type:** Academic.

(Other timing-relevant items, catalogued in their own sections: Horvitz 1999 (1.1), Scerri et al. 2002 (1.2), Ask Now Use Later (5.16), PAINT (10.4), ProbGuard (11.9), Self-Regulation (9.2), LazyDAgger (8.3).)

---

## 7. Learning to defer, selective prediction, abstention

### 7.1 Predict Responsibly: Improving Fairness and Accuracy by Learning to Defer
- **Year:** 2017 arXiv; NeurIPS 2018
- **Authors / affiliation:** David Madras, Toniann Pitassi, Richard Zemel (University of Toronto / Vector)
- **URL:** https://arxiv.org/abs/1711.06664
- **What it does:** Extends rejection learning so the model predicts or defers to a downstream human, taking into account how that human (including their biases) will affect the outcome.
- **Overlap with AgentPause:** Deferral that accounts for who the human is.
- **AgentPause would differ by:** Handling sequential actions, interruption cost, and timing.
- **Direct competitor?** No.
- **Type:** Academic.

### 7.2 Consistent Estimators for Learning to Defer to an Expert
- **Year:** 2020 (ICML 2020)
- **Authors / affiliation:** Hussein Mozannar, David Sontag (MIT)
- **URL:** https://arxiv.org/abs/2006.01862
- **What it does:** Reduces learning to defer to cost-sensitive learning and gives a consistent surrogate loss, learned from samples of the expert's decisions.
- **Overlap with AgentPause:** A principled learned deferral rule. AgentPause's "history of user decisions" could train such a deferral classifier.
- **AgentPause would differ by:** Same contrast as 7.1.
- **Direct competitor?** No.
- **Type:** Academic.

### 7.3 Cost-Sensitive Learning to Defer to Multiple Experts with Workload Constraints (DeCCaF)
- **Year:** 2024 (arXiv)
- **Authors / affiliation:** Jean V. Alves, Diogo Leitão, Sérgio Jesus, Marco O. P. Sampaio, Javier Liébana, Pedro Saleiro, Mário A. T. Figueiredo, Pedro Bizarro (Feedzai / IST Lisbon)
- **URL:** https://arxiv.org/abs/2403.06906
- **What it does:** Deferral with asymmetric error costs and **limited reviewer capacity**, solved with constraint programming.
- **Overlap with AgentPause:** Treats human capacity as a constraint, which is closely related to interruption budget and cognitive load.
- **AgentPause would differ by:** Same contrast as 7.1.
- **Direct competitor?** No.
- **Type:** Academic.

### 7.4 Know Your Limits: A Survey of Abstention in Large Language Models
- **Year:** 2024 arXiv; TACL
- **Authors / affiliation:** Bingbing Wen, Jihan Yao, Shangbin Feng, Chenjun Xu, Yulia Tsvetkov, Bill Howe, Lucy Lu Wang (University of Washington)
- **URL:** https://arxiv.org/abs/2407.18418
- **What it does:** A taxonomy of LLM abstention methods, benchmarks and metrics, organized by query, model and human values.
- **Overlap with AgentPause:** Background for BLOCK and abstain behaviour.
- **AgentPause would differ by:** Not applicable (survey).
- **Direct competitor?** No.
- **Type:** Academic.

### 7.5 AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions
- **Year:** 2025 (arXiv)
- **Authors / affiliation:** Polina Kirichenko, Mark Ibrahim, Kamalika Chaudhuri, Samuel J. Bell (Meta FAIR)
- **URL:** https://arxiv.org/abs/2506.09038
- **What it does:** 20 datasets of unanswerable, underspecified or false-premise questions. Reasoning fine-tuning lowers abstention by about 24%.
- **Overlap with AgentPause:** Evidence that agents cannot be trusted to self-abstain, which motivates an external gate.
- **AgentPause would differ by:** Not applicable.
- **Direct competitor?** No.
- **Type:** Academic + benchmark.

### 7.6 AgentAbstain: Do LLM Agents Know When Not to Act?
- **Year:** 2026 (arXiv, July 2026)
- **Authors / affiliation:** Xun Liu, Yi Evie Zhang, Vira Kasprova, Parisa Rabbani, Pardis Sadat Zahraei, Tianyu Zhang, Ali Ebrahimpour-Boroojeny, Varun Chandrasekaran (UIUC et al.)
- **URL:** https://arxiv.org/abs/2607.10059
- **What it does:** 263 paired tasks (should act / should abstain) in 42 sandboxes, with an 8-scenario taxonomy. The best model (Gemini 3.1 Pro) reaches 59.5% paired accuracy. Identifies "post-hoc abstention", where **agents take irreversible actions before recognizing the trigger**.
- **Overlap with AgentPause:** Directly motivates gating before irreversible actions and is a ready evaluation set for BLOCK/ASK.
- **AgentPause would differ by:** Being a system that reduces post-hoc abstention.
- **Direct competitor?** No (benchmark). Use it for evaluation.
- **Type:** Both (http://agentabstain.github.io).

---

## 8. Interactive imitation learning with intervention budgets (robotics)

### 8.1 SafeDAgger (paper title: "Query-Efficient Imitation Learning for End-to-End Autonomous Driving")
- **Year:** 2016 arXiv; AAAI 2017 (venue per my knowledge)
- **Authors / affiliation:** Jiakai Zhang, Kyunghyun Cho (NYU)
- **URL:** https://arxiv.org/abs/1605.06450
- **What it does:** A learned safety classifier predicts whether the novice policy's action would deviate too far from the reference (expert). If so, the expert takes over and is queried. This makes DAgger query-efficient.
- **Overlap with AgentPause:** A learned "unsafe, hand over to human" gate.
- **AgentPause would differ by:** Covering LLM agents, multi-signal cost, and user-facing explanations.
- **Direct competitor?** No.
- **Type:** Academic.

### 8.2 EnsembleDAgger: A Bayesian Approach to Safe Imitation Learning
- **Year:** 2018 arXiv; IROS 2019
- **Authors / affiliation:** Kunal Menda, Katherine Driggs-Campbell, Mykel J. Kochenderfer (Stanford)
- **URL:** https://arxiv.org/abs/1807.08364
- **What it does:** Uses ensemble variance as novice confidence. A decision rule lets the novice act as much as possible while bounding the probability of failure.
- **Overlap with AgentPause:** Uncertainty-gated handover with a risk constraint.
- **AgentPause would differ by:** Same contrast as 8.1.
- **Direct competitor?** No.
- **Type:** Academic.

### 8.3 LazyDAgger: Reducing Context Switching in Interactive Imitation Learning
- **Year:** 2021 (IEEE CASE 2021)
- **Authors / affiliation:** Ryan Hoque, Ashwin Balakrishna, Carl Putterman, Michael Luo, Daniel S. Brown, Daniel Seita, Brijen Thananjeyan, Ellen Novoseller, Ken Goldberg (UC Berkeley AUTOLAB)
- **URL:** https://arxiv.org/abs/2104.00053
- **What it does:** Extends SafeDAgger to cut **context switches** between human and robot (about 60% fewer), on the grounds that each handoff interrupts the human's other work. It does this with asymmetric switching that makes interventions longer but rarer (mechanism detail per my reading; the abstract confirms the context-switch goal).
- **Overlap with AgentPause:** Treats **interruption or context-switch cost** as a first-class objective, which matches AgentPause's interruption-cost signal and its batching/DEFER idea.
- **AgentPause would differ by:** Same contrast as 8.1, plus timing explanations.
- **Direct competitor?** Partial (conceptual).
- **Type:** Academic.

### 8.4 ThriftyDAgger: Budget-Aware Novelty and Risk Gating for Interactive Imitation Learning
- **Year:** 2021 (CoRL 2021, oral)
- **Authors / affiliation:** Ryan Hoque, Ashwin Balakrishna, Ellen Novoseller, Albert Wilcox, Daniel S. Brown, Ken Goldberg (UC Berkeley)
- **URL:** https://arxiv.org/abs/2109.08273
- **What it does:** Queries the human only when a state is **novel** (no reference behaviour to imitate; measured by ensemble disagreement) or **risky** (low estimated probability of completing the task, from a learned Q-function), under a **desired budget of human interventions**. Thresholds are set to meet the target intervention rate (mechanism detail per my reading; the abstract confirms novelty and risk gating with a budget). Validated with a cable-routing task and a 10-person user study.
- **Overlap with AgentPause:** Multi-signal gating (uncertainty plus risk) under an interruption budget. This is the robotics analogue of AgentPause's adaptive policy.
- **AgentPause would differ by:** Using a richer signal set (reversibility, intent ambiguity, preferences), more action types (CLARIFY/DEFER/BLOCK), and explanations, in an LLM-agent setting.
- **Direct competitor?** Partial. Recommended as a baseline ("risk + novelty gating with a budget").
- **Type:** Academic.

### 8.5 Fleet-DAgger: Interactive Robot Fleet Learning with Scalable Human Supervision
- **Year:** 2022 (CoRL 2022, oral)
- **Authors / affiliation:** Ryan Hoque, Lawrence Yunliang Chen, Satvik Sharma, Karthik Dharmarajan, Brijen Thananjeyan, Pieter Abbeel, Ken Goldberg (UC Berkeley)
- **URL:** https://arxiv.org/abs/2206.14349
- **What it does:** Interactive Fleet Learning: many robots, few humans. Robots are ranked for human attention by a priority function (for example uncertainty, risk or constraint violation), and the paper introduces the metric "Return on Human Effort". Up to 8.8× higher return in 100-robot simulations.
- **Overlap with AgentPause:** Treats human attention as a scarce resource; relevant if AgentPause handles many concurrent agents per user.
- **AgentPause would differ by:** Same contrast as 8.4.
- **Direct competitor?** Partial (weak).
- **Type:** Academic (open-source Isaac Gym benchmark mentioned in the paper).

---

## 9. Learned intervention policies and human-in-the-loop systems for LLM agents

### 9.1 Large Language Model-based Human-Agent Collaboration for Complex Task Solving (ReHAC)
- **Year:** 2024 (arXiv)
- **Authors / affiliation:** Xueyang Feng, Zhi-Yuan Chen, Yujia Qin, Yankai Lin, Xu Chen, Zhiyuan Liu, Ji-Rong Wen (Renmin University / Tsinghua)
- **URL:** https://arxiv.org/abs/2402.12914
- **What it does:** At each step, an offline-RL collaboration policy decides whether the human or the agent handles the subtask. Reward R = T − λ·C, with C the number of human interventions. A few well-timed interventions give large gains.
- **Overlap with AgentPause:** A learned per-step "ask the human" policy with an intervention cost.
- **AgentPause would differ by:** Using interpretable multi-signal features, reversibility and severity, preference adaptation from history, DEFER/BLOCK, and explanations. ReHAC's λ is a fixed hyperparameter.
- **Direct competitor?** Partial (strong).
- **Type:** Both (https://github.com/XueyangFeng/ReHAC).

### 9.2 Self-Regulation and Requesting Interventions
- **Year:** 2025 (arXiv)
- **Authors / affiliation:** So Yeon Min, Yue Wu, Jimin Sun, Max Kaufmann, Fahim Tajwar, Yonatan Bisk, Ruslan Salakhutdinov (CMU)
- **URL:** https://arxiv.org/abs/2502.04576
- **What it does:** A process reward model estimates success probability p(s). Transition statistics are collected by triggering interventions at random rates. Dynamic programming computes expected intervention usage M_s, and **help is chosen iff the per-intervention cost r < Δp_s / ΔM_s** (extra success divided by extra usage). r is found by binary search so that expected usage matches the budget C, and a LLaMA-3B helper is distilled from the DP policy. Plain PRM thresholds caused toggling. The interventions are a stronger LLM or MCTS, not humans (humans appear only as motivation).
- **Overlap with AgentPause:** A formal cost/benefit rule for **when in a trajectory** to intervene, under a budget. Its finding that naive thresholds toggle is directly relevant to AgentPause's fixed-threshold baseline.
- **AgentPause would differ by:** Making the human the intervener, with costs that depend on load and preferences, plus reversibility, severity, explanations, and DEFER to breakpoints.
- **Direct competitor?** Partial (strong; methodologically the closest learned timing policy).
- **Type:** Academic.

### 9.3 Requesting Expert Reasoning: Augmenting LLM Agents with Learned Collaborative Intervention (AHCE)
- **Year:** 2026 (arXiv)
- **Authors / affiliation:** Zhiming Wang, Jinwei He, Feng Lu
- **URL:** https://arxiv.org/abs/2602.22546
- **What it does:** A learned Human Feedback Module policy requests specific reasoning from a human expert on demand (Minecraft). Reported gains: 32% on normal tasks and about 70% on very difficult tasks, with minimal human involvement.
- **Overlap with AgentPause:** A learned on-demand human query.
- **AgentPause would differ by:** Same contrast as 9.1.
- **Direct competitor?** Partial.
- **Type:** Academic.

### 9.4 Modeling Distinct Human Interaction in Web Agents (CowCorpus; PlowPilot)
- **Year:** 2026 (arXiv Feb 2026, v4 Jul 2026)
- **Authors / affiliation:** Faria Huq, Zora Zhiruo Wang, Zhanqiu Guo, Venu Arvind Arangarajan, Tianyue Ou, Frank Xu, Shuyan Zhou, Graham Neubig, Jeffrey P. Bigham (CMU; Duke)
- **URL:** https://arxiv.org/abs/2602.17588
- **What it does:** Motivation: agents "proceed past key decision points or ask for unnecessary confirmation." CowCorpus has 400 real-user web trajectories with 4,200+ interleaved human and agent actions, and identifies four styles: takeover, hands-on, hands-off, collaborative. A fine-tuned LM makes a **per-step binary prediction (`<ask_user>` vs `<agent_continue>`)** for each **proposed action**, given the interaction history, a screenshot plus accessibility tree, and the proposed action. Adding the human-action history raised step accuracy from 76.27% to 81.36% in one ablation. Prediction accuracy improves 61.4–63.4% over base LMs. In the deployed Chrome extension **PlowPilot**, the agent "prompts for intervention only at moments where the model predicts a high likelihood". A user study reports about 26.5–36.8% higher rated usefulness (the figure differs between versions).
- **Overlap with AgentPause:** This is AgentPause's core loop (proposed action plus context → ask or continue), learned from **user intervention history and style**, deployed live, and evaluated against confirm-every-step.
- **AgentPause would differ by:** Using explicit consequence signals (severity, reversibility) instead of imitating when users intervened. Having a richer action space (CLARIFY / DEFER / BLOCK). Reasoning about timing (why not earlier/later). Producing explanations. Comparing policies, including a decision-theoretic one. PlowPilot predicts human behaviour, not the value of intervening; AgentPause could combine the two (P(user would intervene) × cost of not asking).
- **Direct competitor?** **Yes.** It is the closest LLM-agent system and the closest learned, user-style-adaptive confirmation policy.
- **Type:** Both (code https://github.com/oaishi/PlowPilot; models https://huggingface.co/CowCorpus; dataset release location not stated).

### 9.5 CowPilot: A Framework for Autonomous and Human-Agent Collaborative Web Navigation
- **Year:** 2025 (NAACL 2025 System Demonstrations)
- **Authors / affiliation:** Faria Huq, Zora Zhiruo Wang, Frank F. Xu, Tianyue Ou, Shuyan Zhou, Jeffrey P. Bigham, Graham Neubig (CMU)
- **URL:** https://arxiv.org/abs/2501.16609
- **What it does:** The agent proposes next steps; the user can pause, reject, take an alternative action, or hand control back.
- **Overlap with AgentPause:** The interaction substrate (human-initiated pause) that CowCorpus and PlowPilot later make adaptive.
- **AgentPause would differ by:** Initiating the pause from the agent side, adaptively.
- **Direct competitor?** Partial.
- **Type:** Both (demo at oaishi.github.io/cowpilot.html; repository not linked on arXiv).

### 9.6 Collaborative Gym: A Framework for Enabling and Evaluating Human-Agent Collaboration
- **Year:** 2024 arXiv; ICLR 2026
- **Authors / affiliation:** Yijia Shao, Vinay Samuel, Yucheng Jiang, John Yang, Diyi Yang (Stanford)
- **URL:** https://arxiv.org/abs/2412.15701
- **What it does:** A non-turn-taking (asynchronous) human-agent collaboration framework covering travel planning, tabular analysis and related-work writing. Reports communication failures in 65% of real cases and situational-awareness failures in 40%.
- **Overlap with AgentPause:** An asynchronous testbed where the agent decides when to message the human.
- **AgentPause would differ by:** Being a decision policy rather than an environment.
- **Direct competitor?** Partial (evaluation substrate).
- **Type:** Both (MIT-licensed release stated).

### 9.7 Magentic-UI: Towards Human-in-the-loop Agentic Systems
- **Year:** 2025 (arXiv)
- **Authors / affiliation:** Hussein Mozannar, Gagan Bansal, Cheng Tan, Adam Fourney, Victor Dibia, … Ece Kamar, Saleema Amershi (20 authors; Microsoft Research AI Frontiers)
- **URL:** https://arxiv.org/abs/2507.22358
- **What it does:** Open-source human-in-the-loop agent UI with co-planning, co-tasking, multitasking, **action guards** and memory. ActionGuard: each action type has a developer-set irreversibility label (**always irreversible**, e.g. file upload, always asks the user; **maybe**, e.g. clicking a button, goes to an LLM judge that decides whether approval is needed; **never**, e.g. scrolling, runs automatically). There is also a website allow-list. In a 12-person qualitative study, users endorsed approvals for payments, emails and subscriptions, and found approvals for adding to a cart, or after a plan change, unnecessary. It does not report how often users were asked and has no user-adjustable policy.
- **Overlap with AgentPause:** A shipped, reversibility-based confirmation gate with an LLM judge. It covers the "fixed risk threshold" and "LLM-judged" parts of AgentPause's policy set.
- **AgentPause would differ by:** Using continuous multi-signal scoring instead of developer labels. Including interruption cost and cognitive load, per-user learning from approve/deny history, and DEFER/timing. Producing explanations. Running a quantitative policy comparison.
- **Direct competitor?** **Yes (system level).** It is the most direct open-source baseline to implement against.
- **Type:** Both (https://github.com/microsoft/magentic-ui).

### 9.8 Human-In-the-Loop Software Development Agents (HULA)
- **Year:** 2024 arXiv; ICSE SEIP 2025
- **Authors / affiliation:** Wannita Takerngsaksiri, Jirat Pasuksmit, Patanamon Thongtanunam, Chakkrit Tantithamthavorn, Ruixiong Zhang, Fan Jiang, Jing Li, Evan Cook, Kun Chen, Ming Wu (Monash / Atlassian)
- **URL:** https://arxiv.org/abs/2411.12924
- **What it does:** Engineers review and steer the agents at two fixed stages: the coding plan and the code. Deployed inside Atlassian JIRA.
- **Overlap with AgentPause:** Human-in-the-loop checkpoints at natural breakpoints (fixed stages).
- **AgentPause would differ by:** Choosing checkpoints adaptively rather than at fixed stage gates.
- **Direct competitor?** Partial (an example of the fixed-stage baseline).
- **Type:** Academic (industrial deployment).

### 9.9 Proactive Agent: Shifting LLM Agents from Reactive Responses to Active Assistance
- **Year:** 2024 (arXiv)
- **Authors / affiliation:** Yaxi Lu, Shenzhi Yang, Cheng Qian, … Zhiyuan Liu, Fangming Liu, Maosong Sun (Tsinghua et al.)
- **URL:** https://arxiv.org/abs/2410.12361
- **What it does:** A reward model trained on human accept/reject labels judges whether a proactive offer of help is welcome (ProactiveBench, 6,790 events, F1 66.47%).
- **Overlap with AgentPause:** Learns from accept/reject history whether an interruption is welcome.
- **AgentPause would differ by:** Gating risky actions rather than offering help, and adding timing and explanations.
- **Direct competitor?** Partial (weak).
- **Type:** Academic.

### 9.10 Oversight Has a Capacity: Calibrating Agent Guards to a Subjective, Fatiguing Human
- **Year:** 2026 (arXiv, June 2026)
- **Authors / affiliation:** Emre Turan
- **URL:** https://arxiv.org/abs/2606.08919
- **What it does:** Treats the LLM-agent approval gate as selective classification under asymmetric cost, with a **reviewer whose effectiveness drops as escalation load grows**. Reviewers agree only moderately on what is risky (Fleiss' κ = 0.52 on 125 actions). **Realized safety is an inverted U in escalation rate**: "more human oversight can make a system less safe". A load-aware policy resists flooding attacks. These are modelling results; a human study is still to come.
- **Overlap with AgentPause:** Directly supports including cognitive load and fatigue in AgentPause, and shows "always confirm" is not safety-optimal.
- **AgentPause would differ by:** Using a full context signal set, timing/DEFER, preferences, and explanations. AgentPause can cite this as a model-based argument for adaptive gating.
- **Direct competitor?** Partial.
- **Type:** Both (https://github.com/turangenesis/headroom).

### 9.11 Reframing LLM Agent Security as an Agent-Human Interaction Problem
- **Year:** 2026 (arXiv)
- **Authors / affiliation:** Peiran Wang, Ying Li, Yuan Tian (UCLA, per my knowledge)
- **URL:** https://arxiv.org/abs/2605.24309
- **What it does:** Surveys 59 papers, 21 production agents and 26 plugins. Runtime approval, policy specification and scope configuration each ship in at least 14 of the 21 systems. Identifies the trade-off between **approval fatigue** and uncontrolled autonomy.
- **Overlap with AgentPause:** States the problem AgentPause targets.
- **AgentPause would differ by:** Not applicable (survey and position paper).
- **Direct competitor?** No.
- **Type:** Academic.

---

## 10. Irreversibility, recoverability, undo

### 10.1 Leave no Trace: Learning to Reset for Safe and Autonomous Reinforcement Learning
- **Year:** 2017 arXiv; ICLR 2018 (venue per my knowledge)
- **Authors / affiliation:** Benjamin Eysenbach, Shixiang Gu, Julian Ibarz, Sergey Levine (Google Brain / Cambridge / Berkeley)
- **URL:** https://arxiv.org/abs/1711.06782
- **What it does:** A reset policy's value function detects when the forward policy is about to enter an irreversible state and **aborts early**.
- **Overlap with AgentPause:** Uses reversibility as a reason to intervene before acting.
- **AgentPause would differ by:** Asking a human rather than resetting, and adding cost and preferences.
- **Direct competitor?** No.
- **Type:** Academic.

### 10.2 Penalizing side effects using stepwise relative reachability
- **Year:** 2018 (arXiv)
- **Authors / affiliation:** Victoria Krakovna, Laurent Orseau, Ramana Kumar, Miljan Martic, Shane Legg (DeepMind)
- **URL:** https://arxiv.org/abs/1806.01186
- **What it does:** A side-effect penalty based on reduced reachability of states, measured against a stepwise inaction baseline.
- **Overlap with AgentPause:** A formal reversibility measure that could inform the "recoverability" signal.
- **AgentPause would differ by:** Using the signal to decide about the human rather than as a training penalty.
- **Direct competitor?** No.
- **Type:** Academic.

### 10.3 There Is No Turning Back: A Self-Supervised Approach for Reversibility-Aware Reinforcement Learning
- **Year:** 2021 (arXiv; NeurIPS 2021 per my knowledge)
- **Authors / affiliation:** Nathan Grinsztajn, Johan Ferret, Olivier Pietquin, Philippe Preux, Matthieu Geist (Inria / Google Research)
- **URL:** https://arxiv.org/abs/2106.04480
- **What it does:** Learns to estimate how reversible an action is, through a self-supervised task of ordering trajectory events in time, and uses the estimate for safe exploration and control.
- **Overlap with AgentPause:** A learned reversibility estimator.
- **AgentPause would differ by:** Same contrast as 10.2.
- **Direct competitor?** No.
- **Type:** Academic.

### 10.4 When to Ask for Help: Proactive Interventions in Autonomous Reinforcement Learning (PAINT)
- **Year:** 2022 (NeurIPS 2022)
- **Authors / affiliation:** Annie Xie, Fahim Tajwar, Archit Sharma, Chelsea Finn (Stanford)
- **URL:** https://arxiv.org/abs/2210.10765
- **What it does:** Learns to recognize irreversible states (for example an object knocked off a table), steers away from them, and **asks a human to intervene** when it enters one, which is better than waiting for a fixed reset. Improves both sample and intervention efficiency.
- **Overlap with AgentPause:** Reversibility triggers asking for help, and the help is proactive rather than scheduled.
- **AgentPause would differ by:** Asking **before** the irreversible step (pre-commit confirmation) rather than after reaching an unrecoverable state. Adding uncertainty, preferences, and cost.
- **Direct competitor?** Partial.
- **Type:** Both (project https://sites.google.com/view/proactive-interventions).

### 10.5 Avoiding Catastrophe in Online Learning by Asking for Help
- **Year:** 2024 arXiv; ICML 2025
- **Authors / affiliation:** Benjamin Plaut, Hanlin Zhu, Stuart Russell (UC Berkeley)
- **URL:** https://arxiv.org/abs/2402.08062
- **What it does:** Online learning with irreversible catastrophes. The objective is the product of per-round probabilities of avoiding catastrophe, and the mentor can be queried only a limited number of times. Without the ability to ask, an agent must query constantly or face catastrophe; when the mentor's policy class is learnable, regret and query rate both go to 0.
- **Overlap with AgentPause:** Theory that asking for help makes safe learning possible under irreversibility, with a limited query budget.
- **AgentPause would differ by:** Being a practical system with user costs.
- **Direct competitor?** No (theoretical foundation).
- **Type:** Academic.

### 10.6 Safe Learning Under Irreversible Dynamics via Asking for Help
- **Year:** 2025 arXiv; accepted to JMLR
- **Authors / affiliation:** Benjamin Plaut, Juan Liévano-Karim, Hanlin Zhu, Stuart Russell (UC Berkeley)
- **URL:** https://arxiv.org/abs/2502.14043
- **What it does:** Follows a default policy in familiar states and asks the mentor in unfamiliar ones, transferring knowledge across similar states and trading query frequency against error size.
- **Overlap with AgentPause:** A novelty plus irreversibility asking rule.
- **AgentPause would differ by:** Same contrast as 10.5.
- **Direct competitor?** No.
- **Type:** Academic.

### 10.7 GoEX: Perspectives and Designs Towards a Runtime for Autonomous LLM Applications
- **Year:** 2024 (arXiv)
- **Authors / affiliation:** Shishir G. Patil, Tianjun Zhang, Vivian Fang, Noppapon C., Roy Huang, Aaron Hao, Martin Casado, Joseph E. Gonzalez, Raluca Ada Popa, Ion Stoica (UC Berkeley)
- **URL:** https://arxiv.org/abs/2404.06921
- **What it does:** Proposes **post-facto validation**: the human checks outcomes rather than reviewing actions in advance. Provides **undo** and **damage confinement** so actions are reversible or bounded. The Gorilla Execution Engine runtime implements this.
- **Overlap with AgentPause:** Offers the alternative strategy of making actions reversible so you don't need to ask. AgentPause's reversibility signal could read GoEX-style undo availability.
- **AgentPause would differ by:** Deciding pre-action and on timing. The two are complementary: when an action is undoable, AgentPause can CONTINUE and validate afterwards.
- **Direct competitor?** Partial.
- **Type:** Both (https://github.com/ShishirPatil/gorilla/).

### 10.8 Revisable by Design: A Theory of Streaming LLM Agent Execution
- **Year:** 2026 (arXiv)
- **Authors / affiliation:** Zhiyuan Zhai, Ming Li, Xin Wang
- **URL:** https://arxiv.org/abs/2604.23283
- **What it does:** Agent execution and user intervention run concurrently. Actions are classed as idempotent, reversible, compensable or irreversible. The paper proves that "flexibility is bounded by reversibility": conflicting irreversible actions make full satisfaction of the specification impossible. Its Revision Absorber uses an Earliest-Conflict Rollback rule, evaluated on StreamBench.
- **Overlap with AgentPause:** A reversibility taxonomy plus mid-execution user intervention, which formally motivates pausing before irreversible actions.
- **AgentPause would differ by:** Gating before commitment rather than absorbing revisions afterwards.
- **Direct competitor?** Partial.
- **Type:** Academic.

### 10.9 Predicting What Changes: Causal Delta World Models for Risk-Aware LLM Agent Planning (CDWM)
- **Year:** 2026 (NeurIPS 2026 poster)
- **Authors / affiliation:** Guo Yue, Yang Liu, Donghui Zhang, Tang Qingkang, Rong Fu, Li Aoyu
- **URL:** https://neurips.cc/virtual/2026/poster/154820 (OpenReview https://openreview.net/forum?id=AiYvJPM2Oy)
- **What it does:** Predicts structured state changes and explicitly estimates **reversibility, irreversible cost and confidence**. The planner prunes catastrophic actions and **abstains when confidence is low**. Reports 47–71% fewer irreversible failures on WebArena, Mind2Web, ALFWorld and others.
- **Overlap with AgentPause:** Combines reversibility, cost and confidence to decide whether to act.
- **AgentPause would differ by:** Bringing in the human (ask, clarify, defer), user preferences, interruption cost, and explanations.
- **Direct competitor?** Partial (could provide AgentPause's reversibility and severity estimates).
- **Type:** Academic.

### 10.10 GateArena: Environment-Enforced Confirmation for Irreversible Agent Actions
- **Year:** 2026 (NeurIPS 2026 workshop: Agents in the Wild)
- **Authors / affiliation:** Lan Jiang, Francesco Quinzan, Umang Bhatt
- **URL:** https://neurips.cc/virtual/2026/168290 (OpenReview https://openreview.net/forum?id=2fckzsPCbK)
- **What it does:** Shows that "ask the user first" instructions in system prompts are unreliable: backbones attempted a withheld confirmation tool in 38%, 48% and under 1% of episodes. Proposes **warrant tokens** bound to exact parameter values and enforced by the tool handler. Across 1,880 episodes, irreversible harm fell from 37.5–60% to 2.5%, and protocol-violating executions from 91/400 to 0/400.
- **Overlap with AgentPause:** Strong evidence that confirmation must be **enforced outside the model**, which is AgentPause's middleware position.
- **AgentPause would differ by:** Deciding **when** to require a warrant adaptively. GateArena only enforces a confirmation once it has been decided on.
- **Direct competitor?** Partial (complementary enforcement layer).
- **Type:** Both (code, environment and logs stated as released; location not given on the page).

### 10.11 Same Action, Different Justification: Path-Based Authorization for Irreversible Agent Actions
- **Year:** 2026 (ICML 2026 workshop: Failure Modes in Agentic AI)
- **Authors / affiliation:** Jungsoo Baek
- **URL:** https://icml.cc/virtual/2026/77995 (OpenReview https://openreview.net/forum?id=6nnfJ7GVOX)
- **What it does:** Causal-Chain Authorization checks whether an irreversible action traces back to an authenticated user request. On a matched-pair benchmark it separates cases that keyword guards and LLM judges cannot.
- **Overlap with AgentPause:** Gating irreversible actions; provenance could be a signal.
- **AgentPause would differ by:** Weighing human cost and timing.
- **Direct competitor?** No.
- **Type:** Academic.

### 10.12 Preemptive Detection and Correction of Misaligned Actions in LLM Agents (InferAct)
- **Year:** 2024 arXiv; EMNLP 2025
- **Authors / affiliation:** Haishuo Fang, Xiaodan Zhu, Iryna Gurevych (TU Darmstadt UKP; Queen's University)
- **URL:** https://arxiv.org/abs/2407.11843
- **What it does:** Triggered **only at expert-listed critical actions** (for example WebShop "Buy Now", ALFWorld Clean/Heat/Cool, which can cause irreversible state changes). An LLM infers the task the agent appears to be pursuing (Theory-of-Mind style) and checks whether it entails the user's task and is still progressing toward it. If misalignment is flagged (verbal or probability threshold), it **alerts the human** for judgment and feedback, with human review capped at 50% of tasks; false alarms use up that budget.
- **Overlap with AgentPause:** A pre-execution check of irreversible actions, an intent-alignment signal, a human budget, and a feedback loop.
- **AgentPause would differ by:** Discovering risky actions automatically (InferAct lists automatic discovery as future work). Adding interruption cost, preferences, timing, and explanations.
- **Direct competitor?** Partial (strong).
- **Type:** Both (https://github.com/UKPLab/emnlp2025-inferact).

---

## 11. Risk of LM-agent actions: benchmarks, guardrails, runtime enforcement

### 11.1 Identifying the Risks of LM Agents with an LM-Emulated Sandbox (ToolEmu)
- **Year:** 2023 arXiv; ICLR 2024 (Spotlight, per the repository)
- **Authors / affiliation:** Yangjun Ruan, Honghua Dong, Andrew Wang, Silviu Pitis, Yongchao Zhou, Jimmy Ba, Yann Dubois, Chris J. Maddison, Tatsunori Hashimoto (University of Toronto / Vector / Stanford)
- **URL:** https://arxiv.org/abs/2309.15817
- **What it does:** An LM emulates tool execution, and an LM safety evaluator flags risky agent failures and quantifies their severity; 68.8% of flagged failures are judged valid in the real world.
- **Overlap with AgentPause:** Its evaluator is a ready-made severity signal and testbed, with underspecified-instruction cases where asking is the safe move.
- **AgentPause would differ by:** Being a decision layer, not an evaluator.
- **Direct competitor?** No (evaluation resource; recommended).
- **Type:** Both (https://github.com/ryoungj/ToolEmu).

### 11.2 R-Judge: Benchmarking Safety Risk Awareness for LLM Agents
- **Year:** 2024 (EMNLP 2024 Findings)
- **Authors / affiliation:** Tongxin Yuan, Zhiwei He, Lingzhong Dong, … Zhuosheng Zhang, Rui Wang, Gongshen Liu (Shanghai Jiao Tong University)
- **URL:** https://arxiv.org/abs/2401.10019
- **What it does:** 569 multi-turn agent records across 27 scenarios and 10 risk types, testing whether LLMs can judge risk. GPT-4o scores 74.42%.
- **Overlap with AgentPause:** Shows how reliable an LLM is as a risk-signal estimator.
- **AgentPause would differ by:** Not applicable.
- **Direct competitor?** No.
- **Type:** Both (https://github.com/Lordog/R-Judge).

### 11.3 Agent-SafetyBench: Evaluating the Safety of LLM Agents
- **Year:** 2024 (arXiv)
- **Authors / affiliation:** Zhexin Zhang, Shiyao Cui, Yida Lu, Jingzhuo Zhou, Junxiao Yang, Hongning Wang, Minlie Huang (Tsinghua)
- **URL:** https://arxiv.org/abs/2412.14470
- **What it does:** 2,000 tests in 349 environments; no agent scores above 60%; defense prompts are insufficient.
- **Overlap with AgentPause:** An evaluation set.
- **AgentPause would differ by:** Not applicable.
- **Direct competitor?** No.
- **Type:** Both (https://github.com/thu-coai/Agent-SafetyBench/).

### 11.4 AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents
- **Year:** 2024 arXiv; ICLR 2025
- **Authors / affiliation:** Maksym Andriushchenko, Alexandra Souly, … Zico Kolter, Matt Fredrikson, Eric Winsor, Jerome Wynne, Yarin Gal, Xander Davies (Gray Swan AI / UK AISI et al.)
- **URL:** https://arxiv.org/abs/2410.09024
- **What it does:** 110 malicious tasks (440 with augmentations) in 11 categories; agents often comply.
- **Overlap with AgentPause:** Relevant to BLOCK (malicious intent) rather than to asking.
- **AgentPause would differ by:** Not applicable.
- **Direct competitor?** No.
- **Type:** Academic + benchmark.

### 11.5 AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents
- **Year:** 2024 (arXiv; NeurIPS 2024 Datasets & Benchmarks per my knowledge)
- **Authors / affiliation:** Edoardo Debenedetti, Jie Zhang, Mislav Balunović, Luca Beurer-Kellner, Marc Fischer, Florian Tramèr (ETH Zurich / Invariant Labs)
- **URL:** https://arxiv.org/abs/2406.13352
- **What it does:** 97 tasks and 629 injection test cases.
- **Overlap with AgentPause:** Tests whether AgentPause can catch injected, off-intent actions before execution.
- **AgentPause would differ by:** Not applicable.
- **Direct competitor?** No.
- **Type:** Both (https://github.com/ethz-spylab/agentdojo).

### 11.6 ST-WebAgentBench: A Benchmark for Evaluating Safety and Trustworthiness in Web Agents
- **Year:** 2024 arXiv; ICLR 2026
- **Authors / affiliation:** Ido Levy, Ben Wiesel, Sami Marreed, Alon Oved, Avi Yaeli, Nir Mashkif, Segev Shlomov (IBM Research)
- **URL:** https://arxiv.org/abs/2410.06703
- **What it does:** 222 web tasks with policies across six dimensions, including **user consent**. Metrics are Completion-under-Policy and Risk Ratio.
- **Overlap with AgentPause:** Directly measures whether agents ask for consent when policy requires it, so it suits evaluating ASK_HUMAN.
- **AgentPause would differ by:** Not applicable.
- **Direct competitor?** No (recommended evaluation).
- **Type:** Both (https://sites.google.com/view/st-webagentbench/home).

### 11.7 WebGuard: Building a Generalizable Guardrail for Web Agents
- **Year:** 2025 (arXiv)
- **Authors / affiliation:** Boyuan Zheng, Zeyi Liao, Scott Salisbury, … Dawn Song, Huan Sun, Yu Su (Ohio State / UC Berkeley et al.)
- **URL:** https://arxiv.org/abs/2507.14293
- **What it does:** 4,939 human-annotated **state-changing** web actions labelled SAFE, LOW or HIGH risk, from 193 sites. Fine-tuned Qwen2.5-VL-7B raises accuracy from 37% to 80% and HIGH-risk recall from 20% to 76%, still short of the reliability needed for high-stakes use.
- **Overlap with AgentPause:** A **consequence-severity predictor and dataset** for proposed actions, directly usable as AgentPause's severity signal.
- **AgentPause would differ by:** Combining severity with other signals into an ask/defer decision.
- **Direct competitor?** Partial (signal component).
- **Type:** Both (https://github.com/OSU-NLP-Group/WebGuard).

### 11.8 AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents
- **Year:** 2025 arXiv; ICSE 2026 (pp. 2938–2950)
- **Authors / affiliation:** Haoyu Wang, Christopher M. Poskitt, Jun Sun (Singapore Management University)
- **URL:** https://arxiv.org/abs/2503.18666
- **What it does:** A DSL of rules with triggers, predicates and enforcement. Enforcements are `user_inspection` (pause; the user must "inspect the current state and confirm" they wish to proceed), `llm_self_examine`, `invoke_action` and `stop`. Prevents over 90% of unsafe code executions with millisecond overhead.
- **Overlap with AgentPause:** Middleware between agent and environment with ASK_HUMAN (`user_inspection`) and BLOCK (`stop`) outcomes.
- **AgentPause would differ by:** Using adaptive, cost-aware decisions instead of hand-written or LLM-generated deterministic rules. Adding timing and DEFER, user adaptation, and explanations.
- **Direct competitor?** Partial (strong at the architecture level). AgentSpec rules are a natural "fixed policy" baseline.
- **Type:** Both (https://github.com/haoyuwang99/AgentSpec).

### 11.9 ProbGuard: Proactive Runtime Monitoring for LLM Agent Safety via Probabilistic Prediction (earlier arXiv versions titled "Pro2Guard")
- **Year:** 2025 arXiv; ASE 2026 (pp. 1470–1482)
- **Authors / affiliation:** Haoyu Wang, Christopher M. Poskitt, Jiali Wei, Jun Sun (Singapore Management University)
- **URL:** https://arxiv.org/abs/2508.00500
- **What it does:** Abstracts executions into symbolic states, learns a DTMC from traces, and estimates at run time the probability of staying safe. It **intervenes when that probability falls below a user-defined threshold**, ahead of the violation (warnings up to 15.84–38.66 s early in driving). Modes are re-prompting (65.37% less unsafe behaviour, 80.4% of task completion kept) and halting (93.6% less unsafe behaviour).
- **Overlap with AgentPause:** Proactive intervention timing driven by a forecast of risk.
- **AgentPause would differ by:** Bringing in the human (ASK/CLARIFY), user cost and preferences, and counterfactual timing explanations.
- **Direct competitor?** Partial (timing via forecasting).
- **Type:** Academic (no code link on the arXiv page).

### 11.10 Progent: Securing AI Agents with Privilege Control
- **Year:** 2025 (arXiv; v3 2026)
- **Authors / affiliation:** Tianneng Shi, Jingxuan He, Zhun Wang, Hongwei Li, Linyu Wu, Wenbo Guo, Dawn Song (UC Berkeley / UCSB)
- **URL:** https://arxiv.org/abs/2504.11703
- **What it does:** Symbolic privilege policies over tool names and arguments, generated by an LLM from the task and updated during the run. An SMT solver approves policy changes that narrow privileges automatically; **expansions need explicit approval**.
- **Overlap with AgentPause:** BLOCK by policy, and asking only when privileges would expand.
- **AgentPause would differ by:** Making a risk/cost/timing decision rather than a capability check.
- **Direct competitor?** Partial (weak).
- **Type:** Academic (repository not linked on arXiv).

### 11.11 Contextual Agent Security: A Policy for Every Purpose (Conseca)
- **Year:** 2025 (HotOS 2025)
- **Authors / affiliation:** Lillian Tsai, Eugene Bagdasarian (Google; affiliation not shown on the arXiv abstract page)
- **URL:** https://arxiv.org/abs/2501.17070
- **What it does:** Argues that static rules and **user confirmations do not scale** for general agents, and generates just-in-time, context-specific security policies that humans can verify.
- **Overlap with AgentPause:** Shares the critique that always-confirm does not scale.
- **AgentPause would differ by:** Calibrating when confirmation is worth it, rather than replacing confirmation with policies.
- **Direct competitor?** Partial (weak).
- **Type:** Academic.

### 11.12 GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning
- **Year:** 2024 arXiv; ICML 2025
- **Authors / affiliation:** Zhen Xiang, Linzhi Zheng, … Dawn Song, Bo Li (UIUC / UChicago / Berkeley et al.)
- **URL:** https://arxiv.org/abs/2406.09187
- **What it does:** A guard agent turns safety requests into a plan and then into deterministic guardrail code (EICU-AC, Mind2Web-SC).
- **Overlap with AgentPause:** An external monitor on agent actions, with BLOCK.
- **AgentPause would differ by:** Including the human, cost, and timing.
- **Direct competitor?** No.
- **Type:** Both (https://guardagent.github.io/).

### 11.13 ShieldAgent: Shielding Agents via Verifiable Safety Policy Reasoning
- **Year:** 2025 (arXiv)
- **Authors / affiliation:** Zhaorun Chen, Mintong Kang, Bo Li (UChicago / UIUC)
- **URL:** https://arxiv.org/abs/2503.22738
- **What it does:** Verifiable logical reasoning over rules extracted from policy documents to check agent trajectories; ShieldAgent-Bench has about 3k instruction-trajectory pairs.
- **Overlap with AgentPause:** Same as 11.12.
- **AgentPause would differ by:** Same as 11.12.
- **Direct competitor?** No.
- **Type:** Academic.

### 11.14 No Action Without a NOD: A Heterogeneous Multi-Agent Architecture for Reliable Service Agents
- **Year:** 2026 (arXiv)
- **Authors / affiliation:** Zixu Yang, Hang Zheng, Nan Jiang, Zhiyang Tang, Situo Zhang, Xiaobao Wu, Lu Chen, Kai Yu (SJTU et al.)
- **URL:** https://arxiv.org/abs/2605.12240
- **What it does:** A Director agent provides "selective external oversight before critical actions" on τ²-Bench. The overseer is an agent, not a human.
- **Overlap with AgentPause:** Selective gating before critical actions.
- **AgentPause would differ by:** Making the human the gate and adding cost and timing.
- **Direct competitor?** Partial (weak).
- **Type:** Academic.

---

## 12. Levels of autonomy

### 12.1 Levels of Autonomy for AI Agents
- **Year:** 2025 (arXiv; Knight First Amendment Institute essay series)
- **Authors / affiliation:** K. J. Kevin Feng, David W. McDonald, Amy X. Zhang (University of Washington)
- **URL:** https://arxiv.org/abs/2506.12469
- **What it does:** Five levels defined by the user's role: operator, collaborator, consultant, approver, observer.
- **Overlap with AgentPause:** AgentPause moves dynamically between "approver" and "observer" for each action.
- **AgentPause would differ by:** Being an operational mechanism rather than a taxonomy.
- **Direct competitor?** No.
- **Type:** Academic.

### 12.2 Fully Autonomous AI Agents Should Not be Developed
- **Year:** 2025 (arXiv)
- **Authors / affiliation:** Margaret Mitchell, Avijit Ghosh, Alexandra Sasha Luccioni, Giada Pistilli (Hugging Face)
- **URL:** https://arxiv.org/abs/2502.02649
- **What it does:** Defines levels of agent autonomy and argues that risk to people grows as control is ceded.
- **Overlap with AgentPause:** A normative motivation for keeping a human in the loop.
- **AgentPause would differ by:** Not applicable.
- **Direct competitor?** No.
- **Type:** Academic (position paper).

### 12.3 Levels of AGI for Operationalizing Progress on the Path to AGI
- **Year:** 2023 arXiv; ICML 2024 (position paper)
- **Authors / affiliation:** Meredith Ringel Morris, Jascha Sohl-Dickstein, Noah Fiedel, Tris Warkentin, Allan Dafoe, Aleksandra Faust, Clement Farabet, Shane Legg (Google DeepMind)
- **URL:** https://arxiv.org/abs/2311.02462
- **What it does:** Levels of performance and generality, and how they interact with autonomy and risk in deployment.
- **Overlap with AgentPause:** Background on autonomy levels.
- **AgentPause would differ by:** Not applicable.
- **Direct competitor?** No.
- **Type:** Academic.

---

## 13. Analysis of the three special-attention questions

### (a) Asking modelled as expected utility / value of information minus interruption cost
Prior art is **substantial**, so the expected-value-of-asking framing on its own is not novel:
- **Horvitz 1999**: thresholds p* for action, dialog and inaction, from four outcome utilities; the utilities shift with user attention.
- **Scerri et al. 2002**: an MDP over transfer-of-control strategies with explicit costs of delay and miscoordination.
- **Rao & Daumé 2018**: EVPI for ranking clarification questions.
- **Dong et al. ACL 2026 (VoI)**: NetVoI = VoI − c; stakes through utility; cost is user effort; compared against never-ask, fixed rounds and confidence thresholds. **This is the closest match.**
- **SAGE-Agent (ACL Findings 2026)**: EVPI − λ·(aspect redundancy) over tool arguments.
- **Self-Regulation (Min et al. 2025)**: help iff r < Δp/ΔM; r tuned to a budget.
- **ReHAC**: R = T − λ·#interventions.
- **Ask4Help**: r_fail, r_init_ask, r_step_ask, with the **reward configuration embedded as a user preference**.
- **DeCCaF**: cost-sensitive deferral under reviewer workload.
- **Oversight Has a Capacity**: reviewer fatigue makes safety an inverted U in escalation rate.
- **Off-switch game**: the value of deferring depends on uncertainty and on how rational the human is.

**Gap.** None of these makes the **cost of interruption state-dependent and learned from the user's own decision history** (cognitive load, task phase, past approvals) **while also** putting **reversibility/recoverability** explicitly into the loss of acting wrongly.

### (b) Timing of the ask as the decision variable
Prior art exists but is **thin and fragmented**:
- **Scerri 2002**: how long to wait for a human and when to delay a commitment.
- **Horvitz 1999**: deferring an offer until the user is ready, with a learned per-user timing model.
- **SLTD (Joshi et al.)**: defer now versus wait a step, in sequential decision-making.
- **Ask Early/Ask Late/Ask Right (2026)**: empirical value-of-clarification curves over the trajectory; no policy.
- **Ask Now, Use Later (2026)**: ask while the user is present, use later.
- **ProbGuard**: early intervention from forecast risk.
- **PAINT** and **Leave No Trace**: act before or at irreversibility.
- **Self-Regulation**: where in the trajectory to spend a limited budget of interventions.
- **LazyDAgger**: fewer, longer interventions to cut context switching.

**Gap.** No LLM-agent work found that **chooses among ask-now / defer-to-breakpoint / batch-later as explicit actions with counterfactual "why not earlier / why not later" explanations**. The empirical paper (6.1) offers a ready evaluation design and a warning: deferring **goal and constraint** questions hurts. AgentPause's DEFER should therefore be limited to deferrable kinds of interruption, for example approval of a later irreversible commit, or questions about inputs needed only later.

### (c) Combining reversibility, uncertainty, user preference and interruption cost
**No single work found combines all four.** Partial combinations:
- **Magentic-UI**: reversibility heuristic + LLM judge; no user model or cost.
- **VoI (Dong et al.)**: stakes + ambiguity + user effort; no reversibility or timing.
- **Ask4Help**: implicit uncertainty + user-preference cost; no reversibility.
- **PAINT**, **Plaut et al.**: reversibility + asking; no preferences.
- **CDWM**: reversibility + irreversible cost + confidence → abstain; no human.
- **InferAct**: critical (irreversible) actions + intent uncertainty + review budget; no user preference.
- **PlowPilot**: user style + context → ask; no explicit risk or reversibility.
- **Oversight Has a Capacity**: risk + reviewer fatigue; no reversibility or preference.
- **ThriftyDAgger**: risk + novelty + budget; robotics only.

This four-way combination, plus timing and explanations, is AgentPause's most defensible novelty claim.

---

## 14. Could not verify / gaps in this search
- **Web-search budget ran out** (shared across agents) before these could be verified, so they are **not** in the catalogue:
  - Rosenthal & Veloso's CoBot work on asking humans for help, accounting for human availability and interruption (the CoBots "symbiotic autonomy" line, Veloso et al. IJCAI 2015, was seen in results but not fetched).
  - Banerjee/Chernova-style robot work on **human interruptibility**.
  - "FALCON" fatigue-aware learning-to-defer (cited by Turan 2026; not opened).
  - Follow-ups to the partially observable off-switch game.
  - "GA-Rollback" / "WebRollback" (seen only as citations in AgentRewind, arXiv 2608.14380, which was not opened).
- **Venues taken from my knowledge, not the fetched page:** CIRL (NeurIPS 2016), Off-Switch (IJCAI 2017), SafeDAgger (AAAI 2017), Leave No Trace (ICLR 2018), No Turning Back (NeurIPS 2021), AgentDojo (NeurIPS 2024 D&B), MediQ (NeurIPS 2024), STaR-GATE (COLM 2024). Treat them as likely but not page-verified.
- **Mechanism details from my reading rather than the fetched abstract:** ThriftyDAgger (Q-function risk, ensemble novelty, budget-calibrated thresholds), LazyDAgger (asymmetric switching), SafeDAgger (safety classifier), Fleet-DAgger (priority function). The abstracts confirm the overall claims.
- **Not located:** code for CowCorpus data, Ask-Early/Ask-Late (promised), VoI (announced), GateArena (stated as released), ProbGuard, Progent, ShieldAgent.
- ShieldAgent's venue is not shown on arXiv. Zhang & Choi (2311.09469) and Active Task Disambiguation also show no venue on arXiv.
- The τ-bench confirmation-before-consequential-actions policy comes from my knowledge of the benchmark's domain policies; I did not re-read it here.

---

## Closest competitors and key takeaways

**Closest competitors, ranked:**
1. **Value of Information: A Framework for Human–Agent Communication** (Dong et al., ACL 2026). The same decision-theoretic core: ask iff VoI > user cost, with stakes in utility and the same family of baselines. AgentPause must implement it as a baseline and differentiate on reversibility, learned state-dependent cost, timing/DEFER, BLOCK, multi-step action gating, and explanations.
2. **CowCorpus / PlowPilot** (Huq et al., CMU 2026). A per-proposed-action `<ask_user>`/`<agent_continue>` predictor conditioned on user interaction style and history, deployed live, beating confirm-every-step. It is the closest LLM-agent system; it lacks explicit risk and reversibility, DEFER and explanations.
3. **Magentic-UI ActionGuard** (Microsoft 2025). An open-source reversibility-labelled approval gate with an LLM judge. It is the obvious system baseline; it is static and developer-labelled, with no user model or timing.
4. **Ask4Help** (NeurIPS 2022). A learned asking policy conditioned on a **user-preference embedding of asking and failure costs**, on top of a frozen agent. It is prior art for "user-customized policy as middleware".
5. **Self-Regulation and Requesting Interventions** (CMU 2025) and **ReHAC** (2024). Learned, budgeted, per-step intervention timing with an explicit cost-benefit rule.
6. **SAGE-Agent** (ACL Findings 2026). EVPI minus cost for clarification over tool arguments; prior art for AgentPause's CLARIFY branch.
7. **Ask Early, Ask Late, Ask Right** (2026). Evidence on timing and an evaluation protocol; it shows timing matters and that late asks are worse than never asking.
8. **AgentSpec `user_inspection` / ProbGuard** (SMU; ICSE/ASE 2026). Runtime middleware with ASK and STOP; ProbGuard adds proactive, forecast-driven timing.
9. **InferAct** (EMNLP 2025). Checks before irreversible "critical actions", alerts a human under a review budget.
10. **Foundations to cite:** **Horvitz 1999** (expected-utility thresholds for act, dialog and no-act, deferred timing, per-user timing model) and **Scerri/Pynadath/Tambe 2002** (transfer-of-control strategies with timing and deadlines). Together they pre-empt any novelty claim for "expected-value asking" or "defer" in isolation.
11. Robotics and safety analogues: **KnowNo / Introspective Planning** (conformal asking), **ThriftyDAgger** (risk + novelty gating under budget), **PAINT / Plaut et al.** (asking under irreversibility), **Oversight Has a Capacity** (fatigue: more escalation can mean less safety).

**Key takeaways for AgentPause:**
- **Novelty has to be the combination, not the parts.** Expected-value asking, uncertainty-gated asking, reversibility-gated approval, learned intervention prediction, and preference-conditioned asking each exist. No work found unifies (i) reversibility/recoverability and severity, (ii) calibrated uncertainty and intent ambiguity, (iii) an interruption cost that depends on state and is learned from the user's decision history, and (iv) **timing as an explicit action (DEFER to breakpoint) with counterfactual why-not-earlier/later explanations**, in one middleware with a five-policy comparison.
- **Timing claims must respect the empirical evidence.** Gulati et al. show goal and constraint clarifications must come very early and that late asks are worse than none. AgentPause's DEFER should be restricted to deferrable interruptions, such as approving an irreversible commit at the moment it happens, or batching low-stakes confirmations at natural breakpoints. Its "why not later" explanation can cite information-type decay.
- **Arguments for the middleware position:** GateArena shows prompt-based "ask first" is unreliable, so confirmation must be enforced outside the model. AgentAbstain shows agents take irreversible actions before noticing they should stop. Oversight Has a Capacity and Magentic-UI's user study show that over-asking has real safety and usability costs.
- **Recommended baselines:**
  - always/never ask
  - fixed risk threshold (AgentSpec-style rules or a Magentic-UI ActionGuard)
  - KnowNo-style conformal threshold
  - ThriftyDAgger-style risk + novelty gating with a budget
  - VoI (Dong et al.)
  - a PlowPilot-style learned intervention predictor
  - Ask4Help-style preference-conditioned policy
- **Recommended evaluation resources:**
  - τ-bench / τ²-bench (user simulation)
  - ST-WebAgentBench (user-consent policies)
  - ToolEmu (severity evaluator)
  - WebGuard (action-risk labels)
  - AgentAbstain
  - When2Call
  - ClarifyBench
  - the forced-injection timing protocol and LHAW-derived tasks from Ask Early/Ask Late
  - CowCorpus, if it is released
  - GateArena (enforcement)
- **Signal providers to reuse rather than reinvent:** intent-sim entropy (Zhang & Choi), SAUP step-level uncertainty, WebGuard or ToolEmu severity, CDWM or GoEX-style reversibility and undo availability, and PlowPilot-style P(user would intervene) as a prior on the cost of not asking.

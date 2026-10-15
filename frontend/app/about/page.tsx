import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Container, PageHeader } from "@/components/layout/page";
import { Callout } from "@/components/ui/feedback";

export const metadata: Metadata = { title: "Research, methodology & limitations" };

const PRIOR = [
  ["Horvitz (1999), Principles of Mixed-Initiative User Interfaces, CHI", "Expected-utility thresholds for acting vs asking vs doing nothing; deferring to less distracting moments; user-set thresholds. The conceptual ancestor of AgentPause's core."],
  ["Iqbal & Bailey (2005–2010), task breakpoints and OASIS", "Interrupting at task boundaries reduces cost; holding notifications until breakpoints. The basis for the breakpoint signal and DEFER."],
  ["Scerri, Pynadath & Tambe (2002), Adjustable autonomy, JAIR", "Transfer-of-control strategies with timing and deadlines."],
  ["Dong et al. (2026), Value of Information for human–agent communication, ACL", "Ask when value of information exceeds user cost, for LLM agents; compared against never/fixed/threshold baselines."],
  ["Zhou et al. (2026), When Should Users Check?, CHI", "Decision-theoretic placement of confirmation checkpoints in multi-step agent tasks (time cost only; irreversibility left to future work)."],
  ["Huq et al. (2026), Modeling Distinct Human Interaction in Web Agents", "Learned per-step ask/continue prediction from user interaction history (PlowPilot)."],
  ["Gulati et al. (2026), Ask Early, Ask Late, Ask Right", "Value of clarification by trajectory position: goal questions lose value early; late questions can be worse than none."],
  ["Chen et al. (2026), Comparing Human Oversight Strategies for Computer-Use Agents", "Users blocked 21% of problematic actions; 56% of failures involved a timing mismatch; a call for adaptive oversight."],
  ["Krarup et al. (2021), Contrastive Explanations of Plans, JAIR", "Temporal contrastive questions (\"why at time T rather than earlier/later?\") for planners: the question form AgentPause applies to human-intervention decisions."],
  ["Hamid, Li & Liang (2026), When2Talk", "A proactive in-car agent chooses between speaking now, later, or not at all; a VR study found less perceived interruption. The closest recent work to DEFER, in a different domain."],
  ["Magentic-UI (2025), OpenHands (2024), Claude Code auto mode (2026)", "Deployed approval gates: irreversibility labels + LLM judge; swappable always/never/risky policies; transcript classifier."],
];

export default function AboutPage() {
  return (
    <Container className="pt-8">
      <PageHeader
        eyebrow="Research"
        title="Methodology, model, and limitations"
        description="AgentPause is positioned as research infrastructure and an open-source toolkit for studying adaptive human intervention timing in AI-agent systems. It does not claim to be the first adaptive approach; see the prior-art review in research/prior_art.md."
      />
      <div className="mt-8 grid grid-cols-1 gap-10 lg:grid-cols-[14rem_minmax(0,1fr)]">
        <nav aria-label="On this page" className="hidden lg:block">
          <ul className="sticky top-20 flex flex-col gap-2 text-sm text-ink-2">
            {[
              ["questions", "Research questions"],
              ["model", "The intervention model"],
              ["explanations", "Explanations"],
              ["evaluation", "Evaluation"],
              ["prior", "Prior work & positioning"],
              ["limitations", "Limitations"],
              ["ethics", "Privacy & safety"],
              ["cite", "How to cite"],
            ].map(([id, label]) => (
              <li key={id}>
                <a href={`#${id}`} className="hover:text-ink">
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <article className="flex max-w-3xl flex-col gap-12 leading-relaxed text-ink">
          <Section id="questions" title="Research questions">
            <ol className="list-decimal space-y-2 pl-5 text-ink-2">
              <li>
                <strong className="text-ink">RQ1 (timing).</strong> Compared with fixed strategies and with a myopic value-of-asking policy, does deciding <em>when</em> to
                involve the human (now, at a later breakpoint, batched, or never) reduce unnecessary interruptions without increasing missed interventions?
              </li>
              <li>
                <strong className="text-ink">RQ2 (signals).</strong> Which contextual signals carry the value of the decision? (Simulation ablation; human data needed for a
                substantive answer.)
              </li>
              <li>
                <strong className="text-ink">RQ3 (human outcomes).</strong> Effects on perceived control, trust, workload, oversight effectiveness, and time.
              </li>
              <li>
                <strong className="text-ink">RQ4 (understanding).</strong> Can people explain why the agent interrupted them, and why at that moment?
              </li>
              <li>
                <strong className="text-ink">RQ5 (acceptance).</strong> Do timing explanations increase appropriate acceptance of autonomy without increasing over-reliance?
              </li>
              <li>
                <strong className="text-ink">RQ6 (customization).</strong> Do user-authored preferences reduce interruptions, and at what cost?
              </li>
            </ol>
            <p className="text-sm text-ink-2">Hypotheses, variables, and the study design are in research/research_questions.md.</p>
          </Section>

          <Section id="model" title="The intervention model">
            <p className="text-ink-2">
              For a question <em>q</em> that could be asked at step <em>t</em>, AgentPause estimates a net value (all terms on a scale where 1 is the worst outcome the
              deployment cares about):
            </p>
            <pre className="overflow-x-auto rounded-xl border border-line bg-surface p-4 font-mono text-sm">
              V(q, t) = p_err · C_err · e(t) − C_int(t) − RW(q, now→t)
            </pre>
            <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
              <Term name="p_err">Probability that proceeding is wrong: agent error and intent mismatch, assumed independent.</Term>
              <Term name="C_err">Harm if wrong: severity · [(1 − recoverability) + recoverability · undo cost].</Term>
              <Term name="e(t)">Probability you catch the problem when asked; falls with recent interruptions (habituation).</Term>
              <Term name="C_int(t)">Cost of interrupting: grows with your load and mid-task; shrinks at natural breakpoints and when batched; scaled by your profile.</Term>
              <Term name="RW">Expected rework when the agent keeps working on a possibly wrong assumption until t.</Term>
              <Term name="Deadline">A question must be asked before the first irreversible step that depends on it (its commitment point).</Term>
            </dl>
            <p className="text-ink-2">
              Each step considers an approval question for the action itself (deadline: now) and one clarification per open assumption (candidate moments: now,
              later breakpoints, steps that will probably need a confirmation anyway, and the deadline). If any question&apos;s best moment is now and its value is
              positive, AgentPause interrupts and adds other questions whose marginal value is positive (batching). If a question is worth asking but later, the
              decision is <strong>DEFER</strong>. Goal and constraint questions are not deferred, following evidence that they lose value early (Gulati et al. 2026).
              Catastrophic actions (high severity, irreversible, probably wrong) are blocked.
            </p>
            <Callout title="Assumptions, not measurements">
              Default parameters (for example, an interruption costs 0.02 harm units) are documented priors chosen on development seeds. They are not calibrated
              estimates. Every signal shown in the app carries its provenance: agent-reported, estimated, inferred, simulated, user-provided, or default.
            </Callout>
          </Section>

          <Section id="explanations" title="Explanations">
            <p className="text-ink-2">
              Every decision returns reason codes, a template-based explanation (no language model, so every clause maps to a code the policy emitted), factor
              attributions (score change when a signal is set to a low-risk reference), minimal feature counterfactuals (verified by re-running the policy), a
              stability estimate, and <strong>timing counterfactuals</strong>. &ldquo;Why not earlier?&rdquo; is read from what the policy actually computed at earlier
              steps; &ldquo;why not later?&rdquo; comes from the same evaluation at planned future steps. Explanations work for every policy, because the explainer treats
              the policy as a black box.
            </p>
            <p className="text-ink-2">
              The explanation literature warns that explanations can raise acceptance regardless of correctness and that content-free reasons can raise trust. The
              study mode therefore includes a placebic-reason control and measures appropriate reliance, not only satisfaction.
            </p>
          </Section>

          <Section id="evaluation" title="Evaluation">
            <ul className="list-disc space-y-2 pl-5 text-ink-2">
              <li>
                <strong className="text-ink">Simulation.</strong> Six scripted scenarios (travel, email, shopping, files, calendar, research) with injected mistakes and
                wrong intent assumptions. A parametric simulated user habituates to prompts. Common random numbers give paired comparisons. Metrics: unnecessary
                and missed interventions, harm, recovery, rework, time. Results are reported as harm-vs-interruption frontiers, ablations, and sensitivity to
                simulator assumptions.
              </li>
              <li>
                <strong className="text-ink">Human study (protocol ready, not yet run).</strong> Within-subjects policies (balanced Latin square), between-subjects
                explanation types, embedded problematic actions, NASA-TLX and pilot items, comprehension checks.
              </li>
            </ul>
            <p className="text-ink-2">
              <strong className="text-ink">What the simulation shows so far.</strong> On held-out seeds, the adaptive policy needed about half the
              interruptions of always-confirm with no detectable difference in harm, and fewer interruptions than the myopic value-of-asking policy
              it extends. Simple rules stayed competitive: confirming every irreversible action matched its harm with slightly fewer interruptions
              but more rework. The ranking changed when agent confidence was uninformative or users habituated quickly. Details are in the paper
              draft (research/paper_draft.md).
            </p>
            <Callout tone="simulated">Not yet evaluated with human participants. Simulated results are labelled wherever they appear.</Callout>
          </Section>

          <Section id="prior" title="Prior work and positioning">
            <p className="text-ink-2">
              The idea that an agent should weigh the value of asking against the cost of interrupting is not new. AgentPause builds on, and compares against, the
              following (full review with 250+ items: research/prior_art.md):
            </p>
            <ul className="flex flex-col gap-3">
              {PRIOR.map(([title, text]) => (
                <li key={title} className="rounded-xl border border-line bg-surface p-3">
                  <p className="text-sm font-medium text-ink">{title}</p>
                  <p className="mt-0.5 text-sm text-ink-2">{text}</p>
                </li>
              ))}
            </ul>
            <p className="text-ink-2">
              Within the literature and systems reviewed, we found no system that combines (a) deferring and batching questions within an executing agent
              trajectory, bounded by the first irreversible dependent step, (b) user-facing counterfactual timing explanations for intervention decisions, and (c)
              an open, deterministic testbed for comparing intervention-timing policies. The novelty claim is about this combination. See
              research/novelty_audit.md.
            </p>
          </Section>

          <Section id="limitations" title="Limitations">
            <ul className="list-disc space-y-2 pl-5 text-ink-2">
              <li>Parameters are priors; the model has not been calibrated on human data.</li>
              <li>Ground truth is scripted by the scenario authors. People disagree about when intervention is needed, so &ldquo;necessary&rdquo; is a modelling choice.</li>
              <li>Simulated users are not people. The adaptive policy and the simulated user share functional forms; sensitivity analyses vary this.</li>
              <li>Agent confidence is simulated. Real LLM confidence is often miscalibrated, and expected-value policies depend on it.</li>
              <li>In the simulation, a simple rule (always confirm irreversible actions) is a strong baseline.</li>
              <li>Scenarios are short and linear; real agents branch, retry, and run in parallel.</li>
            </ul>
          </Section>

          <Section id="ethics" title="Privacy and safety">
            <ul className="list-disc space-y-2 pl-5 text-ink-2">
              <li>All actions in the demo and study are simulated and labelled as such. Nothing sends email, spends money, or deletes files.</li>
              <li>AgentPause only needs action metadata. It never needs message bodies, credentials, or payment details, and the API does not store them.</li>
              <li>Participants are identified by random codes. No names, emails, or IP addresses are stored.</li>
              <li>AgentPause is not a security boundary: a CONTINUE decision is never proof that an action is safe.</li>
            </ul>
          </Section>

          <Section id="cite" title="How to cite">
            <pre className="overflow-x-auto rounded-xl border border-line bg-surface p-4 font-mono text-xs">{`@software{agentpause2026,
  title  = {AgentPause: Research Infrastructure for Adaptive
            Human Intervention Timing in AI Agents},
  author = {Kaviani, Morvarid and {AgentPause contributors}},
  year   = {2026},
  version = {0.1.0},
  note   = {Simulated results; not yet evaluated with human participants}
}`}</pre>
            <p className="text-sm text-ink-2">See CITATION.cff in the repository.</p>
          </Section>
        </article>
      </div>
    </Container>
  );
}

function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="flex scroll-mt-20 flex-col gap-4">
      <h2 id={`${id}-title`} className="text-xl font-semibold text-ink">
        {title}
      </h2>
      {children}
    </section>
  );
}

function Term({ name, children }: { name: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-3">
      <dt className="font-mono text-sm font-semibold text-ink">{name}</dt>
      <dd className="mt-0.5 text-ink-2">{children}</dd>
    </div>
  );
}

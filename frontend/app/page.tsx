import { ArrowRight, BookOpen, Clock, FlaskConical, Hand, MessageCircleQuestion, OctagonX, Route, Scale, Workflow } from "lucide-react";
import type { Metadata } from "next";

import { Container } from "@/components/layout/page";
import { Callout } from "@/components/ui/feedback";
import { ButtonLink, Card } from "@/components/ui/primitives";
import { API_DOCS_URL, REPO_URL } from "@/lib/site";

export const metadata: Metadata = { title: "AgentPause: when should an AI agent pause and ask?" };

const DECISIONS = [
  { name: "Continue", icon: ArrowRight, color: "var(--d-continue)", tint: "tint-continue", text: "Low stakes, easily undone, or asking would cost you more than it saves." },
  { name: "Clarify", icon: MessageCircleQuestion, color: "var(--d-clarify)", tint: "tint-clarify", text: "The agent had to guess what you meant, and something important depends on it." },
  { name: "Ask human", icon: Hand, color: "var(--d-ask)", tint: "tint-ask", text: "Approve, edit, or reject one specific action before it runs." },
  { name: "Defer", icon: Clock, color: "var(--d-defer)", tint: "tint-defer", text: "Keep doing reversible work; ask at a natural pause, batched, before anything irreversible." },
  { name: "Block", icon: OctagonX, color: "var(--d-block)", tint: "tint-block", text: "The step needs you, or it is high-stakes, irreversible, and probably wrong." },
];

const SDK = `from agentpause import AgentPause

pause = AgentPause(policy="adaptive")

decision = pause.evaluate(
    action="send_email",
    consequence="external_communication",
    reversible=False,
    intent_confidence=0.72,
    agent_confidence=0.86,
)

if decision.should_ask:
    print(decision.explanation)
    print(decision.timing.why_not_later)`;

export default function Home() {
  const repo = REPO_URL;
  return (
    <>
      <section className="border-b border-line">
        <Container className="grid grid-cols-1 gap-10 py-14 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:py-20">
          <div>
            <p className="text-sm font-semibold text-accent">Open-source HCI research infrastructure</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">When should an AI agent pause and ask you?</h1>
            <p className="mt-5 max-w-xl text-lg text-ink-2">
              AgentPause is a toolkit for studying <em>adaptive human intervention timing</em>. It sits between an agent and the world and
              decides, for every proposed action, whether to continue, clarify, ask you, defer the question to a better moment, or stop.
              Every decision comes with a faithful explanation, including <em>why now, and not earlier or later</em>.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <ButtonLink href="/demo" size="lg" icon={<ArrowRight className="size-4" aria-hidden />}>
                Try the interactive demo
              </ButtonLink>
              <ButtonLink href="/about" size="lg" variant="secondary" icon={<BookOpen className="size-4" aria-hidden />}>
                How it works
              </ButtonLink>
            </div>
            <p className="mt-6 text-sm text-ink-3">
              All agent actions are simulated. Results shown in this app are simulated unless labelled otherwise; the human study
              has not been run yet.
            </p>
          </div>
          <ConceptDiagram />
        </Container>
      </section>

      <Container className="py-14">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-3">
          <div>
            <h2 className="text-xl font-semibold text-ink">The problem</h2>
            <p className="mt-3 text-ink-2">
              Agents that ask about everything train people to click &ldquo;approve&rdquo;. In one production coding agent, users approved
              93% of permission prompts. Agents that never ask let mistakes through. Fixed risk thresholds ignore <em>when</em> a question
              is cheapest and most useful: in one study of computer-use agents, 56% of oversight failures involved a timing mismatch.
            </p>
          </div>
          <div>
            <h2 className="text-xl font-semibold text-ink">The research question</h2>
            <p className="mt-3 text-ink-2">
              Can choosing <em>when</em> to involve the human (now, at a later natural pause, batched, or never) reduce unnecessary
              interruptions without letting more errors through, and can people understand why an agent interrupted them at that moment?
            </p>
          </div>
          <div>
            <h2 className="text-xl font-semibold text-ink">What is new, and what is not</h2>
            <p className="mt-3 text-ink-2">
              Weighing the value of asking against its cost goes back to Horvitz (1999) and has recent LLM-agent versions (Dong et al. 2026;
              Zhou et al. 2026), and holding interruptions for better moments is established in HCI. AgentPause contributes a specific{" "}
              <em>timing</em> mechanism for agent questions (defer and batch up to the first irreversible step), counterfactual timing
              explanations, and an open testbed to compare policies. In simulation, simple rules remain competitive.
            </p>
          </div>
        </div>
      </Container>

      <section className="border-y border-line bg-surface">
        <Container className="py-14">
          <h2 className="text-xl font-semibold text-ink">Five decisions, not just &ldquo;approve?&rdquo;</h2>
          <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {DECISIONS.map((d) => (
              <div key={d.name} className={`rounded-xl p-4 ${d.tint}`}>
                <d.icon className="size-5" style={{ color: d.color }} aria-hidden />
                <h3 className="mt-2 font-semibold text-ink">{d.name}</h3>
                <p className="mt-1 text-sm text-ink-2">{d.text}</p>
              </div>
            ))}
          </div>
        </Container>
      </section>

      <Container className="grid grid-cols-1 gap-8 py-14 lg:grid-cols-2">
        <div>
          <h2 className="text-xl font-semibold text-ink">Use it from your agent</h2>
          <p className="mt-2 text-ink-2">
            A zero-dependency Python SDK, a REST API with OpenAPI docs, and a typed TypeScript client. Send action <em>metadata</em>, not
            content. AgentPause never needs your email body or credentials.
          </p>
          <pre className="mt-4 overflow-x-auto rounded-xl border border-line bg-surface p-4 text-sm leading-relaxed text-ink">
            <code>{SDK}</code>
          </pre>
          <div className="mt-4 flex flex-wrap gap-3">
            <a href={API_DOCS_URL} className="text-sm font-medium text-accent-strong hover:underline">
              REST API docs →
            </a>
            {repo ? (
              <a href={repo} className="text-sm font-medium text-accent-strong hover:underline" rel="noreferrer">
                Source code →
              </a>
            ) : (
              <span className="text-sm text-ink-3">Source code: see the repository README</span>
            )}
          </div>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Feature icon={Workflow} title="Inspectable model">
            Every term (error probability, harm, catch probability, interruption cost, rework) is visible, with each signal&apos;s provenance:
            measured, estimated, simulated or defaulted.
          </Feature>
          <Feature icon={Route} title="Timing-aware">
            Questions have deadlines (the first irreversible step that depends on them) and are batched at natural pauses.
          </Feature>
          <Feature icon={Scale} title="Comparable policies">
            Full autonomy, always confirm, fixed threshold, rules, confidence threshold, myopic value-of-asking, adaptive, user-customized.
          </Feature>
          <Feature icon={FlaskConical} title="Reproducible">
            A deterministic simulator with scripted ground truth, common random numbers, held-out seeds, and result hashes.
          </Feature>
        </div>
      </Container>

      <Container>
        <Callout tone="warning" title="Limitations, up front">
          The model&apos;s parameters are documented priors, not calibrated estimates. The simulator&apos;s ground truth encodes the scenario
          authors&apos; judgement, and simulated users are not people. No human-participant study has been run yet; the study mode exists so
          that one can be.
        </Callout>
      </Container>
    </>
  );
}

function Feature({ icon: Icon, title, children }: { icon: typeof Workflow; title: string; children: React.ReactNode }) {
  return (
    <Card className="p-4">
      <Icon className="size-5 text-accent" aria-hidden />
      <h3 className="mt-2 font-semibold text-ink">{title}</h3>
      <p className="mt-1 text-sm text-ink-2">{children}</p>
    </Card>
  );
}

function ConceptDiagram() {
  return (
    <figure className="flex flex-col justify-center" aria-labelledby="concept-caption">
      <div className="rounded-2xl border border-line bg-surface p-5 shadow-card">
        <div className="flex flex-col items-stretch gap-2 text-sm">
          <Node label="You" sub="give an instruction; know your real intent" />
          <Arrow />
          <Node label="AI agent" sub="proposes the next action + metadata" />
          <Arrow />
          <div className="rounded-xl border-2 border-accent bg-accent-soft p-3">
            <p className="text-center font-semibold text-ink">AgentPause</p>
            <p className="text-center text-xs text-ink-2">uncertainty · intent ambiguity · severity · reversibility · timing · load · your preferences</p>
            <div className="mt-3 grid grid-cols-5 gap-1">
              {DECISIONS.map((d) => (
                <div key={d.name} className={`flex flex-col items-center gap-1 rounded-lg px-1 py-2 ${d.tint}`}>
                  <d.icon className="size-4" style={{ color: d.color }} aria-hidden />
                  <span className="text-center text-[11px] leading-tight font-medium text-ink">{d.name}</span>
                </div>
              ))}
            </div>
          </div>
          <Arrow />
          <Node label="Environment" sub="email, payments, files, calendars (simulated here)" />
        </div>
      </div>
      <figcaption id="concept-caption" className="mt-3 text-center text-sm text-ink-3">
        AgentPause sits between the agent and the environment and decides how, and when, to involve you.
      </figcaption>
    </figure>
  );
}

function Node({ label, sub }: { label: string; sub: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface-2 px-3 py-2 text-center">
      <p className="font-semibold text-ink">{label}</p>
      <p className="text-xs text-ink-2">{sub}</p>
    </div>
  );
}

function Arrow() {
  return (
    <div aria-hidden className="flex justify-center text-ink-3">
      ↓
    </div>
  );
}

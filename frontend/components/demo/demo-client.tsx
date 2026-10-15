"use client";

import clsx from "clsx";
import { ChevronRight, Pause, Play, RotateCcw, Shuffle, StepForward, Undo2, X } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { DecisionExplanation, ScheduledQuestions } from "@/components/decision/explanation";
import { Container, PageHeader } from "@/components/layout/page";
import { Field, Segmented, Select, TextInput, Toggle } from "@/components/ui/form";
import { EmptyState, ErrorState } from "@/components/ui/feedback";
import { Badge, Button, ButtonLink, Card, CardBody, CardHeader, Skeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { policyLabel } from "@/lib/format";
import { describePreferences, usePreferences } from "@/lib/preferences";
import { load, save } from "@/lib/storage";
import type { ScenarioSummary, TimelineItem } from "@/lib/types";
import { useSessionRunner } from "@/lib/use-session";
import { useViewMode, type ViewMode } from "@/lib/view-mode";

import { InterventionCardView } from "./intervention-card";
import { OutcomeSummary } from "./outcome";
import { BriefPanel, ScenarioIcon, ScenarioPicker, StepRail } from "./scenario";
import { Timeline } from "./timeline";

/** The three ways to check in that most visitors need. All nine policies stay under "Advanced options". */
const APPROACHES = [
  { policy: "adaptive", title: "Only when it matters", note: "AgentPause", description: "Asks at the right moment and saves small questions for later." },
  { policy: "always_confirm", title: "Ask about everything", note: null, description: "Checks every step with you. Safe, but many interruptions." },
  { policy: "full_autonomy", title: "Never ask", note: null, description: "Works alone. Fast, but mistakes can slip through." },
  { policy: "user_customized", title: "My preferences", note: null, description: "Uses the style and rules you chose on the My preferences page." },
] as const;
const ALL_POLICIES = ["adaptive", "always_confirm", "full_autonomy", "fixed_threshold", "user_customized", "myopic_voi", "rule_based", "confidence_threshold", "learned"];
const SPEEDS = [
  { value: "1600", label: "Slow" },
  { value: "900", label: "Normal" },
  { value: "350", label: "Fast" },
];
const VIEWS: { value: ViewMode; label: string }[] = [
  { value: "simple", label: "Simple" },
  { value: "detailed", label: "Detailed" },
];
const TIP_KEY = "agentpause.demo-tip";

function approachLabel(policy: string): string {
  return APPROACHES.find((a) => a.policy === policy)?.title ?? policyLabel(policy);
}

export function DemoClient() {
  const params = useSearchParams();
  const [scenarios, setScenarios] = useState<ScenarioSummary[] | null>(null);
  const [loadError, setLoadError] = useState<unknown>(null);
  const [scenarioId, setScenarioId] = useState<string>(params.get("scenario") ?? "travel");
  const [policy, setPolicy] = useState<string>(params.get("policy") ?? "adaptive");
  const [seed, setSeed] = useState<string>(params.get("seed") ?? "7");
  const [preferences] = usePreferences();
  const [view, setView] = useViewMode();
  const [tipHidden, setTipHidden] = useState<boolean>(() => load<{ hidden: boolean }>(TIP_KEY, { hidden: false }).hidden);
  const [selectedSeq, setSelectedSeq] = useState<number | null>(null);
  const runner = useSessionRunner({ autoplay: true, delayMs: 900 });
  const { session } = runner;

  const loadScenarios = () =>
    api
      .scenarios()
      .then((list) => {
        setScenarios(list);
        setLoadError(null);
      })
      .catch(setLoadError);
  useEffect(() => {
    void loadScenarios();
  }, []);

  const start = (sameSeed = false) => {
    const chosenSeed = sameSeed && session ? session.seed : Number.parseInt(seed, 10) || 0;
    setSelectedSeq(null);
    runner.setPlaying(true);
    void runner.run(() =>
      api.createSession({
        mode: "demo",
        scenario_id: scenarioId,
        policy,
        preferences: policy === "user_customized" ? preferences : null,
        seed: chosenSeed,
      }),
    );
  };

  /** Back to the start screen with the same task and the same hidden mistakes, to try another approach. */
  const tryAnother = () => {
    if (session) setSeed(String(session.seed));
    runner.setSession(null);
  };

  const hideTip = () => {
    setTipHidden(true);
    save(TIP_KEY, { hidden: true });
  };

  const timeline = useMemo(() => session?.timeline ?? [], [session]);
  const selected: TimelineItem | undefined = useMemo(
    () => timeline.find((t) => t.seq === selectedSeq) ?? [...timeline].reverse().find((t) => t.decision_detail),
    [timeline, selectedSeq],
  );
  const detail = session?.pending?.decision ?? selected?.decision_detail ?? null;

  if (!session) {
    return (
      <Container className="pt-8">
        <PageHeader
          eyebrow="Demo"
          title="Watch an AI assistant work, and see when it stops to ask you"
          description="Pick a task. A simulated assistant works through it step by step and pauses when it needs you. Nothing real happens: no emails are sent and no money is spent."
        />
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <section aria-labelledby="pick-task">
            <h2 id="pick-task" className="mb-3 text-base font-semibold text-ink">
              1. Pick a task
            </h2>
            {loadError ? <ErrorState error={loadError} onRetry={loadScenarios} title="Could not load the tasks" /> : null}
            {!scenarios && !loadError ? (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {Array.from({ length: 6 }, (_, i) => (
                  <Skeleton key={i} className="h-40" />
                ))}
              </div>
            ) : null}
            {scenarios ? <ScenarioPicker scenarios={scenarios} value={scenarioId} onChange={setScenarioId} /> : null}
          </section>

          <Card className="h-fit">
            <CardHeader title="2. When should the assistant ask you?" />
            <CardBody className="flex flex-col gap-4">
              <div role="radiogroup" aria-label="When the assistant asks you" className="flex flex-col gap-2">
                {APPROACHES.map((a) => {
                  const checked = policy === a.policy;
                  return (
                    <button
                      key={a.policy}
                      type="button"
                      role="radio"
                      aria-checked={checked}
                      onClick={() => setPolicy(a.policy)}
                      className={clsx(
                        "flex items-start gap-3 rounded-xl border px-3 py-2.5 text-left transition-colors",
                        checked ? "border-accent bg-accent-soft ring-1 ring-accent" : "border-line hover:border-line-strong",
                      )}
                    >
                      <span
                        aria-hidden
                        className={clsx("mt-1 size-4 shrink-0 rounded-full border-2", checked ? "border-accent bg-accent ring-2 ring-surface ring-inset" : "border-line-strong")}
                      />
                      <span className="min-w-0">
                        <span className="flex flex-wrap items-center gap-1.5 text-sm font-medium text-ink">
                          {a.title}
                          {a.note ? <Badge tone="accent">{a.note}</Badge> : null}
                        </span>
                        <span className="block text-xs text-ink-2">{a.description}</span>
                      </span>
                    </button>
                  );
                })}
              </div>
              {policy === "user_customized" ? (
                <p className="text-xs text-ink-2">
                  Your preferences: <span className="text-ink">{describePreferences(preferences).join(" · ")}</span>.{" "}
                  <Link href="/preferences" className="font-medium text-accent-strong underline">
                    Change
                  </Link>
                </p>
              ) : null}
              {!APPROACHES.some((a) => a.policy === policy) ? (
                <p className="text-xs text-ink-2">
                  Using an advanced setting: <span className="font-medium text-ink">{policyLabel(policy)}</span>.
                </p>
              ) : null}
              <Button size="lg" onClick={() => start()} loading={runner.busy} disabled={!scenarios} icon={<Play className="size-4" aria-hidden />}>
                Start
              </Button>
              {runner.error ? <ErrorState error={runner.error} /> : null}

              <details className="group rounded-lg border border-line px-3 py-2">
                <summary className="flex cursor-pointer list-none items-center gap-1.5 text-sm text-ink-2 hover:text-ink">
                  <ChevronRight className="size-4 transition-transform group-open:rotate-90" aria-hidden />
                  Advanced options
                </summary>
                <div className="mt-3 flex flex-col gap-4 pb-1">
                  <Field label="Policy" hint="All nine policies, including the research baselines.">
                    {(id) => <Select id={id} value={policy} onChange={setPolicy} options={ALL_POLICIES.map((p) => ({ value: p, label: policyLabel(p) }))} />}
                  </Field>
                  <Field label="Seed" hint="Same seed = same hidden mistakes, whatever the policy. Use it to compare fairly.">
                    {(id) => (
                      <div className="flex gap-2">
                        <TextInput id={id} value={seed} onChange={(v) => setSeed(v.replace(/\D/g, "").slice(0, 9))} />
                        <Button
                          variant="secondary"
                          aria-label="Random seed"
                          onClick={() => setSeed(String(Math.floor(Math.random() * 99999)))}
                          icon={<Shuffle className="size-4" aria-hidden />}
                        />
                      </div>
                    )}
                  </Field>
                  <Toggle label="Run automatically" checked={runner.playing} onChange={runner.setPlaying} description="Off: you click “Next step” yourself." />
                </div>
              </details>
            </CardBody>
          </Card>
        </div>
      </Container>
    );
  }

  const scenario = session.scenario!;
  const simple = view === "simple";
  const statusText =
    session.status === "awaiting_human"
      ? "The assistant is waiting for you"
      : session.status === "completed"
        ? "Finished"
        : session.status === "cancelled"
          ? "Cancelled"
          : runner.playing
            ? "The assistant is working…"
            : "Paused";

  return (
    <Container className="pt-6">
      <div className="flex flex-col gap-3 border-b border-line pb-4 md:flex-row md:items-center md:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-accent-soft text-accent-strong">
            <ScenarioIcon icon={scenario.icon} className="size-5" />
          </span>
          <div className="min-w-0">
            <h1 className="truncate text-xl font-semibold text-ink">{scenario.agent_name}</h1>
            <div className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-ink-2">
              <Badge tone="accent">{simple ? approachLabel(session.policy) : policyLabel(session.policy)}</Badge>
              {simple ? null : <span>Seed {session.seed}</span>}
              <span aria-live="polite" className="font-medium text-ink">
                {statusText}
              </span>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {!runner.done ? (
            <>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => runner.setPlaying(!runner.playing)}
                icon={runner.playing ? <Pause className="size-4" aria-hidden /> : <Play className="size-4" aria-hidden />}
                disabled={session.status !== "running"}
              >
                {runner.playing ? "Pause" : "Play"}
              </Button>
              {simple ? null : (
                <>
                  <Button variant="secondary" size="sm" onClick={runner.step} disabled={runner.busy || session.status !== "running"} icon={<StepForward className="size-4" aria-hidden />}>
                    Next step
                  </Button>
                  <Segmented ariaLabel="Speed" size="sm" value={String(runner.delay)} onChange={(v) => runner.setDelay(Number(v))} options={SPEEDS} />
                </>
              )}
            </>
          ) : null}
          <Button variant="ghost" size="sm" onClick={() => start(true)} icon={<RotateCcw className="size-4" aria-hidden />}>
            Start over
          </Button>
          <Button variant="ghost" size="sm" onClick={tryAnother} icon={<Undo2 className="size-4" aria-hidden />}>
            Change task
          </Button>
          <Segmented ariaLabel="View" size="sm" value={view} onChange={setView} options={VIEWS} />
        </div>
      </div>

      {runner.error ? (
        <div className="mt-4">
          <ErrorState error={runner.error} onRetry={runner.refresh} />
        </div>
      ) : null}

      {simple ? (
        <div className="mt-5 grid grid-cols-1 gap-6 lg:grid-cols-[18rem_minmax(0,1fr)]">
          <aside className="flex flex-col gap-5" aria-label="Task">
            <BriefPanel scenario={scenario} brief={session.brief} />
            <ScheduledQuestions questions={session.pending_questions} currentStep={session.step_index} />
            <div>
              <p className="mb-2 text-xs font-semibold tracking-wide text-ink-2 uppercase">Steps</p>
              <StepRail steps={session.steps} current={session.step_index} done={runner.done} simple />
            </div>
          </aside>

          <section className="flex min-w-0 flex-col gap-4" aria-label="Assistant activity">
            {!tipHidden ? (
              <div className="flex items-start gap-3 rounded-xl border border-accent/25 bg-accent-soft px-4 py-3 text-sm text-ink">
                <ol className="flex flex-1 list-decimal flex-col gap-1 pl-4">
                  <li>
                    Read <strong>what you really want</strong> on the left. The assistant doesn&apos;t know it.
                  </li>
                  <li>The assistant works on its own and stops when something matters.</li>
                  <li>When it stops, check its proposal and approve, change, or reject it.</li>
                </ol>
                <button type="button" onClick={hideTip} aria-label="Hide these tips" className="rounded-md p-1 text-ink-2 hover:bg-surface hover:text-ink">
                  <X className="size-4" aria-hidden />
                </button>
              </div>
            ) : null}
            {session.pending ? (
              <InterventionCardView key={session.pending.intervention_id} card={session.pending} onRespond={runner.respond} busy={runner.busy} simple />
            ) : null}
            {runner.done ? <OutcomeSummary session={session} simple onTryAnother={tryAnother} /> : null}
            <h2 className="text-sm font-semibold text-ink">What the assistant did</h2>
            {timeline.length ? (
              <Timeline items={[...timeline].reverse()} selectedSeq={null} onSelect={() => undefined} simple />
            ) : (
              <EmptyState title="The assistant is about to start">Its first step will appear here.</EmptyState>
            )}
            <p className="text-xs text-ink-3">
              Want scores, factors and the model behind each decision? Switch to <strong>Detailed</strong> view at the top.
            </p>
          </section>
        </div>
      ) : (
        <div className="mt-5 grid gap-5 lg:grid-cols-[16rem_minmax(0,1fr)] xl:grid-cols-[17rem_minmax(0,1fr)_24rem]">
          <aside className="flex flex-col gap-5" aria-label="Task">
            <BriefPanel scenario={scenario} brief={session.brief} />
            <ScheduledQuestions questions={session.pending_questions} currentStep={session.step_index} />
            <div>
              <p className="mb-2 text-xs font-semibold tracking-wide text-ink-2 uppercase">Plan</p>
              <StepRail steps={session.steps} current={session.step_index} done={runner.done} />
            </div>
          </aside>

          <section className="flex min-w-0 flex-col gap-4" aria-label="Agent activity">
            {session.pending ? <InterventionCardView key={session.pending.intervention_id} card={session.pending} onRespond={runner.respond} busy={runner.busy} /> : null}
            {runner.done ? <OutcomeSummary session={session} onTryAnother={tryAnother} /> : null}
            {timeline.length ? (
              <Timeline items={[...timeline].reverse()} selectedSeq={selected?.seq ?? null} onSelect={(i) => setSelectedSeq(i.seq)} />
            ) : (
              <EmptyState title="The agent is about to start">Its first proposal will appear here.</EmptyState>
            )}
          </section>

          <aside className="lg:col-span-2 xl:col-span-1" aria-label="Decision explanation">
            <div className="xl:sticky xl:top-20">
              <Card>
                <CardHeader
                  title="Why did AgentPause decide this?"
                  description={detail ? (session.pending ? "The open intervention" : selected?.label) : "Select a step in the timeline"}
                />
                <CardBody>{detail ? <DecisionExplanation decision={detail} /> : <p className="text-sm text-ink-3">No decision yet.</p>}</CardBody>
              </Card>
              <p className="mt-3 text-xs text-ink-3">
                Signals tagged <em>Simulated</em> come from the scenario script; <em>Default</em> means the value was missing and a documented
                prior was used.{" "}
                <ButtonLink href="/about#model" variant="ghost" size="sm" className="h-auto px-1 py-0">
                  How the model works
                </ButtonLink>
              </p>
            </div>
          </aside>
        </div>
      )}
    </Container>
  );
}

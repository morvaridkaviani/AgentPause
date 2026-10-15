"use client";

import clsx from "clsx";
import { Check, CircleHelp, Hand, OctagonX, Pencil, RotateCcw, ShieldAlert, Undo2, UserRound, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { DecisionBadge } from "@/components/decision/decision-badge";
import { Counterfactuals, TimingExplanation } from "@/components/decision/explanation";
import { Badge, Button, Kbd } from "@/components/ui/primitives";
import { categoryLabel, pct } from "@/lib/format";
import type { InterventionCard as Card, ResponseName } from "@/lib/types";

export interface InterventionCardProps {
  card: Card;
  onRespond: (response: ResponseName, answers: Record<string, string>) => void;
  busy?: boolean;
  /** In the study, policy names and model internals are hidden. */
  showInternals?: boolean;
  /** Everyday wording for the decision ("Asked for approval" rather than ASK_HUMAN). */
  simple?: boolean;
}

const TITLE: Record<string, string> = {
  ASK_HUMAN: "The agent needs your confirmation",
  CLARIFY: "The agent has a quick question",
  BLOCK: "The agent stopped and handed control to you",
};
const SIMPLE_TITLE: Record<string, string> = {
  ASK_HUMAN: "The assistant needs your OK",
  CLARIFY: "The assistant has a quick question",
  BLOCK: "The assistant stopped and handed control to you",
};

export function InterventionCardView({ card, onRespond, busy, showInternals = true, simple = false }: InterventionCardProps) {
  const decision = card.decision;
  const allowed = useMemo(() => new Set(card.allowed_responses ?? []), [card.allowed_responses]);
  const assumptions = useMemo(() => card.assumptions ?? [], [card.assumptions]);
  const [answers, setAnswers] = useState<Record<string, string>>(() =>
    Object.fromEntries(assumptions.map((a) => [a.id, a.agent_value])),
  );
  const [showWhy, setShowWhy] = useState(false);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const action = card.action;
  const isClarify = decision.decision === "CLARIFY";
  const isBlock = decision.decision === "BLOCK";

  useEffect(() => {
    headingRef.current?.focus();
  }, [card.intervention_id]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (busy || e.metaKey || e.ctrlKey || e.altKey) return;
      const target = e.target as HTMLElement | null;
      if (target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) return;
      const map: Record<string, ResponseName> = { a: "approve", e: "edit", r: "reject", w: "ask_why", t: "takeover", o: "override" };
      const response = map[e.key.toLowerCase()];
      if (e.key === "Enter" && isClarify) {
        e.preventDefault();
        onRespond("answer", answers);
      } else if (response && allowed.has(response)) {
        e.preventDefault();
        if (response === "ask_why") {
          setShowWhy(true);
          onRespond("ask_why", {});
        } else {
          onRespond(response, answers);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [allowed, answers, busy, isClarify, onRespond]);

  const reversible = action?.reversible ?? false;
  return (
    <section
      aria-labelledby={`card-${card.intervention_id}`}
      aria-live="polite"
      className="animate-slide-in overflow-hidden rounded-2xl border-2 bg-surface shadow-card"
      style={{ borderColor: `color-mix(in oklab, ${isBlock ? "var(--d-block)" : isClarify ? "var(--d-clarify)" : "var(--d-ask)"} 70%, transparent)` }}
    >
      <header className={clsx("flex flex-wrap items-center justify-between gap-3 px-5 py-3", isBlock ? "tint-block" : isClarify ? "tint-clarify" : "tint-ask")}>
        <div className="flex items-center gap-2">
          {isBlock ? <OctagonX className="size-5" aria-hidden /> : isClarify ? <CircleHelp className="size-5" aria-hidden /> : <Hand className="size-5" aria-hidden />}
          <h2 id={`card-${card.intervention_id}`} ref={headingRef} tabIndex={-1} className="text-base font-semibold text-ink outline-none">
            {simple ? (SIMPLE_TITLE[decision.decision] ?? "Your input is needed") : `AgentPause intervention: ${TITLE[decision.decision] ?? "Your input is needed"}`}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {showInternals ? <DecisionBadge decision={decision.decision} plain={simple} /> : null}
          {action?.simulated ? <Badge tone="accent">Simulated action</Badge> : null}
        </div>
      </header>

      <div className="grid grid-cols-1 gap-5 px-5 py-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
        <div className="flex flex-col gap-4">
          {action ? (
            <div>
              <p className="text-xs font-semibold tracking-wide text-ink-2 uppercase">{simple ? "What the assistant wants to do" : "What the agent wants to do"}</p>
              <p className="mt-1 text-base font-medium text-ink">{action.description || action.label}</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                <Badge>{categoryLabel(action.category)}</Badge>
                <Badge tone={reversible ? "good" : "critical"}>
                  {reversible ? <Undo2 className="size-3" aria-hidden /> : <ShieldAlert className="size-3" aria-hidden />}
                  {reversible ? "Can be undone" : "Cannot be undone"}
                </Badge>
                <Badge title="The agent's self-reported confidence (simulated)">
                  {simple ? `${pct(action.agent_confidence)} sure it's right` : `Agent confidence ${pct(action.agent_confidence)}`}
                </Badge>
              </div>
            </div>
          ) : null}

          {action && Object.keys(action.preview).length ? (
            <div>
              <p className="text-xs font-semibold tracking-wide text-ink-2 uppercase">
                {simple ? "Details: compare them with what you really want" : "Details: check them against your situation"}
              </p>
              <dl className="mt-1.5 overflow-hidden rounded-lg border border-line">
                {Object.entries(action.preview).map(([k, v]) => (
                  <div key={k} className="grid grid-cols-[8rem_minmax(0,1fr)] border-b border-line text-sm last:border-0">
                    <dt className="bg-surface-2 px-3 py-1.5 text-ink-2">{k}</dt>
                    <dd className="px-3 py-1.5 font-medium break-words text-ink">{v}</dd>
                  </div>
                ))}
              </dl>
            </div>
          ) : null}

          {action ? (
            <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-xs font-semibold text-ink-2">What will happen</dt>
                <dd className="mt-0.5 text-ink">{action.consequence}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold text-ink-2">Can it be undone?</dt>
                <dd className="mt-0.5 text-ink">{action.undo || (reversible ? "Yes" : "No")}</dd>
              </div>
              {action.what_could_go_wrong ? (
                <div className="sm:col-span-2">
                  <dt className="text-xs font-semibold text-ink-2">What could go wrong</dt>
                  <dd className="mt-0.5 text-ink">{action.what_could_go_wrong}</dd>
                </div>
              ) : null}
            </dl>
          ) : null}

          {assumptions.length ? (
            <fieldset className="rounded-lg border border-line p-3">
              <legend className="px-1 text-xs font-semibold tracking-wide text-ink-2 uppercase">
                {simple
                  ? assumptions.length === 1
                    ? "The assistant had to guess this"
                    : "The assistant had to guess these"
                  : assumptions.length === 1
                    ? "The agent had to guess this"
                    : "The agent had to guess these"}
              </legend>
              <div className="flex flex-col gap-3">
                {assumptions.map((a) => (
                  <div key={a.id} role="radiogroup" aria-label={a.description}>
                    <p className="text-sm text-ink">
                      It assumed <span className="font-medium">{a.description}</span>{" "}
                      <span className="text-ink-3">({pct(a.confidence)} sure)</span>
                    </p>
                    {a.if_wrong ? <p className="text-xs text-ink-3">If wrong: {a.if_wrong}</p> : null}
                    <div className="mt-1.5 flex flex-wrap gap-2">
                      {a.options.map((option) => {
                        const selected = answers[a.id] === option;
                        return (
                          <label
                            key={option}
                            className={clsx(
                              "flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-1.5 text-sm",
                              selected ? "border-accent bg-accent-soft text-ink" : "border-line-strong text-ink-2 hover:bg-surface-2",
                            )}
                          >
                            <input
                              type="radio"
                              name={`a-${card.intervention_id}-${a.id}`}
                              value={option}
                              checked={selected}
                              onChange={() => setAnswers((prev) => ({ ...prev, [a.id]: option }))}
                              className="accent-[var(--accent)]"
                            />
                            {option}
                            {option === a.agent_value ? <span className="text-xs text-ink-3">(agent&apos;s guess)</span> : null}
                          </label>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </fieldset>
          ) : null}

          {action?.alternatives.length ? (
            <div>
              <p className="text-xs font-semibold text-ink-2">Alternatives you could ask for</p>
              <ul className="mt-1 list-disc pl-5 text-sm text-ink-2">
                {action.alternatives.map((alt) => (
                  <li key={alt}>{alt}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>

        <aside className="flex flex-col gap-3 self-start rounded-xl bg-surface-2 p-4" aria-label="Why AgentPause stopped">
          <p className="text-xs font-semibold tracking-wide text-ink-2 uppercase">{simple ? "Why it's asking" : "Why now?"}</p>
          {decision.timing?.why_now && !simple ? <p className="text-sm text-ink">{decision.timing.why_now}</p> : null}
          {decision.explanation ? <p className={clsx("text-sm", simple ? "text-ink" : "text-ink-2")}>{decision.explanation}</p> : null}
          {simple && decision.timing && !showWhy ? <p className="text-xs text-ink-3">Press “Ask why” to see why it asked now, and not earlier or later.</p> : null}
          {!decision.explanation && !decision.timing ? <p className="text-sm text-ink-3">No explanation is shown in this condition.</p> : null}
          {showWhy && decision.timing ? (
            <div className="mt-1 flex flex-col gap-3 border-t border-line pt-3">
              <TimingExplanation decision={decision} />
              {decision.counterfactuals.some((c) => c.kind === "feature") ? (
                <div>
                  <p className="mb-1 text-xs font-semibold text-ink-2">What would have changed this</p>
                  <Counterfactuals decision={decision} />
                </div>
              ) : null}
            </div>
          ) : null}
        </aside>
      </div>

      <footer className="flex flex-wrap items-center gap-2 border-t border-line px-5 py-3">
        {isClarify ? (
          <Button onClick={() => onRespond("answer", answers)} loading={busy} icon={<Check className="size-4" aria-hidden />}>
            Confirm answer{assumptions.length > 1 ? "s" : ""} <Kbd>↵</Kbd>
          </Button>
        ) : null}
        {allowed.has("approve") ? (
          <Button onClick={() => onRespond("approve", answers)} loading={busy} icon={<Check className="size-4" aria-hidden />}>
            Approve <Kbd>A</Kbd>
          </Button>
        ) : null}
        {allowed.has("edit") ? (
          <Button variant="secondary" onClick={() => onRespond("edit", answers)} disabled={busy} icon={<Pencil className="size-4" aria-hidden />}>
            Edit details <Kbd>E</Kbd>
          </Button>
        ) : null}
        {allowed.has("reject") ? (
          <Button variant="secondary" onClick={() => onRespond("reject", answers)} disabled={busy} icon={<X className="size-4" aria-hidden />}>
            Reject <Kbd>R</Kbd>
          </Button>
        ) : null}
        {allowed.has("takeover") ? (
          <Button onClick={() => onRespond("takeover", answers)} loading={busy} icon={<UserRound className="size-4" aria-hidden />}>
            I&apos;ll do this step <Kbd>T</Kbd>
          </Button>
        ) : null}
        {allowed.has("override") ? (
          <Button variant="outline" onClick={() => onRespond("override", answers)} disabled={busy} icon={<RotateCcw className="size-4" aria-hidden />}>
            Let the agent proceed <Kbd>O</Kbd>
          </Button>
        ) : null}
        {allowed.has("ask_why") ? (
          <Button
            variant="ghost"
            onClick={() => {
              setShowWhy(true);
              onRespond("ask_why", {});
            }}
            disabled={busy || showWhy || !decision.timing}
            icon={<CircleHelp className="size-4" aria-hidden />}
          >
            Ask why <Kbd>W</Kbd>
          </Button>
        ) : null}
        <div className="ml-auto">
          {allowed.has("cancel_task") ? (
            <Button variant="danger" size="sm" onClick={() => onRespond("cancel_task", {})} disabled={busy}>
              Cancel task
            </Button>
          ) : null}
        </div>
      </footer>
    </section>
  );
}

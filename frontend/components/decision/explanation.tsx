"use client";

import clsx from "clsx";
import { ArrowDown, ArrowUp, Clock3, GitBranch, History, Info, Minus } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/primitives";
import { Meter } from "@/components/ui/stat";
import { pct, PROVENANCE_HELP, PROVENANCE_LABEL, stepLabel } from "@/lib/format";
import type { Decision, DeferredQuestion, Factor, Provenance } from "@/lib/types";

import { DecisionBadge } from "./decision-badge";

export function ProvenanceTag({ provenance }: { provenance: Provenance }) {
  const tone = provenance === "default" ? "warning" : provenance === "simulated" ? "accent" : "neutral";
  return (
    <Badge tone={tone} title={PROVENANCE_HELP[provenance]} className="font-normal">
      {PROVENANCE_LABEL[provenance]}
    </Badge>
  );
}

/** Signed horizontal bars: how much each signal moved the decision score. */
export function FactorBars({ factors, limit = 8 }: { factors: Factor[]; limit?: number }) {
  const shown = [...factors].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)).slice(0, limit);
  const max = Math.max(0.05, ...shown.map((f) => Math.abs(f.contribution)));
  if (!shown.length) return <p className="text-sm text-ink-3">No factor attribution for this decision.</p>;
  return (
    <ul className="flex flex-col gap-2.5" aria-label="Factors">
      {shown.map((f) => {
        const width = (Math.abs(f.contribution) / max) * 50;
        const toward = f.contribution > 1e-9;
        const away = f.contribution < -1e-9;
        const Icon = toward ? ArrowUp : away ? ArrowDown : Minus;
        return (
          <li key={f.signal} className="grid grid-cols-[minmax(0,1fr)_7rem] items-center gap-3 sm:grid-cols-[minmax(0,12rem)_minmax(0,1fr)_6rem]">
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="truncate text-sm font-medium text-ink" title={f.description}>
                  {f.label}
                </span>
              </div>
              <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-ink-2">
                <span className="tabular">{f.display}</span>
                {f.level ? <span className="text-ink-3">· {f.level}</span> : null}
                <ProvenanceTag provenance={f.provenance} />
              </div>
            </div>
            <div className="relative hidden h-3 sm:block" aria-hidden>
              <div className="absolute inset-y-0 left-1/2 w-px bg-line-strong" />
              <div
                className="absolute inset-y-0 rounded-sm"
                style={{
                  left: toward ? "50%" : `${50 - width}%`,
                  width: `${width}%`,
                  background: toward ? "var(--d-ask)" : "var(--d-continue)",
                  opacity: 0.85,
                }}
              />
            </div>
            <div className="flex items-center justify-end gap-1 text-xs text-ink-2">
              <Icon className="size-3.5" aria-hidden />
              <span className="tabular">{f.contribution >= 0 ? "+" : ""}{f.contribution.toFixed(2)}</span>
              <span className="sr-only">{toward ? "pushes toward asking you" : away ? "pushes toward acting autonomously" : "no effect"}</span>
            </div>
          </li>
        );
      })}
      <li className="text-xs text-ink-3">
        Bars show how the score changes when a signal is set to a low-risk reference value (one at a time; interactions are
        not decomposed). <span className="font-medium">Right</span> = toward asking you, <span className="font-medium">left</span>{" "}
        = toward acting.
      </li>
    </ul>
  );
}

export function TimingExplanation({ decision }: { decision: Decision }) {
  const [open, setOpen] = useState(false);
  const t = decision.timing;
  if (!t) return null;
  return (
    <div className="flex flex-col gap-3">
      <div>
        <h4 className="flex items-center gap-1.5 text-xs font-semibold tracking-wide text-ink-2 uppercase">
          <Clock3 className="size-3.5" aria-hidden /> Why now?
        </h4>
        <p className="mt-1 text-sm text-ink">{t.why_now}</p>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-line bg-surface-2 p-3">
          <h4 className="flex items-center gap-1.5 text-xs font-semibold text-ink-2">
            <History className="size-3.5" aria-hidden /> Why not earlier?
          </h4>
          <p className="mt-1 text-sm text-ink">{t.why_not_earlier}</p>
        </div>
        <div className="rounded-lg border border-line bg-surface-2 p-3">
          <h4 className="flex items-center gap-1.5 text-xs font-semibold text-ink-2">
            <GitBranch className="size-3.5" aria-hidden /> Why not later?
          </h4>
          <p className="mt-1 text-sm text-ink">{t.why_not_later}</p>
        </div>
      </div>
      {t.earlier.length || t.later.length ? (
        <div>
          <button type="button" onClick={() => setOpen((v) => !v)} aria-expanded={open} className="text-xs font-medium text-accent-strong hover:underline">
            {open ? "Hide" : "Show"} step-by-step timing analysis
          </button>
          {open ? (
            <ol className="mt-2 flex flex-col gap-1 text-xs text-ink-2">
              {t.earlier.map((n) => (
                <li key={`e-${n.step}-${n.text}`} className="flex gap-2">
                  <span className="w-16 shrink-0 font-medium text-ink-3">{stepLabel(n.step)}</span>
                  <span>{n.text}</span>
                </li>
              ))}
              <li className="flex gap-2 font-medium text-ink">
                <span className="w-16 shrink-0">{stepLabel(decision.step)}</span>
                <span>Now: {decision.decision.replace("_", " ").toLowerCase()}</span>
              </li>
              {t.later.map((n) => (
                <li key={`l-${n.step}-${n.text}`} className="flex gap-2">
                  <span className="w-16 shrink-0 font-medium text-ink-3">{stepLabel(n.step)}</span>
                  <span>{n.text}</span>
                </li>
              ))}
            </ol>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function Counterfactuals({ decision }: { decision: Decision }) {
  const items = decision.counterfactuals.filter((c) => c.kind === "feature");
  if (!items.length) return <p className="text-sm text-ink-3">No small change to a single signal would have changed this decision.</p>;
  return (
    <ul className="flex flex-col gap-2">
      {items.map((c) => (
        <li key={c.text} className="flex items-start gap-2 text-sm text-ink">
          {c.counterfactual_decision ? <DecisionBadge decision={c.counterfactual_decision} size="sm" className="mt-0.5" /> : null}
          <span>{c.text}</span>
        </li>
      ))}
    </ul>
  );
}

export function ScheduledQuestions({ questions, currentStep }: { questions: DeferredQuestion[]; currentStep?: number }) {
  if (!questions.length) return null;
  return (
    <div className="rounded-lg border border-d-defer/40 tint-defer px-3 py-2.5" role="status">
      <p className="flex items-center gap-1.5 text-xs font-semibold text-ink">
        <Clock3 className="size-3.5" style={{ color: "var(--d-defer)" }} aria-hidden />
        {questions.length === 1 ? "1 question saved for later" : `${questions.length} questions saved for later`}
      </p>
      <ul className="mt-1 flex flex-col gap-1 text-xs text-ink-2">
        {questions.map((q) => (
          <li key={q.assumption_id}>
            “{q.description}” at {stepLabel(q.target_step)}
            {q.deadline_action ? <> (at the latest before “{q.deadline_action.replace(/_/g, " ")}”)</> : null}
            {currentStep !== undefined && q.target_step === currentStep ? " · now" : ""}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ModelTerms({ decision }: { decision: Decision }) {
  const terms = decision.terms;
  if (!("benefit_action" in terms)) {
    const entries = Object.entries(terms).filter(([, v]) => typeof v === "number" || typeof v === "string");
    if (!entries.length) return null;
    return (
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        {entries.map(([k, v]) => (
          <div key={k} className="contents">
            <dt className="text-ink-2">{k.replace(/_/g, " ")}</dt>
            <dd className="tabular text-right text-ink">{typeof v === "number" ? v.toFixed(3) : String(v)}</dd>
          </div>
        ))}
      </dl>
    );
  }
  const n = (k: string) => (typeof terms[k] === "number" ? (terms[k] as number) : 0);
  const rows: [string, string, string][] = [
    ["p_err", "P(proceeding is wrong)", pct(n("p_error_action"), 1)],
    ["C_err", "Harm if wrong (1 = worst)", n("error_cost").toFixed(3)],
    ["e", "P(you catch it if asked)", pct(n("catch_probability"), 0)],
    ["B", "Benefit of asking = p_err·C_err·e", n("benefit_action").toFixed(3)],
    ["C_int", "Cost of interrupting now", n("interruption_cost_now").toFixed(3)],
    ["V", "Net value of asking now = B − C_int", n("value_action").toFixed(3)],
  ];
  return (
    <div>
      <table className="w-full text-xs">
        <tbody>
          {rows.map(([sym, label, value]) => (
            <tr key={sym} className="border-b border-line last:border-0">
              <td className="py-1 pr-2 font-mono text-ink-2">{sym}</td>
              <td className="py-1 pr-2 text-ink-2">{label}</td>
              <td className="tabular py-1 text-right text-ink">{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-ink-3">
        For the action approval only. Clarification questions are valued per assumption, including rework and the best moment
        to ask. All parameters are documented priors, not calibrated estimates.
      </p>
    </div>
  );
}

/** The full "Why did AgentPause decide this?" panel. */
export function DecisionExplanation({ decision, compact = false }: { decision: Decision; compact?: boolean }) {
  const missing = decision.signals.missing ?? [];
  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-3">
        <DecisionBadge decision={decision.decision} size="lg" />
        <div className="min-w-40 flex-1">
          <div className="flex justify-between text-xs text-ink-2">
            <span>Intervention pressure</span>
            <span className="tabular">{decision.score.toFixed(2)}</span>
          </div>
          <Meter value={decision.score} threshold={0.5} label="Intervention pressure" className="mt-1" />
        </div>
        {decision.confidence !== null ? (
          <Badge tone={decision.confidence < 0.75 ? "warning" : "neutral"} title="Share of small perturbations of estimated signals that give the same decision">
            Stability {pct(decision.confidence)}
          </Badge>
        ) : null}
      </div>
      {decision.explanation ? <p className="text-sm leading-relaxed text-ink">{decision.explanation}</p> : null}
      {decision.reason_codes.length ? (
        <div className="flex flex-wrap gap-1.5" aria-label="Reason codes">
          {decision.reason_codes.map((code) => (
            <Badge key={code} tone={code === "MISSING_SIGNAL_DEFAULTED" || code === "CONTRADICTORY_SIGNALS" ? "warning" : "neutral"} className="font-mono">
              {code}
            </Badge>
          ))}
        </div>
      ) : null}
      {decision.timing ? (
        <section>
          <TimingExplanation decision={decision} />
        </section>
      ) : null}
      {decision.factors.length ? (
        <section>
          <h4 className="mb-2 text-xs font-semibold tracking-wide text-ink-2 uppercase">Top factors</h4>
          <FactorBars factors={decision.factors} limit={compact ? 5 : 8} />
        </section>
      ) : null}
      {decision.counterfactuals.some((c) => c.kind === "feature") ? (
        <section>
          <h4 className="mb-2 text-xs font-semibold tracking-wide text-ink-2 uppercase">What would change the decision</h4>
          <Counterfactuals decision={decision} />
        </section>
      ) : null}
      {!compact && Object.keys(decision.terms).length ? (
        <section>
          <h4 className="mb-2 text-xs font-semibold tracking-wide text-ink-2 uppercase">Model terms</h4>
          <ModelTerms decision={decision} />
        </section>
      ) : null}
      {missing.length || decision.warnings.length ? (
        <div className={clsx("flex gap-2 rounded-lg border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-ink-2")}>
          <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden />
          <div>
            {missing.length ? <p>Defaults used for: {missing.map((m) => m.replace(/_/g, " ")).join(", ")}.</p> : null}
            {decision.warnings.map((w) => (
              <p key={w}>{w}</p>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

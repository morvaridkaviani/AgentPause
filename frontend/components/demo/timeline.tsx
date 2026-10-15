"use client";

import clsx from "clsx";
import { CheckCircle2, CircleAlert } from "lucide-react";

import { DecisionBadge } from "@/components/decision/decision-badge";
import { Badge } from "@/components/ui/primitives";
import { level, pct, RESPONSE_LABEL, stepLabel } from "@/lib/format";
import type { TimelineItem } from "@/lib/types";

const RISK_TONE = { LOW: "good", MEDIUM: "warning", HIGH: "critical", "—": "neutral" } as const;

function SignalChip({ label, value, kind }: { label: string; value: unknown; kind: "confidence" | "risk" | "reversibility" | "load" }) {
  const v = typeof value === "number" ? value : null;
  const lvl = level(v, kind);
  return (
    <span className="inline-flex items-center gap-1 text-xs text-ink-2">
      <span className="text-ink-3">{label}</span>
      <span className="font-medium text-ink">{lvl === "—" ? "—" : lvl}</span>
    </span>
  );
}

/** The live agent timeline: one card per proposed action with the key signals and decision. */
export function Timeline({
  items,
  selectedSeq,
  onSelect,
  showGroundTruth = true,
  simple = false,
}: {
  items: TimelineItem[];
  selectedSeq: number | null;
  onSelect: (item: TimelineItem) => void;
  showGroundTruth?: boolean;
  /** Plain-language labels, no signal chips or scores, and no selection. */
  simple?: boolean;
}) {
  if (simple) return <SimpleTimeline items={items} showGroundTruth={showGroundTruth} />;
  return (
    <ol className="flex flex-col gap-2" aria-label="Agent timeline">
      {items.map((item) => {
        const selected = selectedSeq === item.seq;
        const risk = level(
          typeof item.signals.severity === "number" && typeof item.signals.recoverability === "number"
            ? (item.signals.severity as number) * (1 - (item.signals.recoverability as number) * 0.85)
            : null,
          "risk",
        );
        const harmed = showGroundTruth && item.harm && item.harm.length > 0;
        return (
          <li key={item.seq} className="animate-slide-in">
            <button
              type="button"
              onClick={() => onSelect(item)}
              aria-pressed={selected}
              disabled={item.skipped}
              className={clsx(
                "w-full rounded-xl border bg-surface px-4 py-3 text-left transition-colors",
                selected ? "border-accent ring-1 ring-accent" : "border-line hover:border-line-strong",
                item.skipped && "opacity-70",
              )}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-xs text-ink-3">{stepLabel(item.step_index)}</p>
                  <p className="font-medium text-ink">{item.label}</p>
                  {item.description ? <p className="mt-0.5 line-clamp-2 text-sm text-ink-2">{item.description}</p> : null}
                </div>
                <DecisionBadge decision={item.decision} />
              </div>
              {!item.skipped ? (
                <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1">
                  <span className="inline-flex items-center gap-1 text-xs">
                    <span className="text-ink-3">Risk</span>
                    <Badge tone={RISK_TONE[risk]} className="px-1 py-0 text-[11px]">
                      {risk}
                    </Badge>
                  </span>
                  <SignalChip label="Confidence" value={item.signals.agent_confidence} kind="confidence" />
                  <SignalChip label="Intent clarity" value={item.signals.intent_confidence} kind="confidence" />
                  <SignalChip label="Reversibility" value={item.signals.recoverability} kind="reversibility" />
                  {item.response ? <Badge tone="accent">{RESPONSE_LABEL[item.response] ?? item.response}</Badge> : null}
                  {item.deferred.length ? <Badge>{item.deferred.length} question{item.deferred.length > 1 ? "s" : ""} scheduled</Badge> : null}
                  {item.executed && !harmed ? (
                    <span className="inline-flex items-center gap-1 text-xs text-ink-3">
                      <CheckCircle2 className="size-3.5" aria-hidden /> executed (simulated)
                    </span>
                  ) : null}
                  {harmed ? (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-critical">
                      <CircleAlert className="size-3.5" aria-hidden /> an error was executed here
                    </span>
                  ) : null}
                </div>
              ) : null}
              {item.explanation && !item.skipped ? <p className="mt-2 text-sm text-ink-2">{item.explanation}</p> : null}
              {item.confidence !== null && !item.skipped ? (
                <p className="mt-1 text-xs text-ink-3">
                  Score {item.score.toFixed(2)} · stability {pct(item.confidence)}
                </p>
              ) : null}
            </button>
          </li>
        );
      })}
    </ol>
  );
}

function SimpleTimeline({ items, showGroundTruth }: { items: TimelineItem[]; showGroundTruth: boolean }) {
  return (
    <ol className="flex flex-col gap-2" aria-label="What the assistant did">
      {items.map((item) => {
        const harmed = showGroundTruth && item.harm && item.harm.length > 0;
        return (
          <li key={item.seq} className={clsx("animate-slide-in rounded-xl border border-line bg-surface px-4 py-3", item.skipped && "opacity-70")}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-xs text-ink-3">{stepLabel(item.step_index)}</p>
                <p className="font-medium text-ink">{item.label}</p>
              </div>
              <DecisionBadge decision={item.decision} plain />
            </div>
            {item.explanation && !item.skipped ? <p className="mt-1.5 text-sm text-ink-2">{item.explanation}</p> : null}
            <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
              {item.response ? <Badge tone="accent">You: {(RESPONSE_LABEL[item.response] ?? item.response).toLowerCase()}</Badge> : null}
              {item.executed && !harmed ? (
                <span className="inline-flex items-center gap-1 text-ink-3">
                  <CheckCircle2 className="size-3.5" aria-hidden /> done (simulated)
                </span>
              ) : null}
              {harmed ? (
                <span className="inline-flex items-center gap-1 font-medium text-critical">
                  <CircleAlert className="size-3.5" aria-hidden /> a mistake went through here
                </span>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

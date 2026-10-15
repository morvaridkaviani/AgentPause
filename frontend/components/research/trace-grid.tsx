import clsx from "clsx";
import { TriangleAlert } from "lucide-react";

import { DECISION_ICON } from "@/components/decision/decision-badge";
import { DECISION_META, DECISION_ORDER } from "@/lib/format";
import type { TraceStep } from "@/lib/types";

/** Rows = policies, columns = steps of one episode. Shows where each policy interrupts. */
export function TraceGrid({
  traces,
  labelOf,
}: {
  traces: { policy: string; steps: TraceStep[]; outcome: Record<string, unknown> }[];
  labelOf: (p: string) => string;
}) {
  const columns = new Map<number, string>();
  traces.forEach((t) => t.steps.forEach((s) => columns.set(s.step_index, s.label)));
  const steps = [...columns.entries()].sort((a, b) => a[0] - b[0]);
  const errorSteps = new Set(traces.flatMap((t) => t.steps.filter((s) => s.error_present).map((s) => s.step_index)));
  return (
    <div className="overflow-x-auto rounded-xl border border-line bg-surface">
      <table className="w-full min-w-[720px] border-collapse text-xs">
        <caption className="px-4 pt-3 text-left text-sm font-semibold text-ink">
          Same episode, different policies
          <span className="block text-xs font-normal text-ink-2">
            Identical seed, so identical injected mistakes and true intent. Several decisions at one step mean the agent re-proposed after a
            clarification or rejection.
          </span>
        </caption>
        <thead>
          <tr className="border-b border-line">
            <th scope="col" className="sticky left-0 bg-surface px-3 py-2 text-left font-medium text-ink-2">
              Policy
            </th>
            {steps.map(([i, label]) => (
              <th key={i} scope="col" className={clsx("px-2 py-2 text-left font-medium text-ink-2", errorSteps.has(i) && "bg-critical/5")}>
                <span className="block text-ink-3">{i + 1}</span>
                <span className="block max-w-28 truncate" title={label}>
                  {label}
                </span>
                {errorSteps.has(i) ? (
                  <span className="mt-0.5 inline-flex items-center gap-0.5 text-critical">
                    <TriangleAlert className="size-3" aria-hidden /> error
                  </span>
                ) : null}
              </th>
            ))}
            <th scope="col" className="px-3 py-2 text-left font-medium text-ink-2">
              Outcome
            </th>
          </tr>
        </thead>
        <tbody>
          {traces.map((t) => {
            const summary = (t.outcome.summary ?? {}) as Record<string, number>;
            return (
              <tr key={t.policy} className="border-b border-line last:border-0">
                <th scope="row" className="sticky left-0 bg-surface px-3 py-2 text-left font-medium text-ink">
                  {labelOf(t.policy)}
                </th>
                {steps.map(([i]) => {
                  const cells = t.steps.filter((s) => s.step_index === i);
                  return (
                    <td key={i} className={clsx("px-2 py-2 align-top", errorSteps.has(i) && "bg-critical/5")}>
                      <div className="flex flex-col gap-1">
                        {cells.length === 0 ? <span className="text-ink-3">skipped</span> : null}
                        {cells.map((c, k) => {
                          const meta = DECISION_META[c.decision];
                          const Icon = DECISION_ICON[c.decision];
                          return (
                            <span key={k} className={clsx("inline-flex items-center gap-1 rounded px-1.5 py-0.5 font-medium text-ink", meta.tint)} title={`${meta.label}${c.user_response ? ` → ${c.user_response}` : ""}`}>
                              <Icon className="size-3" style={{ color: meta.color }} aria-hidden />
                              {meta.short}
                              {c.n_questions > 1 ? <span className="text-ink-2">×{c.n_questions}</span> : null}
                            </span>
                          );
                        })}
                      </div>
                    </td>
                  );
                })}
                <td className="px-3 py-2 align-top text-ink-2">
                  <span className={clsx("font-medium", t.outcome.task_success ? "text-good-ink" : "text-critical")}>
                    {t.outcome.task_success ? "Success" : "Error got through"}
                  </span>
                  <span className="block">{summary.interventions ?? 0} interruptions</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <ul className="flex flex-wrap gap-3 border-t border-line px-4 py-2" aria-label="Legend">
        {DECISION_ORDER.map((d) => {
          const Icon = DECISION_ICON[d];
          return (
            <li key={d} className="flex items-center gap-1 text-xs text-ink-2">
              <Icon className="size-3" style={{ color: DECISION_META[d].color }} aria-hidden />
              {DECISION_META[d].label}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

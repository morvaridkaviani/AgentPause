import { num, pct, policyLabel } from "@/lib/format";
import type { Aggregate } from "@/lib/types";

export const SUMMARY_METRICS: { key: string; label: string; kind: "count" | "rate" | "seconds" | "harm"; lowerIsBetter?: boolean }[] = [
  { key: "interventions", label: "Interruptions / episode", kind: "count", lowerIsBetter: true },
  { key: "questions", label: "Questions / episode", kind: "count", lowerIsBetter: true },
  { key: "deferrals", label: "Deferrals / episode", kind: "count" },
  { key: "unnecessary_rate", label: "Unnecessary rate", kind: "rate", lowerIsBetter: true },
  { key: "missed_rate", label: "Missed rate", kind: "rate", lowerIsBetter: true },
  { key: "recovery_rate", label: "Recovery rate", kind: "rate" },
  { key: "harm", label: "Harm / episode", kind: "harm", lowerIsBetter: true },
  { key: "task_success", label: "Task success", kind: "rate" },
  { key: "rework_steps", label: "Rework steps", kind: "count", lowerIsBetter: true },
  { key: "task_duration_s", label: "Task time (s)", kind: "seconds", lowerIsBetter: true },
];

export function formatMetric(kind: string, value: unknown): string {
  if (kind === "rate") return pct(value, 1);
  if (kind === "seconds") return num(value, 0);
  if (kind === "harm") return num(value, 3);
  return num(value, 2);
}

export function MetricTable({ rows, labelOf = policyLabel, groupKey = "policy" }: { rows: Aggregate[]; labelOf?: (p: string) => string; groupKey?: string }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line bg-surface">
      <table className="w-full min-w-[860px] text-sm">
        <thead>
          <tr className="border-b border-line text-left text-xs text-ink-2">
            <th scope="col" className="px-3 py-2 font-medium">
              Policy
            </th>
            <th scope="col" className="px-3 py-2 text-right font-medium">
              Episodes
            </th>
            {SUMMARY_METRICS.map((m) => (
              <th key={m.key} scope="col" className="px-3 py-2 text-right font-medium">
                {m.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={String(row[groupKey])} className="border-b border-line last:border-0">
              <th scope="row" className="px-3 py-2 text-left font-medium text-ink">
                {labelOf(String(row[groupKey]))}
              </th>
              <td className="tabular px-3 py-2 text-right text-ink-2">{row.episodes}</td>
              {SUMMARY_METRICS.map((m) => {
                const ci = row[`${m.key}_ci`] as [number | null, number | null] | undefined;
                return (
                  <td key={m.key} className="tabular px-3 py-2 text-right text-ink">
                    {formatMetric(m.kind, row[m.key])}
                    {ci && ci[0] !== null ? (
                      <span className="block text-[11px] text-ink-3">
                        {formatMetric(m.kind, ci[0])}–{formatMetric(m.kind, ci[1])}
                      </span>
                    ) : null}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ComparisonTable({ rows, labelOf = policyLabel }: { rows: Record<string, unknown>[]; labelOf?: (p: string) => string }) {
  const metrics = [
    { key: "interventions", label: "Interruptions" },
    { key: "missed_interventions", label: "Missed interventions" },
    { key: "harm", label: "Harm" },
    { key: "rework_steps", label: "Rework steps" },
  ];
  if (!rows.length) return null;
  return (
    <div className="overflow-x-auto rounded-xl border border-line bg-surface">
      <table className="w-full min-w-[640px] text-sm">
        <caption className="px-3 pt-3 text-left text-sm font-semibold text-ink">
          Paired differences: {labelOf(String(rows[0]!.treatment))} − baseline
          <span className="block text-xs font-normal text-ink-2">Mean per-episode difference on identical seeds, with 95% bootstrap CI. Negative = fewer/less.</span>
        </caption>
        <thead>
          <tr className="border-b border-line text-left text-xs text-ink-2">
            <th scope="col" className="px-3 py-2 font-medium">
              Baseline
            </th>
            <th scope="col" className="px-3 py-2 text-right font-medium">
              Pairs
            </th>
            {metrics.map((m) => (
              <th key={m.key} scope="col" className="px-3 py-2 text-right font-medium">
                {m.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={`${String(r.condition ?? "")}-${String(r.baseline)}`} className="border-b border-line last:border-0">
              <th scope="row" className="px-3 py-2 text-left font-medium text-ink">
                {labelOf(String(r.baseline))}
              </th>
              <td className="tabular px-3 py-2 text-right text-ink-2">{String(r.pairs)}</td>
              {metrics.map((m) => {
                const cell = (r[m.key] ?? {}) as { mean_diff?: number | null; ci?: [number | null, number | null] };
                const excludesZero = cell.ci && cell.ci[0] !== null && cell.ci[1] !== null && (cell.ci[0]! > 0 || cell.ci[1]! < 0);
                return (
                  <td key={m.key} className="tabular px-3 py-2 text-right text-ink">
                    <span className={excludesZero ? "font-semibold" : undefined}>
                      {cell.mean_diff === null || cell.mean_diff === undefined ? "—" : `${cell.mean_diff >= 0 ? "+" : ""}${cell.mean_diff.toFixed(3)}`}
                    </span>
                    {cell.ci && cell.ci[0] !== null ? (
                      <span className="block text-[11px] text-ink-3">
                        [{cell.ci[0]!.toFixed(3)}, {cell.ci[1]!.toFixed(3)}]
                      </span>
                    ) : null}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

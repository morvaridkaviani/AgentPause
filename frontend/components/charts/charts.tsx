"use client";

import { useState, type ReactNode } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ErrorBar,
  LabelList,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { DECISION_META, DECISION_ORDER } from "@/lib/format";

/** Ordinal ramp (blue), lightest step still clears 2:1 on the surface. */
export const ORDINAL_BLUE = ["#86b6ef", "#3987e5", "#1c5cab"];
/** Categorical slots in validated order (light mode values via CSS variables where possible). */
export const SERIES = ["var(--d-continue)", "var(--d-defer)", "var(--d-clarify)", "var(--d-ask)"];

const AXIS = { stroke: "var(--axis)", tick: { fill: "var(--ink-2)", fontSize: 12 }, tickLine: false };

function TooltipBox({ title, rows }: { title?: ReactNode; rows: { label: ReactNode; value: ReactNode; color?: string }[] }) {
  return (
    <div className="rounded-lg border border-line bg-surface px-3 py-2 text-xs shadow-card">
      {title ? <p className="mb-1 font-medium text-ink">{title}</p> : null}
      {rows.map((r, i) => (
        <p key={i} className="flex items-center gap-2 text-ink-2">
          {r.color ? <span aria-hidden className="inline-block size-2 rounded-sm" style={{ background: r.color }} /> : null}
          <span>{r.label}</span>
          <span className="tabular ml-auto pl-3 font-medium text-ink">{r.value}</span>
        </p>
      ))}
    </div>
  );
}

/** Wraps a chart with a title, an optional legend, and a table view (the accessible fallback). */
export function ChartFrame({
  title,
  description,
  legend,
  table,
  children,
}: {
  title: string;
  description?: ReactNode;
  legend?: { label: string; color: string }[];
  table: { columns: string[]; rows: (string | number)[][] };
  children: ReactNode;
}) {
  const [showTable, setShowTable] = useState(false);
  return (
    <figure className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <figcaption className="text-sm font-semibold text-ink">{title}</figcaption>
          {description ? <p className="mt-0.5 text-xs text-ink-2">{description}</p> : null}
        </div>
        <button type="button" onClick={() => setShowTable((v) => !v)} aria-pressed={showTable} className="text-xs font-medium text-accent-strong hover:underline">
          {showTable ? "Show chart" : "Show table"}
        </button>
      </div>
      {legend && legend.length > 1 ? (
        <ul className="flex flex-wrap gap-x-4 gap-y-1" aria-label="Legend">
          {legend.map((l) => (
            <li key={l.label} className="flex items-center gap-1.5 text-xs text-ink-2">
              <span aria-hidden className="inline-block size-2.5 rounded-sm" style={{ background: l.color }} />
              {l.label}
            </li>
          ))}
        </ul>
      ) : null}
      {showTable ? (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-line text-left text-ink-2">
                {table.columns.map((c) => (
                  <th key={c} scope="col" className="py-1.5 pr-3 font-medium">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, i) => (
                <tr key={i} className="border-b border-line last:border-0">
                  {row.map((cell, j) => (
                    <td key={j} className="tabular py-1.5 pr-3 text-ink">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div aria-hidden>{children}</div>
      )}
    </figure>
  );
}

export interface BarDatum {
  label: string;
  value: number | null;
  ci?: [number | null, number | null] | null;
}

/** Horizontal bars for one measure across categories (one series, one hue). */
export function MetricBars({
  title,
  description,
  data,
  format = (v: number) => v.toFixed(2),
  color = "var(--accent)",
  max,
}: {
  title: string;
  description?: ReactNode;
  data: BarDatum[];
  format?: (v: number) => string;
  color?: string;
  max?: number;
}) {
  const rows = data.map((d) => ({
    label: d.label,
    value: d.value ?? 0,
    missing: d.value === null,
    err: d.ci && d.ci[0] !== null && d.ci[1] !== null && d.value !== null ? [d.value - (d.ci[0] as number), (d.ci[1] as number) - d.value] : [0, 0],
    text: d.value === null ? "—" : format(d.value),
  }));
  const height = Math.max(120, rows.length * 34 + 30);
  return (
    <ChartFrame
      title={title}
      description={description}
      table={{
        columns: ["", title, "95% CI"],
        rows: data.map((d) => [d.label, d.value === null ? "—" : format(d.value), d.ci && d.ci[0] !== null ? `${format(d.ci[0] as number)} – ${format(d.ci[1] as number)}` : "—"]),
      }}
    >
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 56, bottom: 4, left: 4 }}>
          <CartesianGrid horizontal={false} stroke="var(--grid)" />
          <XAxis type="number" {...AXIS} domain={[0, max ?? "auto"]} tickFormatter={(v: number) => format(v)} />
          <YAxis type="category" dataKey="label" width={150} {...AXIS} axisLine={false} />
          <Tooltip
            cursor={{ fill: "var(--surface-2)" }}
            content={({ active, payload }) =>
              active && payload?.[0] ? (
                <TooltipBox title={String(payload[0].payload.label)} rows={[{ label: title, value: payload[0].payload.text as string, color }]} />
              ) : null
            }
          />
          <Bar dataKey="value" fill={color} radius={[0, 4, 4, 0]} barSize={18} isAnimationActive={false}>
            <ErrorBar dataKey="err" width={4} strokeWidth={1.5} stroke="var(--ink-2)" direction="x" />
            <LabelList dataKey="text" position="right" offset={8} fill="var(--ink)" fontSize={12} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

/** Stacked horizontal bars: share of each decision type per policy. */
export function DecisionMix({ rows, title = "Decision mix" }: { rows: (Record<string, number | string> & { policy: string; label: string })[]; title?: string }) {
  const data = rows.map((r) => {
    const total = DECISION_ORDER.reduce((s, d) => s + (Number(r[d]) || 0), 0) || 1;
    return { label: r.label, ...Object.fromEntries(DECISION_ORDER.map((d) => [d, (Number(r[d]) || 0) / total])) };
  });
  return (
    <ChartFrame
      title={title}
      description="Share of all decisions, per policy."
      legend={DECISION_ORDER.map((d) => ({ label: DECISION_META[d].label, color: DECISION_META[d].color }))}
      table={{ columns: ["Policy", ...DECISION_ORDER.map((d) => DECISION_META[d].label)], rows: rows.map((r) => [r.label, ...DECISION_ORDER.map((d) => Number(r[d]) || 0)]) }}
    >
      <ResponsiveContainer width="100%" height={Math.max(120, data.length * 34 + 30)}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 4 }}>
          <XAxis type="number" domain={[0, 1]} {...AXIS} tickFormatter={(v: number) => `${Math.round(v * 100)}%`} />
          <YAxis type="category" dataKey="label" width={150} {...AXIS} axisLine={false} />
          <Tooltip
            cursor={{ fill: "var(--surface-2)" }}
            content={({ active, payload, label }) =>
              active && payload?.length ? (
                <TooltipBox
                  title={String(label)}
                  rows={payload.map((p) => ({ label: DECISION_META[p.dataKey as keyof typeof DECISION_META].label, value: `${Math.round(Number(p.value) * 100)}%`, color: String(p.color) }))}
                />
              ) : null
            }
          />
          {DECISION_ORDER.map((d, i) => (
            <Bar key={d} dataKey={d} stackId="a" fill={DECISION_META[d].color} stroke="var(--surface)" strokeWidth={2} barSize={20} isAnimationActive={false} radius={i === DECISION_ORDER.length - 1 ? [0, 4, 4, 0] : 0} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

/** When interventions happen during the task: small multiples, one panel per policy. */
export function TimingMultiples({ data, policies, labelOf }: { data: { policy: string; bin: string; count: number; share: number }[]; policies: string[]; labelOf: (p: string) => string }) {
  const bins = Array.from(new Set(data.map((d) => d.bin)));
  return (
    <ChartFrame
      title="When interruptions happen"
      description="Share of each policy's interruptions by task progress."
      table={{ columns: ["Policy", ...bins], rows: policies.map((p) => [labelOf(p), ...bins.map((b) => `${Math.round((data.find((d) => d.policy === p && d.bin === b)?.share ?? 0) * 100)}%`)]) }}
    >
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {policies.map((p) => {
          const rows = bins.map((b) => ({ bin: b, share: data.find((d) => d.policy === p && d.bin === b)?.share ?? 0 }));
          return (
            <div key={p}>
              <p className="mb-1 text-xs font-medium text-ink-2">{labelOf(p)}</p>
              <ResponsiveContainer width="100%" height={120}>
                <BarChart data={rows} margin={{ top: 4, right: 4, bottom: 0, left: -24 }}>
                  <CartesianGrid vertical={false} stroke="var(--grid)" />
                  <XAxis dataKey="bin" {...AXIS} fontSize={10} interval={0} tick={{ fill: "var(--ink-2)", fontSize: 10 }} />
                  <YAxis {...AXIS} domain={[0, 1]} tickFormatter={(v: number) => `${Math.round(v * 100)}%`} width={48} />
                  <Tooltip
                    cursor={{ fill: "var(--surface-2)" }}
                    content={({ active, payload }) =>
                      active && payload?.[0] ? <TooltipBox title={String(payload[0].payload.bin)} rows={[{ label: "Share", value: `${Math.round(Number(payload[0].value) * 100)}%`, color: "var(--accent)" }]} /> : null
                    }
                  />
                  <Bar dataKey="share" fill="var(--accent)" radius={[4, 4, 0, 0]} barSize={16} isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          );
        })}
      </div>
    </ChartFrame>
  );
}

/** Intervention rate by risk level, per policy (ordinal blue ramp for the three levels). */
export function RiskRates({ data, policies, labelOf }: { data: { policy: string; risk_level: string; rate: number; decisions: number }[]; policies: string[]; labelOf: (p: string) => string }) {
  const levels = ["low", "medium", "high"];
  const rows = policies.map((p) => ({
    label: labelOf(p),
    ...Object.fromEntries(levels.map((l) => [l, data.find((d) => d.policy === p && d.risk_level === l)?.rate ?? 0])),
  }));
  return (
    <ChartFrame
      title="How often each policy interrupts, by action risk"
      description="Interruptions ÷ decisions, for low, medium, and high consequence risk."
      legend={levels.map((l, i) => ({ label: `${l} risk`, color: ORDINAL_BLUE[i]! }))}
      table={{ columns: ["Policy", "Low", "Medium", "High"], rows: rows.map((r) => [r.label, ...levels.map((l) => `${Math.round(Number((r as Record<string, unknown>)[l]) * 100)}%`)]) }}
    >
      <ResponsiveContainer width="100%" height={Math.max(150, rows.length * 48 + 30)}>
        <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 4 }} barGap={2}>
          <CartesianGrid horizontal={false} stroke="var(--grid)" />
          <XAxis type="number" domain={[0, 1]} {...AXIS} tickFormatter={(v: number) => `${Math.round(v * 100)}%`} />
          <YAxis type="category" dataKey="label" width={150} {...AXIS} axisLine={false} />
          <Tooltip
            cursor={{ fill: "var(--surface-2)" }}
            content={({ active, payload, label }) =>
              active && payload?.length ? (
                <TooltipBox title={String(label)} rows={payload.map((p) => ({ label: `${p.dataKey} risk`, value: `${Math.round(Number(p.value) * 100)}%`, color: String(p.color) }))} />
              ) : null
            }
          />
          {levels.map((l, i) => (
            <Bar key={l} dataKey={l} fill={ORDINAL_BLUE[i]} radius={[0, 4, 4, 0]} barSize={10} isAnimationActive={false} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

/** A two-series line chart (e.g. a harm-vs-interruption frontier), direct-labelled at the ends. */
export function TwoLines({
  title,
  description,
  series,
  xLabel,
  yLabel,
}: {
  title: string;
  description?: ReactNode;
  series: { name: string; color: string; points: { x: number; y: number; label?: string }[] }[];
  xLabel: string;
  yLabel: string;
}) {
  const xs = series.flatMap((s) => s.points.map((p) => p.x));
  return (
    <ChartFrame
      title={title}
      description={description}
      legend={series.map((s) => ({ label: s.name, color: s.color }))}
      table={{ columns: ["Series", xLabel, yLabel, ""], rows: series.flatMap((s) => s.points.map((p) => [s.name, p.x.toFixed(2), p.y.toFixed(3), p.label ?? ""])) }}
    >
      <ResponsiveContainer width="100%" height={260}>
        <LineChart margin={{ top: 8, right: 24, bottom: 16, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" />
          <XAxis type="number" dataKey="x" domain={[Math.min(...xs, 0), "auto"]} {...AXIS} label={{ value: xLabel, position: "insideBottom", offset: -8, fill: "var(--ink-2)", fontSize: 12 }} />
          <YAxis type="number" dataKey="y" {...AXIS} width={52} label={{ value: yLabel, angle: -90, position: "insideLeft", fill: "var(--ink-2)", fontSize: 12 }} />
          <Tooltip
            content={({ active, payload }) =>
              active && payload?.[0] ? (
                <TooltipBox
                  title={String(payload[0].payload.label ?? "")}
                  rows={[
                    { label: xLabel, value: Number(payload[0].payload.x).toFixed(2) },
                    { label: yLabel, value: Number(payload[0].payload.y).toFixed(3) },
                  ]}
                />
              ) : null
            }
          />
          {series.map((s) => (
            <Line key={s.name} data={s.points} dataKey="y" name={s.name} stroke={s.color} strokeWidth={2} dot={{ r: 4, fill: s.color, stroke: "var(--surface)", strokeWidth: 2 }} isAnimationActive={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

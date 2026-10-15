"use client";

import { BarChart3 } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { DecisionMix, MetricBars, RiskRates, TimingMultiples } from "@/components/charts/charts";
import { Container, PageHeader } from "@/components/layout/page";
import { Select } from "@/components/ui/form";
import { Callout, EmptyState, ErrorState, SimulatedNote } from "@/components/ui/feedback";
import { Badge, ButtonLink, Skeleton } from "@/components/ui/primitives";
import { Stat } from "@/components/ui/stat";
import { api } from "@/lib/api";
import { pct, policyLabel } from "@/lib/format";
import type { Metrics } from "@/lib/types";

import { MetricTable } from "./metric-table";

type Filters = { source: "experiment" | "sessions"; experiment_id: string; scenario: string; policy: string; participant: string; condition: string; risk: string; mode: string };

const KIND_LABEL = { objective: "Objective", ground_truth: "Needs ground truth", simulated: "Simulated proxy" } as const;

export function DashboardClient() {
  const params = useSearchParams();
  const [filters, setFilters] = useState<Filters>({
    source: params.get("source") === "sessions" ? "sessions" : "experiment",
    experiment_id: params.get("experiment") ?? "",
    scenario: "",
    policy: "",
    participant: "",
    condition: "",
    risk: "",
    mode: "",
  });
  // Each request is keyed by its filters (and a retry counter); "loading" is derived by
  // comparing keys, so no state is set synchronously inside the effect.
  const [attempt, setAttempt] = useState(0);
  const requestKey = JSON.stringify([filters, attempt]);
  const [result, setResult] = useState<{ key: string; error: unknown } | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const loading = result?.key !== requestKey;
  const error = loading ? null : result?.error;
  const load = useCallback(() => setAttempt((a) => a + 1), []);

  useEffect(() => {
    let cancelled = false;
    api
      .metrics({
        source: filters.source,
        experiment_id: filters.experiment_id || undefined,
        scenario: filters.scenario || undefined,
        policy: filters.policy || undefined,
        participant: filters.participant || undefined,
        condition: filters.condition || undefined,
        risk: filters.risk || undefined,
        mode: filters.mode || undefined,
      })
      .then((m) => {
        if (cancelled) return;
        setMetrics(m);
        setResult({ key: requestKey, error: null });
      })
      .catch((err: unknown) => {
        if (!cancelled) setResult({ key: requestKey, error: err });
      });
    return () => {
      cancelled = true;
    };
    // requestKey encodes filters and attempt
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestKey]);

  const set = (key: keyof Filters, value: string) => setFilters((f) => ({ ...f, [key]: value, ...(key === "source" ? { experiment_id: "", participant: "", condition: "" } : {}) }));
  const available = metrics?.available ?? {};
  const charts = metrics?.charts;
  const aggregates = useMemo(() => metrics?.aggregates ?? [], [metrics]);
  const bar = (key: string) => aggregates.map((a) => ({ label: policyLabel(a.policy), value: (a[key] as number | null) ?? null, ci: (a[`${key}_ci`] as [number | null, number | null]) ?? null }));
  const totalInterventions = aggregates.reduce((s, a) => s + ((a.interventions as number) || 0) * a.episodes, 0);

  const option = (values: string[] | undefined, all: string, format: (v: string) => string = (v) => v) => [{ value: "", label: all }, ...(values ?? []).map((v) => ({ value: v, label: format(v) }))];

  return (
    <Container className="pt-8">
      <PageHeader
        eyebrow="Research dashboard"
        title="Experiment metrics"
        description="Aggregate metrics with 95% bootstrap confidence intervals. Switch between simulated experiments and interactive sessions (people responding to simulated agents)."
        actions={<ButtonLink href="/experiments" variant="secondary">Run an experiment</ButtonLink>}
      />
      <div className="sticky top-14 z-30 -mx-4 mt-4 flex flex-wrap items-end gap-3 border-b border-line bg-page/95 px-4 py-3 backdrop-blur sm:-mx-6 sm:px-6" role="group" aria-label="Filters">
        <FilterSelect label="Source" value={filters.source} onChange={(v) => set("source", v)} options={[{ value: "experiment", label: "Simulation experiment" }, { value: "sessions", label: "Interactive sessions" }]} />
        {filters.source === "experiment" ? (
          <FilterSelect
            label="Experiment"
            value={filters.experiment_id || String(metrics?.filters.experiment_id ?? "")}
            onChange={(v) => set("experiment_id", v)}
            options={(available.experiments ?? []).map((e) => ({ value: e.id, label: `${e.name} · ${new Date(e.created_at).toLocaleDateString()}` }))}
          />
        ) : (
          <>
            <FilterSelect label="Mode" value={filters.mode} onChange={(v) => set("mode", v)} options={[{ value: "", label: "Demo + study" }, { value: "demo", label: "Demo" }, { value: "study", label: "Study" }]} />
            <FilterSelect label="Participant" value={filters.participant} onChange={(v) => set("participant", v)} options={option(available.participants, "All participants")} />
          </>
        )}
        <FilterSelect label="Scenario" value={filters.scenario} onChange={(v) => set("scenario", v)} options={option(available.scenarios, "All scenarios")} />
        <FilterSelect label="Policy" value={filters.policy} onChange={(v) => set("policy", v)} options={option(available.policies, "All policies", policyLabel)} />
        {filters.source === "experiment" && (available.conditions?.length ?? 0) > 1 ? (
          <FilterSelect label="Condition" value={filters.condition} onChange={(v) => set("condition", v)} options={option(available.conditions, "All conditions")} />
        ) : null}
        <FilterSelect label="Risk level" value={filters.risk} onChange={(v) => set("risk", v)} options={[{ value: "", label: "All" }, { value: "low", label: "Low" }, { value: "medium", label: "Medium" }, { value: "high", label: "High" }]} />
      </div>

      <div className="mt-6 flex flex-col gap-6">
        {error ? <ErrorState error={error} onRetry={load} /> : null}
        {loading && !metrics ? <Skeleton className="h-64" /> : null}
        {metrics && metrics.n_episodes === 0 ? (
          <EmptyState
            icon={<BarChart3 className="size-8" aria-hidden />}
            title={filters.source === "experiment" ? "No experiment results yet" : "No completed interactive sessions yet"}
            action={filters.source === "experiment" ? <ButtonLink href="/experiments">Run an experiment</ButtonLink> : <ButtonLink href="/demo">Open the demo</ButtonLink>}
          >
            {filters.source === "experiment" ? "Run a simulation experiment, or change the filters." : "Finish a demo or study session to see human responses here."}
          </EmptyState>
        ) : null}
        {metrics && metrics.n_episodes > 0 && charts ? (
          <>
            {metrics.source === "experiment" ? <SimulatedNote /> : <Callout title="Interactive sessions">{metrics.note} Small samples, so treat these as exploratory.</Callout>}
            {filters.risk ? <Callout>The risk filter applies to decision-level charts; episode-level metrics (table, top bars) cover whole episodes.</Callout> : null}
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <Stat label="Episodes" value={metrics.n_episodes.toLocaleString()} />
              <Stat label="Policies" value={aggregates.length} />
              <Stat label="Interruptions (total)" value={Math.round(totalInterventions).toLocaleString()} />
              <Stat label="Decisions analysed" value={charts.decisions_by_policy.reduce((s, r) => s + Object.entries(r).reduce((t, [k, v]) => (k === "policy" ? t : t + Number(v)), 0), 0).toLocaleString()} />
            </div>
            <MetricTable rows={aggregates} />
            <div className="grid gap-4 xl:grid-cols-2">
              <MetricBars title="Interruptions per episode" data={bar("interventions")} />
              <MetricBars title="Harm per episode" data={bar("harm")} format={(v) => v.toFixed(3)} />
              <MetricBars title="Missed-intervention rate" data={bar("missed_rate")} format={(v) => pct(v)} max={1} />
              <MetricBars title="Unnecessary-intervention rate" data={bar("unnecessary_rate")} format={(v) => pct(v)} max={1} />
            </div>
            <DecisionMix rows={charts.decisions_by_policy.map((r) => ({ ...r, label: policyLabel(r.policy) }))} />
            <TimingMultiples data={charts.intervention_timing} policies={charts.policies} labelOf={policyLabel} />
            <div className="grid gap-4 xl:grid-cols-2">
              <RiskRates data={charts.risk} policies={charts.policies} labelOf={policyLabel} />
              <MetricBars
                title="Most common reasons for interrupting"
                description="Reason codes on interruptions, all policies."
                data={charts.reasons.slice(0, 10).map((r) => ({ label: r.code.toLowerCase().replace(/_/g, " "), value: r.count }))}
                format={(v) => v.toFixed(0)}
              />
              <MetricBars title="User override rate" description="Responses that changed the proposal (edit, reject, take over, override)." data={bar("override_rate")} format={(v) => pct(v)} max={1} />
              <MetricBars title="Task time (simulated seconds)" data={bar("task_duration_s")} format={(v) => v.toFixed(0)} />
            </div>
            <details className="rounded-xl border border-line bg-surface p-4">
              <summary className="cursor-pointer text-sm font-medium text-ink">Metric definitions</summary>
              <dl className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
                {metrics.metric_definitions.map((m) => (
                  <div key={m.key}>
                    <dt className="flex items-center gap-2 text-sm font-medium text-ink">
                      {m.label} <Badge tone={m.kind === "simulated" ? "warning" : m.kind === "ground_truth" ? "accent" : "neutral"}>{KIND_LABEL[m.kind]}</Badge>
                    </dt>
                    <dd className="text-xs text-ink-2">{m.description}</dd>
                  </div>
                ))}
              </dl>
              <p className="mt-3 text-xs text-ink-3">Formal definitions: research/metrics.md.</p>
            </details>
          </>
        ) : null}
      </div>
    </Container>
  );
}

function FilterSelect({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: { value: string; label: string }[] }) {
  return (
    <label className="flex min-w-36 flex-col gap-1 text-xs font-medium text-ink-2">
      {label}
      <Select value={value} onChange={onChange} options={options} className="h-9" />
    </label>
  );
}

"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { MetricBars } from "@/components/charts/charts";
import { Container, PageHeader } from "@/components/layout/page";
import { EmptyState, ErrorState, SimulatedNote } from "@/components/ui/feedback";
import { Badge, ButtonLink, Skeleton } from "@/components/ui/primitives";
import { Meter } from "@/components/ui/stat";
import { DownloadButton } from "@/components/ui/download";
import { api } from "@/lib/api";
import { pct, policyLabel } from "@/lib/format";
import type { Aggregate, Experiment } from "@/lib/types";

import { statusTone } from "./experiments-client";
import { ComparisonTable, MetricTable } from "./metric-table";

export function ExperimentDetail({ id }: { id: string }) {
  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [error, setError] = useState<unknown>(null);
  const load = useCallback(() => {
    api.experiment(id).then(setExperiment).catch(setError);
  }, [id]);
  useEffect(load, [load]);
  useEffect(() => {
    if (!experiment || experiment.status === "completed" || experiment.status === "failed") return;
    const t = window.setInterval(load, 1000);
    return () => window.clearInterval(t);
  }, [experiment, load]);

  if (error) return <Container className="pt-8"><ErrorState error={error} onRetry={load} /></Container>;
  if (!experiment) return <Container className="pt-8"><Skeleton className="h-64" /></Container>;

  const result = experiment.result;
  const aggregates = (result?.aggregates ?? []) as Aggregate[];
  const conditions = Array.from(new Set(aggregates.map((a) => String(a.condition ?? "default"))));
  const bar = (rows: Aggregate[], key: string) => rows.map((a) => ({ label: policyLabel(a.policy), value: (a[key] as number | null) ?? null, ci: (a[`${key}_ci`] as [number | null, number | null]) ?? null }));

  return (
    <Container className="pt-8">
      <PageHeader
        eyebrow="Experiment"
        title={experiment.name}
        description={
          <span className="flex flex-wrap items-center gap-2">
            <Badge tone={statusTone(experiment.status)}>{experiment.status}</Badge>
            <span>
              {experiment.progress.total.toLocaleString()} episodes · seed {String(experiment.config.seed)} · {experiment.config.episodes} per cell
            </span>
            {result?.result_hash ? <span className="font-mono text-xs">hash {String(result.result_hash).slice(0, 12)}</span> : null}
          </span>
        }
        actions={
          experiment.status === "completed" ? (
            <>
              <DownloadButton path={`/experiments/${experiment.id}/export`} params={{ table: "records", format: "csv" }} filename="agentpause-records.csv">
                Decisions CSV
              </DownloadButton>
              <DownloadButton path={`/experiments/${experiment.id}/export`} params={{ table: "episodes", format: "csv" }} filename="agentpause-episodes.csv">
                Episodes CSV
              </DownloadButton>
              <DownloadButton path={`/experiments/${experiment.id}/export`} params={{ table: "summary" }} filename="agentpause-summary.json" variant="ghost">
                Summary JSON
              </DownloadButton>
              <ButtonLink href={`/dashboard?experiment=${experiment.id}`}>Open in dashboard</ButtonLink>
            </>
          ) : null
        }
      />
      <div className="mt-6 flex flex-col gap-6">
        {experiment.status === "running" || experiment.status === "queued" ? (
          <div>
            <p className="mb-2 text-sm text-ink-2">
              Running: {experiment.progress.done.toLocaleString()} / {experiment.progress.total.toLocaleString()} episodes
            </p>
            <Meter value={experiment.progress.total ? experiment.progress.done / experiment.progress.total : 0} label="Progress" />
          </div>
        ) : null}
        {experiment.error ? <ErrorState error={experiment.error} title="The experiment failed" /> : null}
        {result ? (
          <>
            <SimulatedNote />
            {conditions.map((condition) => {
              const rows = aggregates.filter((a) => String(a.condition ?? "default") === condition);
              const comps = (result.comparisons ?? []).filter((c) => String(c.condition ?? "default") === condition);
              return (
                <section key={condition} className="flex flex-col gap-4" aria-labelledby={`cond-${condition}`}>
                  {conditions.length > 1 ? (
                    <h2 id={`cond-${condition}`} className="text-lg font-semibold text-ink">
                      Condition: {condition.replace(/_/g, " ")}
                    </h2>
                  ) : null}
                  <MetricTable rows={rows} />
                  <div className="grid gap-4 xl:grid-cols-2">
                    <MetricBars title="Interruptions per episode" data={bar(rows, "interventions")} />
                    <MetricBars title="Harm per episode" data={bar(rows, "harm")} format={(v) => v.toFixed(3)} />
                    <MetricBars title="Missed-intervention rate" data={bar(rows, "missed_rate")} format={(v) => pct(v)} max={1} />
                    <MetricBars title="Unnecessary-intervention rate" data={bar(rows, "unnecessary_rate")} format={(v) => pct(v)} max={1} />
                  </div>
                  {comps.length ? <ComparisonTable rows={comps} /> : null}
                </section>
              );
            })}
            <details className="rounded-xl border border-line bg-surface p-4">
              <summary className="cursor-pointer text-sm font-medium text-ink">Configuration (for reproduction)</summary>
              <pre className="mt-3 overflow-auto text-xs text-ink-2">{JSON.stringify(experiment.config, null, 2)}</pre>
            </details>
          </>
        ) : null}
      </div>
    </Container>
  );
}

/** Reads the experiment id from the URL (?id=…). */
export function ExperimentFromQuery() {
  const id = useSearchParams().get("id");
  if (!id) {
    return (
      <Container className="pt-10">
        <EmptyState title="No experiment selected">
          Open one from the <Link href="/experiments" className="font-medium text-accent-strong underline">experiments page</Link>.
        </EmptyState>
      </Container>
    );
  }
  return <ExperimentDetail id={id} />;
}

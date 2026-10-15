"use client";

import { Play } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { MetricBars } from "@/components/charts/charts";
import { Container, PageHeader } from "@/components/layout/page";
import { CheckboxChips, Field, Select, Slider, TextInput } from "@/components/ui/form";
import { EmptyState, ErrorState, SimulatedNote } from "@/components/ui/feedback";
import { Button, Card, CardBody, CardHeader, Skeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { pct, policyLabel } from "@/lib/format";
import { loadPreferences } from "@/lib/preferences";
import type { Aggregate, CompareResult, PolicySpec, ScenarioSummary } from "@/lib/types";

import { ComparisonTable, MetricTable } from "./metric-table";
import { TraceGrid } from "./trace-grid";

const ALL_POLICIES = ["full_autonomy", "always_confirm", "fixed_threshold", "adaptive", "myopic_voi", "rule_based", "confidence_threshold", "user_customized", "learned"];
const DEFAULT_POLICIES = ["full_autonomy", "always_confirm", "fixed_threshold", "adaptive", "myopic_voi", "rule_based"];

function bars(rows: Aggregate[], key: string) {
  return rows.map((r) => ({ label: policyLabel(r.policy), value: (r[key] as number | null) ?? null, ci: (r[`${key}_ci`] as [number | null, number | null] | undefined) ?? null }));
}

export function CompareClient() {
  const params = useSearchParams();
  const [scenarios, setScenarios] = useState<ScenarioSummary[] | null>(null);
  const [scenario, setScenario] = useState(params.get("scenario") || "all");
  const [traceScenario, setTraceScenario] = useState(params.get("scenario") || "travel");
  const [policies, setPolicies] = useState<string[]>(DEFAULT_POLICIES);
  const [episodes, setEpisodes] = useState(30);
  const [seed, setSeed] = useState(params.get("seed") ?? "314159");
  const [vigilance, setVigilance] = useState(0.85);
  const [result, setResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.scenarios().then(setScenarios).catch(setError);
  }, []);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const specs: (PolicySpec | string)[] = policies.map((p) => (p === "user_customized" ? { name: p, preferences: loadPreferences() } : p));
      setResult(
        await api.compare({
          scenarios: scenario === "all" ? ["all"] : [scenario],
          policies: specs,
          episodes,
          seed: Number.parseInt(seed, 10) || 0,
          trace_scenario: scenario === "all" ? traceScenario : scenario,
          user: { approval_vigilance: vigilance },
        }),
      );
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  const nScenarios = scenario === "all" ? (scenarios?.length ?? 6) : 1;
  const total = nScenarios * policies.length * episodes;
  const aggregates = result?.aggregates ?? [];
  const adaptiveComparisons = (result?.comparisons ?? []).filter((c) => c.treatment === "adaptive");

  return (
    <Container className="pt-8">
      <PageHeader
        eyebrow="Policy comparison"
        title="Same tasks, different intervention policies"
        description="Run identical simulated episodes (same seeds, so the same mistakes and the same true intent) under several policies, with a simulated user, and compare interruptions against errors that get through."
      />
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[20rem_minmax(0,1fr)]">
        <Card className="h-fit">
          <CardHeader title="Setup" />
          <CardBody className="flex flex-col gap-4">
            <Field label="Scenario">
              {(id) => (
                <Select
                  id={id}
                  value={scenario}
                  onChange={setScenario}
                  options={[{ value: "all", label: "All six scenarios" }, ...(scenarios ?? []).map((s) => ({ value: s.id, label: s.name }))]}
                />
              )}
            </Field>
            {scenario === "all" ? (
              <Field label="Example trace scenario">
                {(id) => <Select id={id} value={traceScenario} onChange={setTraceScenario} options={(scenarios ?? []).map((s) => ({ value: s.id, label: s.name }))} />}
              </Field>
            ) : null}
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium text-ink">Policies</span>
              <CheckboxChips ariaLabel="Policies" values={policies} onChange={setPolicies} options={ALL_POLICIES.map((p) => ({ value: p, label: policyLabel(p) }))} />
            </div>
            <Slider label="Episodes per scenario" value={episodes} onChange={(v) => setEpisodes(Math.round(v))} min={5} max={100} step={5} format={(v) => String(v)} />
            <Field label="Seed">{(id) => <TextInput id={id} value={seed} onChange={(v) => setSeed(v.replace(/\D/g, ""))} />}</Field>
            <Slider
              label="Simulated user vigilance"
              value={vigilance}
              onChange={setVigilance}
              min={0.3}
              max={1}
              format={(v) => pct(v)}
              hint="Chance the simulated user spots a visible mistake when asked (before habituation)."
            />
            <Button onClick={run} loading={loading} disabled={!policies.length || total > 3000} icon={<Play className="size-4" aria-hidden />}>
              Run {total.toLocaleString()} episodes
            </Button>
            {total > 3000 ? <p className="text-xs text-critical">At most 3,000 episodes here. Use the Experiments page for larger runs.</p> : null}
          </CardBody>
        </Card>
        <div className="flex min-w-0 flex-col gap-5">
          {error ? <ErrorState error={error} onRetry={run} /> : null}
          {loading && !result ? (
            <div className="grid gap-4">
              <Skeleton className="h-40" />
              <Skeleton className="h-64" />
            </div>
          ) : null}
          {!result && !loading && !error ? (
            <EmptyState title="Choose policies and run the comparison">A run with the defaults takes a few seconds.</EmptyState>
          ) : null}
          {result ? (
            <>
              <SimulatedNote>
                {result.episodes} episodes per scenario and policy, seed {result.seed}. Simulated users, scripted ground truth. Not evaluated with human
                participants.
              </SimulatedNote>
              {Object.keys(result.traces).length ? (
                <TraceGrid traces={Object.entries(result.traces).map(([policy, t]) => ({ policy, ...t }))} labelOf={policyLabel} />
              ) : null}
              <div className="grid gap-4 xl:grid-cols-2">
                <MetricBars title="Interruptions per episode" data={bars(aggregates, "interventions")} />
                <MetricBars title="Harm per episode" description="Sum of error costs that got through (1 = worst outcome)." data={bars(aggregates, "harm")} format={(v) => v.toFixed(3)} />
                <MetricBars title="Missed-intervention rate" description="Errors that caused harm without ever being shown to the user." data={bars(aggregates, "missed_rate")} format={(v) => pct(v)} max={1} />
                <MetricBars title="Unnecessary-intervention rate" description="Interruptions when no error was present." data={bars(aggregates, "unnecessary_rate")} format={(v) => pct(v)} max={1} />
              </div>
              <MetricTable rows={aggregates} />
              {adaptiveComparisons.length ? <ComparisonTable rows={adaptiveComparisons} /> : null}
            </>
          ) : null}
        </div>
      </div>
    </Container>
  );
}

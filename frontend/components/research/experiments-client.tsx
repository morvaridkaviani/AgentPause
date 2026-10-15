"use client";

import { FlaskConical, Play, Trash2 } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Container, PageHeader } from "@/components/layout/page";
import { CheckboxChips, Field, Slider, TextInput, Toggle } from "@/components/ui/form";
import { Callout, EmptyState, ErrorState } from "@/components/ui/feedback";
import { Badge, Button, Card, CardBody, CardHeader, Skeleton } from "@/components/ui/primitives";
import { Meter } from "@/components/ui/stat";
import { api } from "@/lib/api";
import { policyLabel } from "@/lib/format";
import type { Experiment, ScenarioSummary } from "@/lib/types";

const POLICIES = ["full_autonomy", "always_confirm", "fixed_threshold", "adaptive", "myopic_voi", "rule_based", "confidence_threshold", "user_customized", "learned"];

const CONDITIONS = [
  { id: "default", label: "Default world", spec: { name: "default" } },
  { id: "uncalibrated", label: "Uncalibrated agent", spec: { name: "uncalibrated_agent", engine: { calibration: 0, propagated_calibration: 0 } } },
  { id: "fast_habituation", label: "Fast-habituating user", spec: { name: "fast_habituating_user", user: { habituation_rate: 0.35 } } },
  { id: "careless", label: "Careless user", spec: { name: "careless_user", user: { approval_vigilance: 0.6, clarification_accuracy: 0.8 } } },
];

export function statusTone(status: Experiment["status"]) {
  return status === "completed" ? "good" : status === "failed" ? "critical" : status === "running" ? "accent" : "neutral";
}

export function ExperimentsClient() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [experiments, setExperiments] = useState<Experiment[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [submitError, setSubmitError] = useState<unknown>(null);
  const [name, setName] = useState("my-comparison");
  const [selectedScenarios, setSelectedScenarios] = useState<string[]>([]);
  const [policies, setPolicies] = useState<string[]>(["full_autonomy", "always_confirm", "fixed_threshold", "adaptive"]);
  const [conditions, setConditions] = useState<string[]>(["default"]);
  const [episodes, setEpisodes] = useState(50);
  const [seed, setSeed] = useState("314159");
  const [bootstrap, setBootstrap] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const refresh = useCallback(() => {
    api.experiments().then(setExperiments).catch(setError);
  }, []);
  useEffect(() => {
    refresh();
    api.scenarios().then((s) => {
      setScenarios(s);
      setSelectedScenarios(s.map((x) => x.id));
    }).catch(setError);
  }, [refresh]);
  useEffect(() => {
    if (!experiments?.some((e) => e.status === "running" || e.status === "queued")) return;
    const t = window.setInterval(refresh, 1000);
    return () => window.clearInterval(t);
  }, [experiments, refresh]);

  const total = selectedScenarios.length * policies.length * conditions.length * episodes;
  const submit = async () => {
    setSubmitting(true);
    setSubmitError(null);
    try {
      await api.createExperiment({
        name,
        scenarios: selectedScenarios.length === scenarios.length ? ["all"] : selectedScenarios,
        policies,
        episodes,
        seed: Number.parseInt(seed, 10) || 0,
        conditions: CONDITIONS.filter((c) => conditions.includes(c.id)).map((c) => c.spec),
        bootstrap: bootstrap ? 300 : 0,
      });
      refresh();
    } catch (err) {
      setSubmitError(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Container className="pt-8">
      <PageHeader
        eyebrow="Experiment runner"
        title="Configure and run simulation experiments"
        description="Every episode is deterministic given its seed. Policies face identical injected mistakes (common random numbers), so comparisons are paired. For publication-scale runs, use the scripts in experiments/."
      />
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[24rem_minmax(0,1fr)]">
        <Card className="h-fit">
          <CardHeader title="New experiment" />
          <CardBody className="flex flex-col gap-4">
            <Field label="Name">{(id) => <TextInput id={id} value={name} onChange={setName} />}</Field>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium text-ink">Scenarios</span>
              <CheckboxChips ariaLabel="Scenarios" values={selectedScenarios} onChange={setSelectedScenarios} options={scenarios.map((s) => ({ value: s.id, label: s.name }))} />
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium text-ink">Policies (conditions)</span>
              <CheckboxChips ariaLabel="Policies" values={policies} onChange={setPolicies} options={POLICIES.map((p) => ({ value: p, label: policyLabel(p) }))} />
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium text-ink">Simulated world</span>
              <CheckboxChips ariaLabel="Simulated world conditions" values={conditions} onChange={setConditions} options={CONDITIONS.map((c) => ({ value: c.id, label: c.label }))} />
            </div>
            <Slider label="Episodes (simulated participants) per cell" value={episodes} onChange={(v) => setEpisodes(Math.round(v))} min={10} max={500} step={10} format={(v) => String(v)} />
            <Field label="Seed" hint="Use a fresh seed for confirmatory runs; record it.">
              {(id) => <TextInput id={id} value={seed} onChange={(v) => setSeed(v.replace(/\D/g, ""))} />}
            </Field>
            <Toggle label="Bootstrap confidence intervals" checked={bootstrap} onChange={setBootstrap} />
            <Callout>
              Randomization: episode order does not affect results (each episode&apos;s randomness derives from its own seed).
            </Callout>
            <Button onClick={submit} loading={submitting} disabled={!policies.length || !selectedScenarios.length || !conditions.length || total > 20000} icon={<Play className="size-4" aria-hidden />}>
              Run {total.toLocaleString()} episodes
            </Button>
            {total > 20000 ? <p className="text-xs text-critical">The web runner allows at most 20,000 episodes per experiment.</p> : null}
            {submitError ? <ErrorState error={submitError} /> : null}
          </CardBody>
        </Card>
        <section aria-labelledby="runs-title" className="flex min-w-0 flex-col gap-3">
          <h2 id="runs-title" className="text-sm font-semibold text-ink">
            Experiments
          </h2>
          {error ? <ErrorState error={error} onRetry={refresh} /> : null}
          {!experiments && !error ? <Skeleton className="h-32" /> : null}
          {experiments && experiments.length === 0 ? (
            <EmptyState icon={<FlaskConical className="size-8" aria-hidden />} title="No experiments yet">
              Configure one on the left. Results appear here and on the dashboard.
            </EmptyState>
          ) : null}
          <ul className="flex flex-col gap-2">
            {experiments?.map((e) => (
              <li key={e.id} className="rounded-xl border border-line bg-surface px-4 py-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="min-w-0">
                    <Link href={`/experiments/${e.id}`} className="font-medium text-ink hover:text-accent-strong hover:underline">
                      {e.name}
                    </Link>
                    <p className="text-xs text-ink-3">
                      {new Date(e.created_at).toLocaleString()} · {e.progress.total.toLocaleString()} episodes · seed {String(e.config.seed)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge tone={statusTone(e.status)}>{e.status}</Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      aria-label={`Delete ${e.name}`}
                      onClick={async () => {
                        try {
                          await api.deleteExperiment(e.id);
                          refresh();
                        } catch (err) {
                          setError(err);
                        }
                      }}
                      icon={<Trash2 className="size-4" aria-hidden />}
                    />
                  </div>
                </div>
                {e.status === "running" || e.status === "queued" ? (
                  <Meter value={e.progress.total ? e.progress.done / e.progress.total : 0} label={`${e.name} progress`} className="mt-2" />
                ) : null}
                {e.error ? <p className="mt-2 text-xs text-critical">{e.error.split("\n")[0]}</p> : null}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </Container>
  );
}

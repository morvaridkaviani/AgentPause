"use client";

import clsx from "clsx";
import { Check, ChevronRight, Eye, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { MetricBars } from "@/components/charts/charts";
import { Container, PageHeader } from "@/components/layout/page";
import { CheckboxChips, Field, Select, Slider, Toggle } from "@/components/ui/form";
import { Callout, ErrorState, SimulatedNote } from "@/components/ui/feedback";
import { Button, ButtonLink, Card, CardBody, CardHeader } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { CATEGORY_LABEL, pct, policyLabel } from "@/lib/format";
import { DEFAULT_PREFERENCES, PROFILES, describePreferences, usePreferences } from "@/lib/preferences";
import type { CompareResult, Preferences, ScenarioSummary } from "@/lib/types";

import { TraceGrid } from "./trace-grid";

const CATEGORIES = Object.entries(CATEGORY_LABEL).map(([value, label]) => ({ value, label }));

export function PreferencesClient() {
  const [prefs, storePrefs] = usePreferences();
  const [saved, setSaved] = useState(false);
  const savedTimer = useRef<number | undefined>(undefined);
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [scenario, setScenario] = useState("email");
  const [preview, setPreview] = useState<CompareResult | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.scenarios().then(setScenarios).catch(() => undefined);
  }, []);
  useEffect(() => () => window.clearTimeout(savedTimer.current), []);

  const setPrefs = (next: Preferences) => {
    storePrefs(next);
    setSaved(true);
    window.clearTimeout(savedTimer.current);
    savedTimer.current = window.setTimeout(() => setSaved(false), 1500);
  };
  const set = <K extends keyof Preferences>(key: K, value: Preferences[K]) => setPrefs({ ...prefs, [key]: value });

  const runPreview = async () => {
    setLoading(true);
    setError(null);
    try {
      setPreview(
        await api.compare({
          scenarios: [scenario],
          policies: ["adaptive", { name: "user_customized", preferences: prefs }],
          episodes: 30,
          seed: 314159,
          trace_scenario: scenario,
        }),
      );
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container className="pt-8">
      <PageHeader
        eyebrow="My preferences"
        title="How often should the assistant ask you?"
        description="Choose a style, and add rules if you like. Your choices are saved in this browser only. To use them, pick “My preferences” in the demo."
        actions={
          <>
            <span aria-live="polite" className={clsx("inline-flex items-center gap-1 self-center text-sm text-good-ink transition-opacity", saved ? "opacity-100" : "opacity-0")}>
              <Check className="size-4" aria-hidden /> Saved
            </span>
            <Button variant="ghost" onClick={() => setPrefs(DEFAULT_PREFERENCES)} icon={<RotateCcw className="size-4" aria-hidden />}>
              Reset
            </Button>
            <ButtonLink href="/demo?policy=user_customized">Try them in the demo</ButtonLink>
          </>
        }
      />
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="flex flex-col gap-6">
          <section aria-labelledby="profile-title">
            <h2 id="profile-title" className="mb-3 text-base font-semibold text-ink">
              1. Choose a style
            </h2>
            <div role="radiogroup" aria-labelledby="profile-title" className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {PROFILES.map((p) => {
                const selected = prefs.profile === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    onClick={() => set("profile", p.id)}
                    title={`Interruption cost ${p.multiplier}`}
                    className={clsx("rounded-xl border bg-surface p-4 text-left", selected ? "border-accent ring-1 ring-accent" : "border-line hover:border-line-strong")}
                  >
                    <p className="flex flex-wrap items-center gap-1.5 font-medium text-ink">
                      {p.title}
                      {p.id === "balanced" ? <span className="text-xs font-normal text-accent-strong">recommended</span> : null}
                    </p>
                    <p className="mt-1 text-sm text-ink-2">{p.description}</p>
                  </button>
                );
              })}
            </div>
          </section>
          <Card>
            <CardHeader title="2. Rules (optional)" description="Your rules always win over the assistant's own judgement." />
            <CardBody className="flex flex-col gap-4">
              <Toggle label="Ask me before external communication" checked={prefs.ask_before_external} onChange={(v) => set("ask_before_external", v)} description="Emails, messages, invitations, posts." />
              <Toggle label="Ask me before irreversible actions" checked={prefs.ask_before_irreversible} onChange={(v) => set("ask_before_irreversible", v)} description="Anything that is hard to undo." />
              <Toggle label="Allow low-risk actions without asking" checked={prefs.allow_low_risk_autonomy} onChange={(v) => set("allow_low_risk_autonomy", v)} description="Never interrupt you for small, low-risk actions." />
              {prefs.allow_low_risk_autonomy ? (
                <Slider label="What counts as low-risk (lower = stricter)" value={prefs.low_risk_threshold} onChange={(v) => set("low_risk_threshold", v)} min={0.05} max={0.5} format={(v) => v.toFixed(2)} />
              ) : null}
              <Toggle
                label="Limit interruptions per task"
                checked={prefs.max_interruptions_per_task !== null}
                onChange={(v) => set("max_interruptions_per_task", v ? 3 : null)}
                description="After this many questions, the assistant carries on by itself (your rules above still apply)."
              />
              {prefs.max_interruptions_per_task !== null ? (
                <Slider label="Maximum questions per task" value={prefs.max_interruptions_per_task} onChange={(v) => set("max_interruptions_per_task", Math.round(v))} min={0} max={10} step={1} format={(v) => String(v)} />
              ) : null}
            </CardBody>
          </Card>
          <details className="group rounded-xl border border-line bg-surface">
            <summary className="flex cursor-pointer list-none items-center gap-2 px-5 py-4 text-sm font-semibold text-ink">
              <ChevronRight className="size-4 text-ink-2 transition-transform group-open:rotate-90" aria-hidden />
              3. Fine-tune by type of action (optional)
            </summary>
            <div className="flex flex-col gap-5 border-t border-line px-5 py-4">
              <div className="flex flex-col gap-2">
                <p className="text-sm font-medium text-ink">Always ask me</p>
                <CheckboxChips ariaLabel="Always ask categories" values={prefs.always_ask_categories} onChange={(v) => set("always_ask_categories", v)} options={CATEGORIES} />
              </div>
              <div className="flex flex-col gap-2">
                <p className="text-sm font-medium text-ink">Never ask me</p>
                <CheckboxChips ariaLabel="Never ask categories" values={prefs.never_ask_categories} onChange={(v) => set("never_ask_categories", v)} options={CATEGORIES} />
              </div>
              <div className="flex flex-col gap-2">
                <p className="text-sm font-medium text-ink">Never allow (block)</p>
                <CheckboxChips ariaLabel="Blocked categories" values={prefs.block_categories} onChange={(v) => set("block_categories", v)} options={CATEGORIES} />
              </div>
            </div>
          </details>
        </div>
        <div className="flex flex-col gap-4">
          <Card>
            <CardHeader title="Your choices" />
            <CardBody>
              <ul className="list-disc pl-5 text-sm text-ink">
                {describePreferences(prefs).map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </CardBody>
          </Card>
          <Callout title="A caution from prior work">
            In a study with 113 people, user-written permission rules reduced prompts but caught less agent overreach, and most rules people
            wrote were &ldquo;ask&rdquo; (Yan 2026). Preferences are a research variable here, not a guaranteed improvement.
          </Callout>
          <Card>
            <CardHeader title="See the difference" description="Runs the assistant with and without your preferences on the same simulated tasks." />
            <CardBody className="flex flex-col gap-4">
              <div className="flex flex-wrap items-end gap-3">
                <Field label="Task" className="min-w-48 flex-1">
                  {(id) => <Select id={id} value={scenario} onChange={setScenario} options={scenarios.map((s) => ({ value: s.id, label: s.name }))} />}
                </Field>
                <Button onClick={runPreview} loading={loading} icon={<Eye className="size-4" aria-hidden />}>
                  Preview
                </Button>
              </div>
              {error ? <ErrorState error={error} /> : null}
              {preview ? (
                <>
                  <SimulatedNote />
                  <TraceGrid traces={Object.entries(preview.traces).map(([policy, t]) => ({ policy, ...t }))} labelOf={policyLabel} />
                  <MetricBars title="Interruptions per episode (30 episodes)" data={preview.aggregates.map((a) => ({ label: policyLabel(a.policy), value: a.interventions as number }))} />
                  <MetricBars title="Missed-intervention rate" data={preview.aggregates.map((a) => ({ label: policyLabel(a.policy), value: (a.missed_rate as number | null) ?? null }))} format={(v) => pct(v)} max={1} />
                </>
              ) : null}
            </CardBody>
          </Card>
        </div>
      </div>
    </Container>
  );
}

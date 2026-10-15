"use client";

import { Save } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { TokenPrompt } from "@/components/research/token-gate";
import { Container, PageHeader } from "@/components/layout/page";
import { CheckboxChips, Field, Select, TextInput } from "@/components/ui/form";
import { Callout, ErrorState } from "@/components/ui/feedback";
import { Badge, Button, ButtonLink, Card, CardBody, CardHeader, Spinner } from "@/components/ui/primitives";
import { DownloadButton } from "@/components/ui/download";
import { api } from "@/lib/api";
import { policyLabel } from "@/lib/format";
import type { ExplanationMode, Instrument, PolicyInfo, ScenarioSummary, StudyConfig } from "@/lib/types";

const MODES: { value: ExplanationMode; label: string }[] = [
  { value: "none", label: "No explanation" },
  { value: "placebo", label: "Placebic reason" },
  { value: "factors", label: "Factors only" },
  { value: "full", label: "Factors + timing" },
];

export function StudyAdmin() {
  const [config, setConfig] = useState<StudyConfig | null>(null);
  const [policies, setPolicies] = useState<PolicyInfo[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const load = useCallback(() => {
    Promise.all([api.studyConfig(), api.policies(), api.scenarios(), api.instruments()])
      .then(([c, p, s, i]) => {
        setConfig(c);
        setPolicies(p);
        setScenarios(s);
        setInstruments(i);
      })
      .catch(setError);
  }, []);
  useEffect(load, [load]);

  const save = async () => {
    if (!config) return;
    setSaving(true);
    setError(null);
    try {
      setConfig(await api.updateStudyConfig(config));
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      setError(err);
    } finally {
      setSaving(false);
    }
  };

  if (!config) return <Container className="pt-10">{error ? <ErrorState error={error} onRetry={load} /> : <Spinner />}</Container>;
  const set = <K extends keyof StudyConfig>(key: K, value: StudyConfig[K]) => setConfig({ ...config, [key]: value });
  const post = instruments.filter((i) => i.when === "post_task");
  const finals = instruments.filter((i) => i.when === "final");

  return (
    <Container className="pt-8">
      <PageHeader
        eyebrow="Study administration"
        title="Configure the user study"
        description="Within-subjects policy conditions (balanced Latin square), between-subjects explanation conditions (round-robin), rotating scenarios. Participants are identified only by random codes."
        actions={
          <Button onClick={save} loading={saving} icon={<Save className="size-4" aria-hidden />}>
            {saved ? "Saved" : "Save configuration"}
          </Button>
        }
      />
      <div className="mt-4 flex flex-col gap-4">
        <TokenPrompt error={error} onSaved={save} />
        {error ? <ErrorState error={error} /> : null}
        <Callout tone="warning" title="Before collecting real data">
          Obtain ethics approval, set <code>AGENTPAUSE_ADMIN_TOKEN</code> on the server so that exports and configuration are protected, pre-register
          your hypotheses and measures, and pilot the protocol.
        </Callout>
      </div>
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Design" />
          <CardBody className="flex flex-col gap-4">
            <Field label="Study title">{(id) => <TextInput id={id} value={config.title} onChange={(v) => set("title", v)} />}</Field>
            <Field label="Consent text" hint="Shown before enrolment. Adapt it to your ethics approval.">
              {(id) => (
                <textarea id={id} value={config.consent_text} onChange={(e) => set("consent_text", e.target.value)} rows={6} className="w-full rounded-lg border border-line-strong bg-surface p-3 text-sm text-ink" />
              )}
            </Field>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium text-ink">Policy conditions (within-subjects)</span>
              <CheckboxChips ariaLabel="Policy conditions" values={config.conditions} onChange={(v) => set("conditions", v)} options={policies.map((p) => ({ value: p.name, label: policyLabel(p.name) }))} />
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium text-ink">Scenarios (rotated across blocks)</span>
              <CheckboxChips ariaLabel="Scenarios" values={config.scenarios} onChange={(v) => set("scenarios", v)} options={scenarios.map((s) => ({ value: s.id, label: s.name }))} />
            </div>
            <Field label="Practice scenario">
              {(id) => (
                <Select
                  id={id}
                  value={config.practice_scenario ?? ""}
                  onChange={(v) => set("practice_scenario", v || null)}
                  options={[{ value: "", label: "No practice block" }, ...scenarios.map((s) => ({ value: s.id, label: s.name }))]}
                />
              )}
            </Field>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium text-ink">Explanation conditions (between-subjects)</span>
              <CheckboxChips ariaLabel="Explanation conditions" values={config.explanation_modes} onChange={(v) => set("explanation_modes", v)} options={MODES} />
            </div>
          </CardBody>
        </Card>
        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader title="Questionnaires" description="Only instruments with item text available (bundled or supplied locally) can be used." />
            <CardBody className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <span className="text-sm font-medium text-ink">After each task</span>
                <CheckboxChips ariaLabel="Post-task instruments" values={config.post_task_instruments} onChange={(v) => set("post_task_instruments", v)} options={post.map((i) => ({ value: i.id, label: i.name }))} />
              </div>
              <div className="flex flex-col gap-1.5">
                <span className="text-sm font-medium text-ink">At the end</span>
                <CheckboxChips ariaLabel="Final instruments" values={config.final_instruments} onChange={(v) => set("final_instruments", v)} options={finals.map((i) => ({ value: i.id, label: i.name }))} />
              </div>
              <ul className="flex flex-col divide-y divide-line rounded-lg border border-line">
                {instruments.map((i) => (
                  <li key={i.id} className="px-3 py-2 text-sm">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium text-ink">{i.name}</span>
                      <Badge tone={i.ready ? "good" : "warning"}>{i.ready ? `items ${i.items_source}` : "items missing"}</Badge>
                      <Badge tone={i.validated ? "neutral" : "warning"}>{i.validated ? "validated scale" : "not validated"}</Badge>
                    </div>
                    <p className="mt-0.5 text-xs [overflow-wrap:anywhere] text-ink-2">{i.license}</p>
                    {i.source_url ? (
                      <a href={i.source_url} className="text-xs text-accent-strong hover:underline" rel="noreferrer">
                        Source
                      </a>
                    ) : null}
                  </li>
                ))}
              </ul>
              <p className="text-xs text-ink-3">
                To use a licensed instrument whose text is not bundled (e.g. SUS), put its items in <code>$INSTRUMENTS_LOCAL_DIR/&lt;id&gt;.json</code> on the
                server. See docs/experiments.md.
              </p>
            </CardBody>
          </Card>
          <Card>
            <CardHeader title="Data" />
            <CardBody className="flex flex-wrap gap-2">
              <DownloadButton path="/study/export" params={{ format: "csv" }} filename="agentpause-questionnaires.csv">
                Questionnaires CSV
              </DownloadButton>
              <DownloadButton path="/study/export" params={{ format: "json" }} filename="agentpause-questionnaires.json">
                Questionnaires JSON
              </DownloadButton>
              <DownloadButton path="/events" params={{ mode: "study", format: "csv" }} filename="agentpause-study-events.csv">
                Study events CSV
              </DownloadButton>
              <ButtonLink href="/dashboard?source=sessions" variant="ghost">
                Study sessions on the dashboard
              </ButtonLink>
            </CardBody>
          </Card>
        </div>
      </div>
    </Container>
  );
}

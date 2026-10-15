"use client";

import { RotateCcw } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { DecisionExplanation } from "@/components/decision/explanation";
import { Container, PageHeader } from "@/components/layout/page";
import { Field, Segmented, Select, Slider, Toggle } from "@/components/ui/form";
import { ErrorState } from "@/components/ui/feedback";
import { Badge, Button, Card, CardBody, CardHeader, Spinner } from "@/components/ui/primitives";
import { api, type ActionContextInput } from "@/lib/api";
import { CATEGORY_LABEL, pct, policyLabel } from "@/lib/format";
import { DEFAULT_PREFERENCES as DEFAULT_PREFS } from "@/lib/preferences";
import type { Decision, Preferences } from "@/lib/types";

interface LabState {
  action: string;
  description: string;
  consequence: string;
  agent_confidence: number;
  intent_confidence: number;
  severity: number;
  recoverability: number;
  cognitive_load: number;
  at_breakpoint: "yes" | "no" | "unknown";
  external_effects: "yes" | "no" | "default";
  recent_interruptions: number;
  policy: string;
  profile: Preferences["profile"];
  useSeverity: boolean;
  useRecoverability: boolean;
}

const PRESETS: { id: string; label: string; state: Partial<LabState> }[] = [
  {
    id: "email",
    label: "Send an email (the example from the brief)",
    state: { action: "send_email", description: "Send the drafted email to Professor Smith", consequence: "external_communication", agent_confidence: 0.86, intent_confidence: 0.72, useSeverity: false, useRecoverability: true, recoverability: 0.02, at_breakpoint: "unknown", cognitive_load: 0.3 },
  },
  {
    id: "search",
    label: "Search flights",
    state: { action: "search_flights", description: "Search flights Berlin → Vienna", consequence: "read_only", agent_confidence: 0.95, intent_confidence: 0.9, useSeverity: false, useRecoverability: false, at_breakpoint: "yes" },
  },
  {
    id: "purchase",
    label: "Buy a non-refundable ticket",
    state: { action: "purchase_ticket", description: "Purchase the €212 flight", consequence: "financial_transaction", agent_confidence: 0.9, intent_confidence: 0.97, useSeverity: true, severity: 0.8, useRecoverability: true, recoverability: 0.05, at_breakpoint: "no" },
  },
  {
    id: "delete",
    label: "Permanently delete files (agent unsure)",
    state: { action: "empty_trash", description: "Empty the Trash (9.8 GB)", consequence: "data_deletion", agent_confidence: 0.3, intent_confidence: 0.9, useSeverity: true, severity: 0.95, useRecoverability: true, recoverability: 0.0, at_breakpoint: "no" },
  },
];

const INITIAL: LabState = {
  action: "send_email",
  description: "Send the drafted email to Professor Smith",
  consequence: "external_communication",
  agent_confidence: 0.86,
  intent_confidence: 0.72,
  severity: 0.45,
  recoverability: 0.02,
  cognitive_load: 0.3,
  at_breakpoint: "unknown",
  external_effects: "default",
  recent_interruptions: 0,
  policy: "adaptive",
  profile: "balanced",
  useSeverity: false,
  useRecoverability: true,
};

const LAB_POLICIES = ["adaptive", "myopic_voi", "fixed_threshold", "confidence_threshold", "rule_based", "always_confirm", "full_autonomy", "learned"];

export function LabClient() {
  const [state, setState] = useState<LabState>(INITIAL);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const requestId = useRef(0);
  const set = <K extends keyof LabState>(key: K, value: LabState[K]) => setState((s) => ({ ...s, [key]: value }));

  const context: ActionContextInput = useMemo(() => {
    const c: ActionContextInput = {
      action: state.action,
      description: state.description,
      consequence: state.consequence,
      agent_confidence: state.agent_confidence,
      intent_confidence: state.intent_confidence,
      cognitive_load: state.cognitive_load,
      step: state.recent_interruptions,
    };
    if (state.useSeverity) c.severity = state.severity;
    if (state.useRecoverability) c.recoverability = state.recoverability;
    if (state.at_breakpoint !== "unknown") c.at_breakpoint = state.at_breakpoint === "yes";
    if (state.external_effects !== "default") c.external_effects = state.external_effects === "yes";
    return c;
  }, [state]);

  useEffect(() => {
    const id = ++requestId.current;
    const timer = window.setTimeout(() => {
      setLoading(true);
      const history = state.recent_interruptions
        ? { step: state.recent_interruptions, interruption_steps: Array.from({ length: state.recent_interruptions }, (_, i) => i) }
        : null;
      api
        .evaluate(context, state.policy, { preferences: state.profile === "balanced" ? null : { ...DEFAULT_PREFS, profile: state.profile }, state: history })
        .then((d) => {
          if (id === requestId.current) {
            setDecision(d);
            setError(null);
          }
        })
        .catch((err) => id === requestId.current && setError(err))
        .finally(() => id === requestId.current && setLoading(false));
    }, 200);
    return () => window.clearTimeout(timer);
  }, [context, state.policy, state.profile, state.recent_interruptions]);

  return (
    <Container className="pt-8">
      <PageHeader
        eyebrow="Decision lab"
        title="Move the signals, watch the decision"
        description="Describe one proposed action and see exactly how each policy would decide, and why. Every term of the adaptive model is shown, and every value is tagged with where it came from."
        actions={
          <Button variant="ghost" onClick={() => setState(INITIAL)} icon={<RotateCcw className="size-4" aria-hidden />}>
            Reset
          </Button>
        }
      />
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,24rem)_minmax(0,1fr)]">
        <Card className="h-fit">
          <CardHeader title="The proposed action" />
          <CardBody className="flex flex-col gap-4">
            <Field label="Preset">
              {(id) => (
                <Select
                  id={id}
                  value=""
                  onChange={(v) => {
                    const preset = PRESETS.find((p) => p.id === v);
                    if (preset) setState((s) => ({ ...s, ...preset.state }));
                  }}
                  options={[{ value: "", label: "Choose an example…" }, ...PRESETS.map((p) => ({ value: p.id, label: p.label }))]}
                />
              )}
            </Field>
            <Field label="Consequence category">
              {(id) => (
                <Select id={id} value={state.consequence} onChange={(v) => set("consequence", v)} options={Object.entries(CATEGORY_LABEL).map(([value, label]) => ({ value, label }))} />
              )}
            </Field>
            <Slider label="Agent confidence" value={state.agent_confidence} onChange={(v) => set("agent_confidence", v)} format={(v) => pct(v)} tag={<Badge>agent-reported</Badge>} />
            <Slider label="Intent clarity" value={state.intent_confidence} onChange={(v) => set("intent_confidence", v)} format={(v) => pct(v)} hint="How sure the agent is that this matches what you meant." tag={<Badge>agent-reported</Badge>} />
            <div className="flex flex-col gap-2 rounded-lg border border-line p-3">
              <Toggle label="Override severity" checked={state.useSeverity} onChange={(v) => set("useSeverity", v)} description="Off = use the category's documented prior." />
              {state.useSeverity ? <Slider label="Severity" value={state.severity} onChange={(v) => set("severity", v)} /> : null}
            </div>
            <div className="flex flex-col gap-2 rounded-lg border border-line p-3">
              <Toggle label="Override reversibility" checked={state.useRecoverability} onChange={(v) => set("useRecoverability", v)} description="1 = trivially undone, 0 = cannot be undone." />
              {state.useRecoverability ? <Slider label="Recoverability" value={state.recoverability} onChange={(v) => set("recoverability", v)} /> : null}
            </div>
            <Slider label="Your current load" value={state.cognitive_load} onChange={(v) => set("cognitive_load", v)} format={(v) => pct(v)} tag={<Badge>estimated</Badge>} />
            <Field label="At a natural breakpoint?">
              {() => (
                <Segmented
                  ariaLabel="At a natural breakpoint"
                  value={state.at_breakpoint}
                  onChange={(v) => set("at_breakpoint", v)}
                  options={[
                    { value: "yes", label: "Yes" },
                    { value: "no", label: "Mid-task" },
                    { value: "unknown", label: "Unknown" },
                  ]}
                />
              )}
            </Field>
            <Slider label="Recent interruptions" value={state.recent_interruptions} onChange={(v) => set("recent_interruptions", Math.round(v))} min={0} max={8} step={1} format={(v) => String(v)} hint="Repeated prompts get rubber-stamped, so asking is worth less." />
          </CardBody>
        </Card>
        <div className="flex flex-col gap-4">
          <Card>
            <CardHeader
              title="Decision"
              description={policyLabel(state.policy)}
              action={loading ? <Spinner label="Evaluating" /> : null}
            />
            <CardBody className="flex flex-col gap-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Policy">
                  {(id) => <Select id={id} value={state.policy} onChange={(v) => set("policy", v)} options={LAB_POLICIES.map((p) => ({ value: p, label: policyLabel(p) }))} />}
                </Field>
                <Field label="Your interruption preference">
                  {(id) => (
                    <Select
                      id={id}
                      value={state.profile}
                      onChange={(v) => set("profile", v)}
                      options={[
                        { value: "fewer_interruptions", label: "Prefer fewer interruptions" },
                        { value: "balanced", label: "Balanced" },
                        { value: "maximum_control", label: "Maximum control" },
                      ]}
                    />
                  )}
                </Field>
              </div>
              {error ? <ErrorState error={error} /> : null}
              {decision ? <DecisionExplanation decision={decision} /> : null}
            </CardBody>
          </Card>
          {decision ? (
            <details className="rounded-xl border border-line bg-surface p-4">
              <summary className="cursor-pointer text-sm font-medium text-ink">Raw API response</summary>
              <pre className="mt-3 max-h-96 overflow-auto text-xs text-ink-2">{JSON.stringify(decision, null, 2)}</pre>
            </details>
          ) : null}
        </div>
      </div>
    </Container>
  );
}

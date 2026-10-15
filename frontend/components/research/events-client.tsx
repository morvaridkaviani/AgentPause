"use client";

import { ChevronDown, ChevronRight, Download, Radio } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Fragment, useCallback, useEffect, useState } from "react";

import { DecisionBadge } from "@/components/decision/decision-badge";
import { Container, PageHeader } from "@/components/layout/page";
import { Select, TextInput, Toggle } from "@/components/ui/form";
import { EmptyState, ErrorState } from "@/components/ui/feedback";
import { Badge, Button, ButtonLink, Skeleton } from "@/components/ui/primitives";
import { api, downloadUrl } from "@/lib/api";
import { DECISION_META, policyLabel, RESPONSE_LABEL } from "@/lib/format";
import type { ApiEvent, DecisionType } from "@/lib/types";

import { TokenPrompt } from "./token-gate";

const PAGE = 50;

type Filters = { session_id: string; mode: string; scenario: string; policy: string; decision: string; risk: string; type: string; interventions_only: boolean };

export function EventsClient() {
  const params = useSearchParams();
  const [filters, setFilters] = useState<Filters>({ session_id: params.get("session") ?? "", mode: "", scenario: "", policy: "", decision: "", risk: "", type: "", interventions_only: false });
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<{ total: number; items: ApiEvent[] } | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [live, setLive] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  const query = useCallback(
    () => ({
      session_id: filters.session_id || undefined,
      mode: filters.mode || undefined,
      scenario: filters.scenario || undefined,
      policy: filters.policy || undefined,
      decision: filters.decision || undefined,
      risk: filters.risk || undefined,
      type: filters.type || undefined,
      interventions_only: filters.interventions_only || undefined,
    }),
    [filters],
  );

  const load = useCallback(() => {
    api
      .events({ ...query(), offset, limit: PAGE })
      .then((d) => {
        setData(d);
        setError(null);
      })
      .catch(setError);
  }, [query, offset]);
  useEffect(load, [load]);
  useEffect(() => {
    if (!live) return;
    const t = window.setInterval(load, 2000);
    return () => window.clearInterval(t);
  }, [live, load]);

  const set = (key: keyof Filters, value: string | boolean) => {
    setOffset(0);
    setFilters((f) => ({ ...f, [key]: value }));
  };

  return (
    <Container className="pt-8">
      <PageHeader
        eyebrow="Event log"
        title="Every proposal, decision, and response"
        description="Append-only log across demo, study, and API sessions. Participants appear only as pseudonymous codes."
        actions={
          <ButtonLink href={downloadUrl("/events", { ...query(), format: "csv" })} variant="secondary" icon={<Download className="size-4" aria-hidden />}>
            Export CSV
          </ButtonLink>
        }
      />
      <div className="mt-4 flex flex-wrap items-end gap-3" role="group" aria-label="Filters">
        <label className="flex min-w-56 flex-col gap-1 text-xs font-medium text-ink-2">
          Session ID
          <TextInput value={filters.session_id} onChange={(v) => set("session_id", v.trim())} placeholder="any" className="h-9" />
        </label>
        <Filter label="Mode" value={filters.mode} onChange={(v) => set("mode", v)} options={[["", "All"], ["demo", "Demo"], ["study", "Study"], ["api", "API"]]} />
        <Filter label="Scenario" value={filters.scenario} onChange={(v) => set("scenario", v)} options={[["", "All"], ["travel", "Travel"], ["email", "Email"], ["shopping", "Shopping"], ["files", "Files"], ["calendar", "Calendar"], ["research", "Research"]]} />
        <Filter label="Type" value={filters.type} onChange={(v) => set("type", v)} options={[["", "All"], ["decision", "Decision"], ["intervention", "Intervention"], ["response", "Response"], ["executed", "Executed"], ["ask_why", "Ask why"], ["completed", "Completed"]]} />
        <Filter label="Decision" value={filters.decision} onChange={(v) => set("decision", v)} options={[["", "All"], ...(Object.keys(DECISION_META).filter((d) => d !== "SKIPPED").map((d) => [d, DECISION_META[d as DecisionType].label]) as [string, string][])]} />
        <Filter label="Risk" value={filters.risk} onChange={(v) => set("risk", v)} options={[["", "All"], ["low", "Low"], ["medium", "Medium"], ["high", "High"]]} />
        <div className="flex flex-col gap-2 pb-1">
          <Toggle label="Interruptions only" checked={filters.interventions_only} onChange={(v) => set("interventions_only", v)} />
        </div>
        <div className="flex flex-col gap-2 pb-1">
          <Toggle label="Live" checked={live} onChange={setLive} />
        </div>
      </div>

      <div className="mt-4">
        <TokenPrompt error={error} onSaved={load} />
        {error ? <ErrorState error={error} onRetry={load} /> : null}
        {!data && !error ? <Skeleton className="h-64" /> : null}
        {data && data.items.length === 0 ? <EmptyState title="No events match">Run the demo or an API session to create events.</EmptyState> : null}
        {data && data.items.length ? (
          <div className="overflow-x-auto rounded-xl border border-line bg-surface">
            <table className="w-full min-w-[960px] text-sm">
              <caption className="sr-only">Events, newest first</caption>
              <thead>
                <tr className="border-b border-line text-left text-xs text-ink-2">
                  {["", "Time", "Session", "Mode", "Scenario", "Policy", "Step", "Type", "Action", "Decision", "Score", "Risk", "Response", "Latency"].map((h) => (
                    <th key={h} scope="col" className="px-3 py-2 font-medium">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map((e) => (
                  <Fragment key={e.id}>
                    <tr className="border-b border-line">
                      <td className="px-2 py-1.5">
                        <button type="button" aria-expanded={expanded === e.id} aria-label="Show payload" onClick={() => setExpanded(expanded === e.id ? null : e.id)} className="rounded p-1 text-ink-3 hover:bg-surface-2">
                          {expanded === e.id ? <ChevronDown className="size-4" aria-hidden /> : <ChevronRight className="size-4" aria-hidden />}
                        </button>
                      </td>
                      <td className="tabular px-3 py-1.5 whitespace-nowrap text-ink-2">{new Date(e.created_at).toLocaleTimeString()}</td>
                      <td className="px-3 py-1.5 font-mono text-xs">
                        <button type="button" onClick={() => set("session_id", e.session_id)} className="text-accent-strong hover:underline">
                          {e.session_id.slice(0, 8)}
                        </button>
                      </td>
                      <td className="px-3 py-1.5 text-ink-2">{e.mode}</td>
                      <td className="px-3 py-1.5 text-ink-2">{e.scenario_id ?? "—"}</td>
                      <td className="px-3 py-1.5 text-ink-2">{policyLabel(e.policy)}</td>
                      <td className="tabular px-3 py-1.5 text-ink-2">{e.step_index === null ? "—" : e.step_index + 1}</td>
                      <td className="px-3 py-1.5">
                        <Badge>{e.type}</Badge>
                      </td>
                      <td className="px-3 py-1.5 text-ink">{e.action ?? "—"}</td>
                      <td className="px-3 py-1.5">{e.decision ? <DecisionBadge decision={e.decision} size="sm" /> : "—"}</td>
                      <td className="tabular px-3 py-1.5 text-ink">{e.score === null ? "—" : e.score.toFixed(2)}</td>
                      <td className="px-3 py-1.5 text-ink-2">{e.risk_level ?? "—"}</td>
                      <td className="px-3 py-1.5 text-ink-2">{e.user_response ? RESPONSE_LABEL[e.user_response] ?? e.user_response : "—"}</td>
                      <td className="tabular px-3 py-1.5 text-ink-2">{e.latency_ms === null ? "—" : `${e.latency_ms.toFixed(1)} ms`}</td>
                    </tr>
                    {expanded === e.id ? (
                      <tr className="border-b border-line bg-surface-2">
                        <td colSpan={14} className="px-4 py-3">
                          <pre className="max-h-80 overflow-auto text-xs text-ink-2">{JSON.stringify(e.payload, null, 2)}</pre>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                ))}
              </tbody>
            </table>
            <div className="flex items-center justify-between gap-3 px-4 py-2 text-sm text-ink-2">
              <span className="flex items-center gap-1.5">
                {live ? <Radio className="size-4 text-accent" aria-hidden /> : null}
                {offset + 1}–{Math.min(offset + PAGE, data.total)} of {data.total.toLocaleString()}
              </span>
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>
                  Newer
                </Button>
                <Button variant="secondary" size="sm" disabled={offset + PAGE >= data.total} onClick={() => setOffset(offset + PAGE)}>
                  Older
                </Button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </Container>
  );
}

function Filter({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: [string, string][] }) {
  return (
    <label className="flex min-w-32 flex-col gap-1 text-xs font-medium text-ink-2">
      {label}
      <Select value={value} onChange={onChange} options={options.map(([v, l]) => ({ value: v, label: l }))} className="h-9" />
    </label>
  );
}

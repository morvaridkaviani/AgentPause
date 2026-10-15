"use client";

import clsx from "clsx";
import { BookOpen, Bot, Calendar, CircleUserRound, Folder, Mail, Plane, ShieldAlert, ShoppingCart, type LucideIcon } from "lucide-react";

import { Badge } from "@/components/ui/primitives";
import { categoryLabel, stepLabel } from "@/lib/format";
import type { ScenarioSummary, StepInfo } from "@/lib/types";

export const SCENARIO_ICON: Record<string, LucideIcon> = {
  plane: Plane,
  mail: Mail,
  cart: ShoppingCart,
  folder: Folder,
  calendar: Calendar,
  book: BookOpen,
};

export function ScenarioIcon({ icon, className }: { icon: string; className?: string }) {
  const Icon = SCENARIO_ICON[icon] ?? Bot;
  return <Icon className={className} aria-hidden />;
}

export function ScenarioPicker({ scenarios, value, onChange }: { scenarios: ScenarioSummary[]; value: string | null; onChange: (id: string) => void }) {
  return (
    <div role="radiogroup" aria-label="Choose a task" className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {scenarios.map((s) => {
        const selected = s.id === value;
        return (
          <button
            key={s.id}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(s.id)}
            className={clsx(
              "flex flex-col gap-2 rounded-xl border bg-surface p-4 text-left transition-colors",
              selected ? "border-accent ring-1 ring-accent" : "border-line hover:border-line-strong",
            )}
          >
            <div className="flex items-center gap-2">
              <span className="inline-flex size-8 items-center justify-center rounded-lg bg-accent-soft text-accent-strong">
                <ScenarioIcon icon={s.icon} className="size-4" />
              </span>
              <span className="font-medium text-ink">{s.agent_name}</span>
            </div>
            <p className="text-sm text-ink-2">{s.description}</p>
            <div className="mt-auto flex flex-wrap gap-1.5 pt-1">
              <Badge>{s.n_steps} steps</Badge>
              <Badge>{s.n_assumptions} unclear details</Badge>
              <Badge tone="critical">
                <ShieldAlert className="size-3" aria-hidden /> {s.irreversible_steps.length} can&apos;t be undone
              </Badge>
            </div>
          </button>
        );
      })}
    </div>
  );
}

export function BriefPanel({ scenario, brief }: { scenario: ScenarioSummary; brief: string | null }) {
  return (
    <div className="flex flex-col gap-3">
      <div>
        <p className="text-xs font-semibold tracking-wide text-ink-2 uppercase">Your instruction</p>
        <p className="mt-1 rounded-lg bg-surface-2 px-3 py-2 text-sm text-ink">“{scenario.goal}”</p>
      </div>
      {brief ? (
        <div>
          <p className="flex items-center gap-1.5 text-xs font-semibold tracking-wide text-ink-2 uppercase">
            <CircleUserRound className="size-3.5" aria-hidden /> What you really want (the assistant doesn&apos;t know this)
          </p>
          <p className="mt-1 text-sm leading-relaxed text-ink">{brief}</p>
          <p className="mt-1 text-xs text-ink-3">When the assistant asks you something, check it against this.</p>
        </div>
      ) : null}
    </div>
  );
}

export function StepRail({ steps, current, done, simple = false }: { steps: StepInfo[]; current: number; done: boolean; simple?: boolean }) {
  return (
    <ol aria-label="Task plan" className="flex flex-col">
      {steps.map((s) => {
        const status = done || s.index < current ? "done" : s.index === current ? "current" : "todo";
        return (
          <li key={s.id} className="relative flex gap-3 pb-3 last:pb-0">
            <span
              aria-hidden
              className={clsx(
                "relative z-10 mt-1 size-2.5 shrink-0 rounded-full border-2",
                status === "done" && "border-accent bg-accent",
                status === "current" && "border-accent bg-surface ring-4 ring-accent/20",
                status === "todo" && "border-line-strong bg-surface",
              )}
            />
            <div className="min-w-0">
              <p className={clsx("text-sm", status === "current" ? "font-medium text-ink" : "text-ink-2")}>
                <span className="sr-only">{status === "done" ? "Done: " : status === "current" ? "Current: " : "Upcoming: "}</span>
                {s.label}
              </p>
              {simple ? (
                !s.reversible || s.requires_human_input ? (
                  <p className="text-xs text-ink-3">
                    {[!s.reversible ? "can't be undone" : null, s.requires_human_input ? "needs you" : null].filter(Boolean).join(" · ")}
                  </p>
                ) : null
              ) : (
                <p className="text-xs text-ink-3">
                  {stepLabel(s.index)} · {categoryLabel(s.category)}
                  {!s.reversible ? " · irreversible" : ""}
                  {s.breakpoint ? " · natural pause" : ""}
                  {s.requires_human_input ? " · needs you" : ""}
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

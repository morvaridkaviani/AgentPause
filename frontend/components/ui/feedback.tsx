import clsx from "clsx";
import { AlertTriangle, FlaskConical, Info, RotateCw } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "./primitives";

export function EmptyState({ icon, title, children, action }: { icon?: ReactNode; title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-line-strong px-6 py-12 text-center">
      {icon ? <div className="text-ink-3">{icon}</div> : null}
      <div>
        <p className="font-medium text-ink">{title}</p>
        {children ? <div className="mx-auto mt-1 max-w-md text-sm text-ink-2">{children}</div> : null}
      </div>
      {action}
    </div>
  );
}

export function ErrorState({ error, onRetry, title = "Something went wrong" }: { error: unknown; onRetry?: () => void; title?: string }) {
  const message = error instanceof Error ? error.message : String(error);
  return (
    <div role="alert" className="flex items-start gap-3 rounded-xl border border-critical/30 bg-critical/5 px-4 py-3">
      <AlertTriangle className="mt-0.5 size-5 shrink-0 text-critical" aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="font-medium text-ink">{title}</p>
        <p className="mt-0.5 text-sm break-words text-ink-2">{message}</p>
        {message.includes("fetch") || message.includes("Failed") ? (
          <p className="mt-1 text-xs text-ink-3">Is the API server running? Start it with <code>make dev</code> (see Getting started).</p>
        ) : null}
      </div>
      {onRetry ? (
        <Button variant="secondary" size="sm" onClick={onRetry} icon={<RotateCw className="size-3.5" aria-hidden />}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}

export function Callout({ tone = "info", title, children, className }: { tone?: "info" | "simulated" | "warning"; title?: string; children: ReactNode; className?: string }) {
  const Icon = tone === "simulated" ? FlaskConical : tone === "warning" ? AlertTriangle : Info;
  return (
    <div
      className={clsx(
        "flex gap-3 rounded-xl border px-4 py-3 text-sm",
        tone === "warning" ? "border-warning/40 bg-warning/10" : tone === "simulated" ? "border-accent/25 bg-accent-soft" : "border-line bg-surface-2",
        className,
      )}
    >
      <Icon className={clsx("mt-0.5 size-4 shrink-0", tone === "simulated" ? "text-accent-strong" : "text-ink-2")} aria-hidden />
      <div className="min-w-0 text-ink-2">
        {title ? <p className="font-medium text-ink">{title}</p> : null}
        {children}
      </div>
    </div>
  );
}

export function SimulatedNote({ children }: { children?: ReactNode }) {
  return (
    <Callout tone="simulated" title="Simulated results">
      {children ?? "Produced by the AgentPause simulator under documented assumptions. Not evaluated with human participants."}
    </Callout>
  );
}

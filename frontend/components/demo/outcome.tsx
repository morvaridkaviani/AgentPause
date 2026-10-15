import { CheckCircle2, CircleAlert, FlaskConical, Repeat } from "lucide-react";
import { Button, ButtonLink } from "@/components/ui/primitives";
import { Stat } from "@/components/ui/stat";
import { seconds } from "@/lib/format";
import type { Session } from "@/lib/types";

export function OutcomeSummary({ session, simple = false, onTryAnother }: { session: Session; simple?: boolean; onTryAnother?: () => void }) {
  const outcome = session.outcome ?? {};
  const summary = (outcome.summary ?? {}) as Record<string, number>;
  const success = Boolean(outcome.task_success);
  const cancelled = session.status === "cancelled";
  const compareHref = `/compare?scenario=${session.scenario?.id ?? ""}&seed=${session.seed}`;
  return (
    <section aria-labelledby="outcome-title" className="rounded-2xl border border-line bg-surface p-5 shadow-card">
      <div className="flex flex-wrap items-center gap-3">
        {cancelled ? null : success ? (
          <CheckCircle2 className="size-6 text-good" aria-hidden />
        ) : (
          <CircleAlert className="size-6 text-critical" aria-hidden />
        )}
        <h2 id="outcome-title" className="text-lg font-semibold text-ink">
          {cancelled ? "Task cancelled" : success ? "Done, and no mistakes got through" : "Done, but a mistake got through"}
        </h2>
      </div>
      <p className="mt-1 flex items-center gap-1.5 text-sm text-ink-2">
        <FlaskConical className="size-4" aria-hidden />
        {simple
          ? "Nothing real happened: everything was simulated."
          : `Everything was simulated. Ground truth comes from the scenario script (seed ${session.seed}).`}
      </p>
      <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label={simple ? "Times it asked you" : "Interruptions"} value={summary.interventions ?? "—"} sub={`${summary.questions ?? 0} questions in total`} />
        <Stat label={simple ? "Asked for nothing" : "Unnecessary interruptions"} value={summary.unnecessary ?? "—"} sub="nothing was wrong at the time" />
        <Stat
          label={simple ? "Mistakes caught" : "Errors caught"}
          value={`${summary.errors_caught ?? 0} / ${summary.errors_total ?? 0}`}
          sub={`${summary.missed_interventions ?? 0} never shown to you`}
        />
        <Stat label={simple ? "Time taken (simulated)" : "Task time (simulated)"} value={seconds(outcome.task_duration_s)} sub={`${seconds(outcome.human_time_s)} of it was yours`} />
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {onTryAnother ? (
          <Button onClick={onTryAnother} icon={<Repeat className="size-4" aria-hidden />}>
            Try the same task another way
          </Button>
        ) : null}
        <ButtonLink href={compareHref} variant="secondary">
          {simple ? "Compare all the ways side by side" : "Compare policies on this episode"}
        </ButtonLink>
        {simple ? null : (
          <ButtonLink href="/dashboard?source=sessions" variant="ghost">
            See it on the dashboard
          </ButtonLink>
        )}
      </div>
    </section>
  );
}

"use client";

import { CheckCircle2, ClipboardList, Play } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { InterventionCardView } from "@/components/demo/intervention-card";
import { BriefPanel, StepRail } from "@/components/demo/scenario";
import { Timeline } from "@/components/demo/timeline";
import { Container } from "@/components/layout/page";
import { TextInput } from "@/components/ui/form";
import { Callout, ErrorState } from "@/components/ui/feedback";
import { Badge, Button, Card, CardBody, Spinner } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { load, remove, save } from "@/lib/storage";
import type { Instrument, Participant, StudyConfig } from "@/lib/types";
import { useSessionRunner } from "@/lib/use-session";

import { Questionnaire } from "./questionnaire";

type Phase = "welcome" | "briefing" | "task" | "post" | "final" | "done";
interface Progress {
  code: string | null;
  block: number;
  phase: Phase;
  sessionId: string | null;
  instrumentIndex: number;
}
const KEY = "agentpause.study";
const START: Progress = { code: null, block: 0, phase: "welcome", sessionId: null, instrumentIndex: 0 };

function nextBlock(current: number, n: number, hasFinal: boolean): Partial<Progress> {
  return current + 1 < n
    ? { block: current + 1, phase: "briefing", sessionId: null, instrumentIndex: 0 }
    : { phase: hasFinal ? "final" : "done", instrumentIndex: 0 };
}

export function StudyClient() {
  const [config, setConfig] = useState<StudyConfig | null>(null);
  const [instruments, setInstruments] = useState<Record<string, Instrument>>({});
  const [participant, setParticipant] = useState<Participant | null>(null);
  const [progress, setProgress] = useState<Progress>(START);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [resumeCode, setResumeCode] = useState("");
  const runner = useSessionRunner({ autoplay: true, delayMs: 1400 });

  const update = useCallback((next: Partial<Progress>) => {
    setProgress((p) => {
      const merged = { ...p, ...next };
      save(KEY, merged);
      return merged;
    });
  }, []);

  useEffect(() => {
    Promise.all([api.studyConfig(), api.instruments()])
      .then(([c, list]) => {
        setConfig(c);
        setInstruments(Object.fromEntries(list.map((i) => [i.id, i])));
      })
      .catch(setError);
    const saved = load<Progress>(KEY, START);
    if (saved.code) {
      api
        .participant(saved.code)
        .then((p) => {
          setParticipant(p);
          setProgress(saved);
          if (saved.sessionId && saved.phase === "task") void runner.run(() => api.session(saved.sessionId!));
        })
        .catch(() => remove(KEY));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const block = participant?.plan[progress.block];
  const total = participant?.plan.length ?? 0;
  const practiceOffset = participant?.plan[0]?.practice ? 1 : 0;
  const post = useMemo(() => (config?.post_task_instruments ?? []).map((id) => instruments[id]).filter((i): i is Instrument => Boolean(i?.ready)), [config, instruments]);
  const final = useMemo(() => (config?.final_instruments ?? []).map((id) => instruments[id]).filter((i): i is Instrument => Boolean(i?.ready)), [config, instruments]);

  // After the episode ends the participant moves on explicitly, which also gives them a moment to see the outcome.
  const finishTask = () => {
    if (!block) return;
    update(block.practice || !post.length ? nextBlock(progress.block, total, final.length > 0) : { phase: "post", instrumentIndex: 0 });
  };

  const enrol = async () => {
    setBusy(true);
    setError(null);
    try {
      const p = await api.enrol();
      const consented = await api.updateParticipant(p.code, { consented: true });
      setParticipant(consented);
      update({ code: p.code, block: 0, phase: "briefing", sessionId: null });
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  const resume = async () => {
    setBusy(true);
    setError(null);
    try {
      const p = await api.participant(resumeCode.trim().toUpperCase());
      setParticipant(p);
      update({ code: p.code, block: 0, phase: p.completed ? "done" : "briefing", sessionId: null });
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  const startBlock = async () => {
    if (!participant) return;
    setBusy(true);
    setError(null);
    try {
      const session = await api.startBlock(participant.code, progress.block);
      runner.attach(session);
      runner.setPlaying(true);
      update({ phase: "task", sessionId: session.id });
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  const submit = async (instrument: Instrument, responses: Record<string, number | string>, isFinal: boolean) => {
    if (!participant) return;
    setBusy(true);
    setError(null);
    try {
      await api.submitQuestionnaire({
        participant_code: participant.code,
        instrument_id: instrument.id,
        responses,
        session_id: isFinal ? undefined : (progress.sessionId ?? undefined),
        block: isFinal ? undefined : progress.block,
      });
      const list = isFinal ? final : post;
      if (progress.instrumentIndex + 1 < list.length) update({ instrumentIndex: progress.instrumentIndex + 1 });
      else if (isFinal) {
        await api.updateParticipant(participant.code, { completed: true });
        update({ phase: "done" });
      } else update(nextBlock(progress.block, total, final.length > 0));
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  if (!config) {
    return <Container className="pt-10">{error ? <ErrorState error={error} /> : <Spinner label="Loading the study" />}</Container>;
  }

  return (
    <Container className="max-w-5xl pt-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-line pb-4">
        <div>
          <p className="text-xs font-semibold tracking-wide text-accent uppercase">Study</p>
          <h1 className="text-2xl font-semibold text-ink">{config.title}</h1>
        </div>
        {participant ? (
          <div className="flex items-center gap-2 text-sm text-ink-2">
            <span>
              Participant <span className="font-mono font-semibold text-ink">{participant.code}</span>
            </span>
            {progress.phase !== "welcome" && progress.phase !== "done" && block ? (
              <Badge>{block.practice ? "Practice" : `Task ${progress.block - practiceOffset + 1} of ${total - practiceOffset}`}</Badge>
            ) : null}
          </div>
        ) : null}
      </div>
      {error ? (
        <div className="mb-4">
          <ErrorState error={error} />
        </div>
      ) : null}

      {progress.phase === "welcome" ? (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-[minmax(0,1fr)_18rem]">
          <Card>
            <CardBody className="flex flex-col gap-4">
              <h2 className="text-lg font-semibold text-ink">Information and consent</h2>
              <p className="leading-relaxed whitespace-pre-line text-ink">{config.consent_text}</p>
              <Button size="lg" onClick={enrol} loading={busy} className="self-start">
                I agree to take part
              </Button>
            </CardBody>
          </Card>
          <Card className="h-fit">
            <CardBody className="flex flex-col gap-3">
              <h2 className="text-sm font-semibold text-ink">Returning?</h2>
              <label htmlFor="resume" className="text-xs text-ink-2">
                Enter your participant code
              </label>
              <TextInput id="resume" value={resumeCode} onChange={setResumeCode} placeholder="P-XXXXXX" />
              <Button variant="secondary" onClick={resume} disabled={!resumeCode.trim()} loading={busy}>
                Resume
              </Button>
            </CardBody>
          </Card>
        </div>
      ) : null}

      {progress.phase === "briefing" && block ? (
        <Card>
          <CardBody className="flex flex-col gap-4">
            <h2 className="text-lg font-semibold text-ink">{block.practice ? "Practice task" : "Next task"}</h2>
            {block.practice ? (
              <Callout title="This one is for practice">
                Get used to the interface: the assistant pauses and asks you when it needs input. Your answers here are not analysed.
              </Callout>
            ) : null}
            <p className="text-ink-2">
              You will supervise an AI assistant doing a task for you. Read your situation carefully: the assistant does not know it, and you can use it to
              check what the assistant shows you. Everything is simulated.
            </p>
            <Button size="lg" onClick={startBlock} loading={busy} className="self-start" icon={<Play className="size-4" aria-hidden />}>
              Start
            </Button>
          </CardBody>
        </Card>
      ) : null}

      {progress.phase === "task" && runner.session ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[16rem_minmax(0,1fr)]">
          <aside className="flex flex-col gap-5">
            {runner.session.scenario ? <BriefPanel scenario={runner.session.scenario} brief={runner.session.brief} /> : null}
            <StepRail steps={runner.session.steps} current={runner.session.step_index} done={runner.done} />
          </aside>
          <section className="flex min-w-0 flex-col gap-4" aria-label="Assistant activity">
            <p aria-live="polite" className="text-sm text-ink-2">
              {runner.session.status === "awaiting_human" ? "The assistant is waiting for you." : runner.done ? "Task finished." : "The assistant is working…"}
            </p>
            {runner.done ? (
              <Callout title="Task finished">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span>{block?.practice ? "That was the practice task." : "Thank you. Next, a few questions about this task."}</span>
                  <Button onClick={finishTask} autoFocus>
                    Continue
                  </Button>
                </div>
              </Callout>
            ) : null}
            {runner.session.pending ? (
              <InterventionCardView key={runner.session.pending.intervention_id} card={runner.session.pending} onRespond={runner.respond} busy={runner.busy} showInternals={false} />
            ) : null}
            {runner.error ? <ErrorState error={runner.error} onRetry={runner.refresh} /> : null}
            <Timeline items={[...runner.session.timeline].reverse()} selectedSeq={null} onSelect={() => undefined} showGroundTruth={false} />
          </section>
        </div>
      ) : null}

      {(progress.phase === "post" || progress.phase === "final") && (progress.phase === "post" ? post : final)[progress.instrumentIndex] ? (
        <Card>
          <CardBody>
            <p className="mb-3 flex items-center gap-2 text-sm text-ink-2">
              <ClipboardList className="size-4" aria-hidden />
              {progress.phase === "post" ? "About the task you just did" : "A few final questions"} · {progress.instrumentIndex + 1} of {(progress.phase === "post" ? post : final).length}
            </p>
            <Questionnaire
              key={`${progress.phase}-${progress.block}-${progress.instrumentIndex}`}
              instrument={(progress.phase === "post" ? post : final)[progress.instrumentIndex]!}
              onSubmit={(r) => submit((progress.phase === "post" ? post : final)[progress.instrumentIndex]!, r, progress.phase === "final")}
              busy={busy}
            />
          </CardBody>
        </Card>
      ) : null}

      {progress.phase === "done" ? (
        <Card>
          <CardBody className="flex flex-col items-start gap-3">
            <CheckCircle2 className="size-8 text-good" aria-hidden />
            <h2 className="text-xl font-semibold text-ink">Thank you!</h2>
            <p className="text-ink-2">
              You have completed the study. Your participant code is <span className="font-mono font-semibold text-ink">{participant?.code}</span>. Keep it if you
              want to withdraw your data later.
            </p>
            <Button
              variant="ghost"
              onClick={() => {
                remove(KEY);
                setParticipant(null);
                setProgress(START);
                runner.setSession(null);
              }}
            >
              Start over (new participant)
            </Button>
          </CardBody>
        </Card>
      ) : null}
    </Container>
  );
}

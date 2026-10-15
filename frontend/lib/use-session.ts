"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "./api";
import type { ResponseName, Session } from "./types";

/** Drives a simulated session: stepping, optional autoplay, and human responses. */
export function useSessionRunner({ autoplay = false, delayMs = 900 }: { autoplay?: boolean; delayMs?: number } = {}) {
  const [session, setSession] = useState<Session | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [playing, setPlaying] = useState(autoplay);
  const [delay, setDelay] = useState(delayMs);
  const inFlight = useRef(false);

  const run = useCallback(async (fn: () => Promise<Session>) => {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError(null);
    try {
      setSession(await fn());
    } catch (err) {
      setError(err);
      setPlaying(false);
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }, []);

  const attach = useCallback((s: Session) => {
    setSession(s);
    setError(null);
  }, []);

  const step = useCallback(() => {
    if (!session) return;
    void run(async () => (await api.step(session.id, "next")).session);
  }, [run, session]);

  const respond = useCallback(
    (response: ResponseName, answers: Record<string, string> = {}) => {
      if (!session) return;
      const pending = session.pending?.intervention_id;
      void run(async () => (await api.respond(session.id, response, answers, pending)).session);
    },
    [run, session],
  );

  const refresh = useCallback(() => {
    if (!session) return;
    void run(() => api.session(session.id));
  }, [run, session]);

  // Autoplay: keep stepping while the agent is running; stop at cards and at the end.
  useEffect(() => {
    if (!playing || !session || busy || session.status !== "running") return;
    const timer = window.setTimeout(step, delay);
    return () => window.clearTimeout(timer);
  }, [playing, session, busy, step, delay]);

  const done = session?.status === "completed" || session?.status === "cancelled";
  return { session, attach, step, respond, refresh, busy, error, playing, setPlaying, delay, setDelay, done, run, setSession };
}

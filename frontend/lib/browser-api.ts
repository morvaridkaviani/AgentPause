/** Client for the in-browser engine (static online demo only). See public/py-worker.js. */
import { useSyncExternalStore } from "react";

import { BASE_PATH } from "./site";

export interface EngineStatus {
  state: "idle" | "loading" | "ready" | "failed";
  text: string;
}
export interface EngineResponse {
  status: number;
  contentType: string;
  body: string;
}

const IDLE: EngineStatus = { state: "idle", text: "" };
let status: EngineStatus = IDLE;
let worker: Worker | null = null;
let nextId = 1;
const pending = new Map<number, { resolve: (r: EngineResponse) => void; reject: (e: Error) => void }>();
const listeners = new Set<() => void>();

function setStatus(next: EngineStatus): void {
  status = next;
  for (const listener of listeners) listener();
}

function ensureWorker(): Worker {
  if (worker) return worker;
  const version = process.env.NEXT_PUBLIC_BUILD_ID ?? "dev";
  worker = new Worker(`${BASE_PATH}/py-worker.js?v=${encodeURIComponent(version)}`, { type: "module" });
  setStatus({ state: "loading", text: "Starting the in-browser engine…" });
  worker.onmessage = (event: MessageEvent) => {
    const data = event.data as { type?: string; state?: EngineStatus["state"]; text?: string; id?: number; result?: EngineResponse; error?: string };
    if (data.type === "status") {
      setStatus({ state: data.state ?? "loading", text: data.text ?? "" });
      return;
    }
    const entry = data.id !== undefined ? pending.get(data.id) : undefined;
    if (!entry || data.id === undefined) return;
    pending.delete(data.id);
    if (data.error !== undefined) entry.reject(new Error(data.error));
    else entry.resolve(data.result as EngineResponse);
  };
  worker.onerror = (event) => setStatus({ state: "failed", text: event.message || "The in-browser engine crashed." });
  return worker;
}

/** Start downloading the engine early (e.g. while the visitor reads the page). */
export function warmUpEngine(): void {
  ensureWorker();
}

export function engineRequest(method: string, path: string, query: string, body: string | null): Promise<EngineResponse> {
  const w = ensureWorker();
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    w.postMessage({ id, method, path, query, body });
  });
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useEngineStatus(): EngineStatus {
  return useSyncExternalStore(subscribe, () => status, () => IDLE);
}

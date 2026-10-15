"use client";

import { AlertTriangle, Cpu, Loader2 } from "lucide-react";
import { useEffect } from "react";

import { useEngineStatus, warmUpEngine } from "@/lib/browser-api";
import { REPO_URL } from "@/lib/site";

/** Shown only in the static online demo: explains that everything runs in the browser, and shows engine start-up. */
export function EngineBanner() {
  const status = useEngineStatus();
  useEffect(() => {
    warmUpEngine();
  }, []);
  return (
    <div className="border-b border-line bg-accent-soft text-sm text-ink">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2 sm:px-6">
        <span className="inline-flex items-center gap-1.5 font-medium">
          <Cpu className="size-4 text-accent-strong" aria-hidden /> Online demo
        </span>
        <span className="text-ink-2">
          Everything runs in your browser (Python in WebAssembly). Nothing is stored, and reloading starts fresh.
        </span>
        <span className="ml-auto inline-flex items-center gap-1.5 text-xs" aria-live="polite">
          {status.state === "loading" ? (
            <>
              <Loader2 className="size-3.5 animate-spin" aria-hidden />
              {status.text} <span className="text-ink-3">(first visit: about 20 MB)</span>
            </>
          ) : status.state === "ready" ? (
            <span className="text-good-ink">Engine ready</span>
          ) : status.state === "failed" ? (
            <span className="inline-flex items-center gap-1 text-critical">
              <AlertTriangle className="size-3.5" aria-hidden /> The engine could not start: {status.text}.{" "}
              <a href={REPO_URL} className="underline">
                Run it locally
              </a>
            </span>
          ) : null}
        </span>
      </div>
    </div>
  );
}

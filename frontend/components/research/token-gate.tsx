"use client";

import { KeyRound } from "lucide-react";
import { useState } from "react";

import { TextInput } from "@/components/ui/form";
import { Button } from "@/components/ui/primitives";
import { ApiError, setResearcherToken } from "@/lib/api";

/** Shown when a researcher-only endpoint returns 401: asks for the token configured on the server. */
export function TokenPrompt({ error, onSaved }: { error: unknown; onSaved: () => void }) {
  const [token, setToken] = useState("");
  if (!(error instanceof ApiError) || error.status !== 401) return null;
  return (
    <form
      className="flex flex-wrap items-end gap-2 rounded-xl border border-line bg-surface p-4"
      onSubmit={(e) => {
        e.preventDefault();
        setResearcherToken(token || null);
        onSaved();
      }}
    >
      <div className="min-w-64 flex-1">
        <label htmlFor="researcher-token" className="flex items-center gap-1.5 text-sm font-medium text-ink">
          <KeyRound className="size-4" aria-hidden /> Researcher token
        </label>
        <p className="mb-1.5 text-xs text-ink-2">This server protects research data. The token is kept for this browser tab only.</p>
        <TextInput id="researcher-token" type="password" value={token} onChange={setToken} />
      </div>
      <Button type="submit">Unlock</Button>
    </form>
  );
}

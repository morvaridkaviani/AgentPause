import clsx from "clsx";
import Link from "next/link";
import type { ReactNode } from "react";

import { Logo } from "./logo";
import { API_DOCS_URL, REPO_URL } from "@/lib/site";

export function Container({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={clsx("mx-auto w-full max-w-7xl px-4 sm:px-6", className)}>{children}</div>;
}

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="flex flex-col gap-4 border-b border-line pb-6 md:flex-row md:items-end md:justify-between">
      <div className="min-w-0">
        {eyebrow ? <p className="text-xs font-semibold tracking-wide text-accent uppercase">{eyebrow}</p> : null}
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-ink sm:text-3xl">{title}</h1>
        {description ? <div className="mt-2 max-w-3xl text-sm text-ink-2 sm:text-base">{description}</div> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function SiteFooter() {
  const repo = REPO_URL;
  return (
    <footer className="mt-16 border-t border-line">
      <Container className="flex flex-col gap-4 py-8 text-sm text-ink-2 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2">
          <Logo className="size-5" />
          <span>
            AgentPause, research infrastructure for adaptive human intervention timing. All agent actions in this app are
            simulated.
          </span>
        </div>
        <nav aria-label="Footer" className="flex flex-wrap gap-4">
          <Link href="/about" className="hover:text-ink">
            Research &amp; limitations
          </Link>
          <a href={API_DOCS_URL} className="hover:text-ink">
            API docs
          </a>
          {repo ? (
            <a href={repo} className="hover:text-ink" rel="noreferrer">
              Source code
            </a>
          ) : (
            <span title="Set NEXT_PUBLIC_REPO_URL to link the repository">Source code: see README</span>
          )}
          <span>MIT licence</span>
        </nav>
      </Container>
    </footer>
  );
}

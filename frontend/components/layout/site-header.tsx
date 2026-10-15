"use client";

import clsx from "clsx";
import { ChevronDown, Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Logo } from "./logo";
import { ThemeToggle } from "./theme";

/** What most visitors need. */
export const NAV = [
  { href: "/demo", label: "Try the demo" },
  { href: "/preferences", label: "My preferences" },
  { href: "/about", label: "How it works" },
];

/** Tools for researchers, grouped in one menu so they do not crowd the main navigation. */
export const RESEARCH_NAV = [
  { href: "/lab", label: "Decision lab", description: "Change one action and see how each policy decides" },
  { href: "/compare", label: "Compare policies", description: "Run the same task under several policies" },
  { href: "/dashboard", label: "Dashboard", description: "Metrics and charts" },
  { href: "/experiments", label: "Experiments", description: "Run simulated experiments" },
  { href: "/events", label: "Event log", description: "Every decision and response" },
  { href: "/study", label: "User study", description: "The participant flow" },
  { href: "/study/admin", label: "Study setup", description: "Conditions and questionnaires" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const active = (href: string) => pathname === href || pathname.startsWith(`${href}/`);
  const researchActive = RESEARCH_NAV.some((item) => active(item.href));
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-page/85 backdrop-blur">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:rounded-md focus:bg-surface focus:px-3 focus:py-2">
        Skip to content
      </a>
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold text-ink" onClick={() => setOpen(false)}>
          <Logo className="size-6" />
          <span>AgentPause</span>
        </Link>
        <nav aria-label="Main" className="ml-4 hidden flex-1 items-center gap-1 md:flex">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active(item.href) ? "page" : undefined}
              className={clsx(
                "rounded-md px-3 py-1.5 text-sm transition-colors",
                active(item.href) ? "bg-surface-2 font-medium text-ink" : "text-ink-2 hover:text-ink",
              )}
            >
              {item.label}
            </Link>
          ))}
          <ResearchMenu active={researchActive} isActive={active} />
        </nav>
        <div className="ml-auto flex items-center gap-1">
          <ThemeToggle />
          <button
            type="button"
            className="inline-flex size-9 items-center justify-center rounded-lg text-ink-2 hover:bg-surface-2 md:hidden"
            aria-expanded={open}
            aria-controls="mobile-nav"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X className="size-5" aria-hidden /> : <Menu className="size-5" aria-hidden />}
          </button>
        </div>
      </div>
      {open ? (
        <nav id="mobile-nav" aria-label="Main" className="border-t border-line px-4 py-3 md:hidden">
          <ul className="flex flex-col gap-1">
            {NAV.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={() => setOpen(false)}
                  aria-current={active(item.href) ? "page" : undefined}
                  className={clsx("block rounded-md px-3 py-2 text-sm", active(item.href) ? "bg-surface-2 font-medium" : "text-ink")}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
          <p className="mt-3 px-3 text-xs font-semibold tracking-wide text-ink-3 uppercase">For researchers</p>
          <ul className="mt-1 grid grid-cols-2 gap-1">
            {RESEARCH_NAV.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={() => setOpen(false)}
                  aria-current={active(item.href) ? "page" : undefined}
                  className={clsx("block rounded-md px-3 py-2 text-sm", active(item.href) ? "bg-surface-2 font-medium" : "text-ink-2")}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      ) : null}
    </header>
  );
}

function ResearchMenu({ active, isActive }: { active: boolean; isActive: (href: string) => boolean }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointer = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        aria-expanded={open}
        aria-controls="research-menu"
        onClick={() => setOpen((v) => !v)}
        className={clsx(
          "inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-sm transition-colors",
          active ? "bg-surface-2 font-medium text-ink" : "text-ink-2 hover:text-ink",
        )}
      >
        For researchers
        <ChevronDown className={clsx("size-4 transition-transform", open && "rotate-180")} aria-hidden />
      </button>
      {open ? (
        <ul id="research-menu" className="absolute left-0 mt-2 w-80 rounded-xl border border-line bg-surface p-1.5 shadow-card">
          {RESEARCH_NAV.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                onClick={() => setOpen(false)}
                aria-current={isActive(item.href) ? "page" : undefined}
                className={clsx("block rounded-lg px-3 py-2 hover:bg-surface-2", isActive(item.href) && "bg-surface-2")}
              >
                <span className="block text-sm font-medium text-ink">{item.label}</span>
                <span className="block text-xs text-ink-2">{item.description}</span>
              </Link>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

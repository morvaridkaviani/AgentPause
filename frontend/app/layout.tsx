import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { SiteFooter } from "@/components/layout/page";
import { SiteHeader } from "@/components/layout/site-header";
import { THEME_SCRIPT } from "@/components/layout/theme-script";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "AgentPause", template: "%s · AgentPause" },
  description:
    "Research infrastructure and open-source toolkit for studying when AI agents should continue, clarify, ask, defer, or stop.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f9f9f7" },
    { media: "(prefers-color-scheme: dark)", color: "#0d0d0d" },
  ],
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body className="min-h-screen">
        <SiteHeader />
        <main id="main" className="pb-8">
          {children}
        </main>
        <SiteFooter />
      </body>
    </html>
  );
}

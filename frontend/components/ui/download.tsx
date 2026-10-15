"use client";

import { Download } from "lucide-react";
import { useState, type ReactNode } from "react";

import { downloadFile, downloadUrl } from "@/lib/api";
import { STATIC_DEMO } from "@/lib/site";

import { Button, ButtonLink } from "./primitives";

type Params = Record<string, string | number | boolean | undefined>;

/** An export link. With a server it is a plain download URL; in the static demo the file is built in the browser. */
export function DownloadButton({
  path,
  params = {},
  filename,
  variant = "secondary",
  children,
}: {
  path: string;
  params?: Params;
  filename: string;
  variant?: "primary" | "secondary" | "ghost";
  children: ReactNode;
}) {
  const [busy, setBusy] = useState(false);
  const icon = <Download className="size-4" aria-hidden />;
  if (!STATIC_DEMO) {
    return (
      <ButtonLink href={downloadUrl(path, params)} variant={variant} icon={icon}>
        {children}
      </ButtonLink>
    );
  }
  return (
    <Button
      variant={variant}
      icon={icon}
      loading={busy}
      onClick={async () => {
        setBusy(true);
        try {
          await downloadFile(path, params, filename);
        } finally {
          setBusy(false);
        }
      }}
    >
      {children}
    </Button>
  );
}

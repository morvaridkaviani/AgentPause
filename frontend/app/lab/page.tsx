import type { Metadata } from "next";

import { LabClient } from "@/components/lab/lab-client";

export const metadata: Metadata = { title: "Decision lab" };

export default function LabPage() {
  return <LabClient />;
}

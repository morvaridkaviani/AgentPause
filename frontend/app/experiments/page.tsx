import type { Metadata } from "next";

import { ExperimentsClient } from "@/components/research/experiments-client";

export const metadata: Metadata = { title: "Experiment runner" };

export default function ExperimentsPage() {
  return <ExperimentsClient />;
}

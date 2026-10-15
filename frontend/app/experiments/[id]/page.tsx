import type { Metadata } from "next";

import { ExperimentDetail } from "@/components/research/experiment-detail";

export const metadata: Metadata = { title: "Experiment" };

export default async function ExperimentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ExperimentDetail id={id} />;
}

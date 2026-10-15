import type { Metadata } from "next";
import { Suspense } from "react";

import { ExperimentFromQuery } from "@/components/research/experiment-detail";

export const metadata: Metadata = { title: "Experiment" };

/** /experiments/view?id=… (a query parameter, so the page also works as a static export). */
export default function ExperimentPage() {
  return (
    <Suspense fallback={null}>
      <ExperimentFromQuery />
    </Suspense>
  );
}

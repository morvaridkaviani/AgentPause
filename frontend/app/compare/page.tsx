import type { Metadata } from "next";
import { Suspense } from "react";

import { Container } from "@/components/layout/page";
import { CompareClient } from "@/components/research/compare-client";
import { Spinner } from "@/components/ui/primitives";

export const metadata: Metadata = { title: "Policy comparison" };

export default function ComparePage() {
  return (
    <Suspense fallback={<Container className="pt-10"><Spinner /></Container>}>
      <CompareClient />
    </Suspense>
  );
}

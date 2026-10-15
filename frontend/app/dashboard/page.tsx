import type { Metadata } from "next";
import { Suspense } from "react";

import { Container } from "@/components/layout/page";
import { DashboardClient } from "@/components/research/dashboard-client";
import { Spinner } from "@/components/ui/primitives";

export const metadata: Metadata = { title: "Research dashboard" };

export default function DashboardPage() {
  return (
    <Suspense fallback={<Container className="pt-10"><Spinner /></Container>}>
      <DashboardClient />
    </Suspense>
  );
}

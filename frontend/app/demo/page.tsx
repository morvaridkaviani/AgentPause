import type { Metadata } from "next";
import { Suspense } from "react";

import { DemoClient } from "@/components/demo/demo-client";
import { Container } from "@/components/layout/page";
import { Spinner } from "@/components/ui/primitives";

export const metadata: Metadata = { title: "Interactive demo" };

export default function DemoPage() {
  return (
    <Suspense
      fallback={
        <Container className="pt-10">
          <Spinner label="Loading the demo" />
        </Container>
      }
    >
      <DemoClient />
    </Suspense>
  );
}

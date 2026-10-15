import type { Metadata } from "next";
import { Suspense } from "react";

import { Container } from "@/components/layout/page";
import { EventsClient } from "@/components/research/events-client";
import { Spinner } from "@/components/ui/primitives";

export const metadata: Metadata = { title: "Event log" };

export default function EventsPage() {
  return (
    <Suspense fallback={<Container className="pt-10"><Spinner /></Container>}>
      <EventsClient />
    </Suspense>
  );
}

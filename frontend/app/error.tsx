"use client";

import { Container } from "@/components/layout/page";
import { ErrorState } from "@/components/ui/feedback";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <Container className="pt-16">
      <ErrorState error={error} onRetry={reset} title="This page failed to load" />
    </Container>
  );
}

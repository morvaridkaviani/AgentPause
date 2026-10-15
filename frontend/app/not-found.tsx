import { Container } from "@/components/layout/page";
import { ButtonLink } from "@/components/ui/primitives";

export default function NotFound() {
  return (
    <Container className="flex flex-col items-start gap-4 pt-16">
      <p className="text-sm font-semibold text-accent">404</p>
      <h1 className="text-3xl font-semibold text-ink">This page does not exist</h1>
      <p className="text-ink-2">The link may be outdated, or the experiment or session was deleted.</p>
      <ButtonLink href="/">Back to the start</ButtonLink>
    </Container>
  );
}

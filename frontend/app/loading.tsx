import { Container } from "@/components/layout/page";
import { Spinner } from "@/components/ui/primitives";

export default function Loading() {
  return (
    <Container className="pt-16">
      <Spinner label="Loading" />
    </Container>
  );
}

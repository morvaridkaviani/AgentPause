import type { Metadata } from "next";

import { StudyClient } from "@/components/study/study-client";

export const metadata: Metadata = { title: "Study" };

export default function StudyPage() {
  return <StudyClient />;
}

import type { Metadata } from "next";

import { StudyAdmin } from "@/components/study/study-admin";

export const metadata: Metadata = { title: "Study administration" };

export default function StudyAdminPage() {
  return <StudyAdmin />;
}

import type { Metadata } from "next";

import { PreferencesClient } from "@/components/research/preferences-client";

export const metadata: Metadata = { title: "Preferences" };

export default function PreferencesPage() {
  return <PreferencesClient />;
}

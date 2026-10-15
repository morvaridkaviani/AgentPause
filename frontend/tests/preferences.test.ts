import { act, renderHook } from "@testing-library/react";

import { DEFAULT_PREFERENCES, PREFERENCES_KEY, describePreferences, usePreferences } from "@/lib/preferences";

describe("preferences store", () => {
  beforeEach(() => localStorage.clear());

  it("persists updates and notifies subscribers", () => {
    const { result } = renderHook(() => usePreferences());
    const other = renderHook(() => usePreferences());
    act(() => result.current[1]({ ...DEFAULT_PREFERENCES, ask_before_external: true }));
    expect(result.current[0].ask_before_external).toBe(true);
    expect(other.result.current[0].ask_before_external).toBe(true);
    expect(JSON.parse(localStorage.getItem(PREFERENCES_KEY)!).ask_before_external).toBe(true);
  });

  it("summarises preferences in plain language", () => {
    expect(describePreferences({ ...DEFAULT_PREFERENCES, block_categories: ["data_deletion"], max_interruptions_per_task: 3 })).toEqual([
      "Balanced",
      "Blocked: 1 categories",
      "At most 3 interruptions per task",
    ]);
  });
});

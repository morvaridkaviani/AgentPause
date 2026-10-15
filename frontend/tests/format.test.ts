import { DECISION_META, DECISION_ORDER, level, num, pct, policyLabel, seconds, titleCase } from "@/lib/format";

describe("format helpers", () => {
  it("formats percentages and numbers, with a dash for missing values", () => {
    expect(pct(0.256)).toBe("26%");
    expect(pct(0.256, 1)).toBe("25.6%");
    expect(pct(null)).toBe("—");
    expect(pct(Number.NaN)).toBe("—");
    expect(num(1.23456)).toBe("1.23");
    expect(num(undefined)).toBe("—");
  });

  it("formats durations", () => {
    expect(seconds(42)).toBe("42 s");
    expect(seconds(125)).toBe("2 min 5 s");
  });

  it("maps values to levels per signal kind", () => {
    expect(level(0.9, "confidence")).toBe("HIGH");
    expect(level(0.7, "confidence")).toBe("MEDIUM");
    expect(level(0.2, "reversibility")).toBe("LOW");
    expect(level(0.7, "risk")).toBe("HIGH");
    expect(level(null, "risk")).toBe("—");
  });

  it("labels policies, falling back to readable names", () => {
    expect(policyLabel("adaptive")).toBe("Adaptive (AgentPause)");
    expect(policyLabel("my_custom_policy")).toBe("my custom policy");
    expect(titleCase("ask_human")).toBe("Ask Human");
  });

  it("has metadata for every decision type", () => {
    for (const d of DECISION_ORDER) expect(DECISION_META[d].label).toBeTruthy();
  });
});

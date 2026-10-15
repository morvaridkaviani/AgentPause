import type { Decision, InterventionCard, TimelineItem } from "@/lib/types";

export function makeDecision(overrides: Partial<Decision> = {}): Decision {
  return {
    decision: "ASK_HUMAN",
    score: 0.71,
    confidence: 0.94,
    policy: "adaptive",
    action: "book_flight",
    step: 3,
    reason_codes: ["IRREVERSIBLE", "HIGH_SEVERITY"],
    explanation: "Booking cannot be undone and the price exceeds what you approved.",
    recommended_intervention: "confirm",
    should_ask: true,
    questions: [],
    deferred: [],
    factors: [],
    counterfactuals: [],
    timing: {
      why_now: "This is the last moment before the booking becomes permanent.",
      why_not_earlier: "Earlier, the flight had not been chosen yet.",
      why_not_later: "Later, the booking could no longer be undone.",
      earlier: [],
      later: [],
    },
    item_timings: [],
    terms: {},
    signals: {},
    warnings: [],
    latency_ms: 1.2,
    ...overrides,
  };
}

export function makeCard(overrides: Partial<InterventionCard> = {}): InterventionCard {
  return {
    intervention_id: "iv-1",
    step_index: 3,
    decision: makeDecision(),
    action: {
      label: "Book flight",
      description: "Book the 08:10 flight to Lisbon for €412",
      category: "financial_transaction",
      consequence: "€412 is charged to the saved card (simulated).",
      undo: "Non-refundable fare.",
      reversible: false,
      recoverability: 0.1,
      severity: 0.7,
      what_could_go_wrong: "Wrong dates or a fare above your budget.",
      preview: { Date: "12 May", Price: "€412" },
      alternatives: ["Hold the fare for 24 hours"],
      requires_human_input: false,
      agent_confidence: 0.82,
      simulated: true,
    },
    assumptions: [],
    allowed_responses: ["approve", "edit", "reject", "ask_why", "cancel_task"],
    ...overrides,
  };
}

export function makeTimelineItem(overrides: Partial<TimelineItem> = {}): TimelineItem {
  return {
    seq: 1,
    step_index: 0,
    step_id: "search",
    label: "Search flights",
    description: "Look up flights for the requested dates",
    decision: "CONTINUE",
    score: 0.05,
    confidence: 1,
    risk_level: "low",
    signals: { agent_confidence: 0.95, intent_confidence: 0.9, severity: 0.05, recoverability: 1 },
    reason_codes: ["READ_ONLY"],
    explanation: "Read-only search.",
    n_questions: 0,
    deferred: [],
    response: null,
    executed: true,
    skipped: false,
    harm: null,
    decision_detail: null,
    ...overrides,
  };
}

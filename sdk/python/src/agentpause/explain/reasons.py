"""Reason codes: stable, machine-readable labels attached to every decision.

Codes are part of the public API and are logged in experiments. Rename only with a
deprecation note in CHANGELOG.md. Each code has a short phrase used to build
natural-language explanations.
"""

from __future__ import annotations

from enum import StrEnum


class ReasonCode(StrEnum):
    # Signals that push toward involving the human
    LOW_AGENT_CONFIDENCE = "LOW_AGENT_CONFIDENCE"
    LOW_INTENT_CONFIDENCE = "LOW_INTENT_CONFIDENCE"
    AMBIGUOUS_ASSUMPTION = "AMBIGUOUS_ASSUMPTION"
    HIGH_SEVERITY = "HIGH_SEVERITY"
    IRREVERSIBLE_ACTION = "IRREVERSIBLE_ACTION"
    EXTERNAL_CONSEQUENCE = "EXTERNAL_CONSEQUENCE"
    FINANCIAL_CONSEQUENCE = "FINANCIAL_CONSEQUENCE"
    PRIVACY_RISK = "PRIVACY_RISK"
    DATA_LOSS_RISK = "DATA_LOSS_RISK"
    COMMITMENT_POINT = "COMMITMENT_POINT"
    DEPENDENT_COMMITMENT = "DEPENDENT_COMMITMENT"
    AT_BREAKPOINT = "AT_BREAKPOINT"
    BATCHED_QUESTIONS = "BATCHED_QUESTIONS"
    USER_HISTORY_DISAGREES = "USER_HISTORY_DISAGREES"
    # Signals that push toward autonomy or toward waiting
    LOW_RISK_ACTION = "LOW_RISK_ACTION"
    READ_ONLY_ACTION = "READ_ONLY_ACTION"
    REVERSIBLE_ACTION = "REVERSIBLE_ACTION"
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    ASKING_NOT_WORTH_IT = "ASKING_NOT_WORTH_IT"
    USER_HISTORY_APPROVES = "USER_HISTORY_APPROVES"
    MID_TASK = "MID_TASK"
    HIGH_COGNITIVE_LOAD = "HIGH_COGNITIVE_LOAD"
    HABITUATION_RISK = "HABITUATION_RISK"
    DEFERRED_TO_BREAKPOINT = "DEFERRED_TO_BREAKPOINT"
    # Hard constraints
    CATASTROPHIC_RISK = "CATASTROPHIC_RISK"
    REQUIRES_HUMAN_INPUT = "REQUIRES_HUMAN_INPUT"
    # User preference rules
    USER_RULE_ALWAYS_ASK = "USER_RULE_ALWAYS_ASK"
    USER_RULE_NEVER_ASK = "USER_RULE_NEVER_ASK"
    USER_RULE_BLOCK = "USER_RULE_BLOCK"
    USER_RULE_IRREVERSIBLE = "USER_RULE_IRREVERSIBLE"
    USER_RULE_EXTERNAL = "USER_RULE_EXTERNAL"
    USER_RULE_LOW_RISK_AUTONOMY = "USER_RULE_LOW_RISK_AUTONOMY"
    INTERRUPTION_BUDGET_EXHAUSTED = "INTERRUPTION_BUDGET_EXHAUSTED"
    # Policy-specific
    POLICY_ALWAYS_CONFIRM = "POLICY_ALWAYS_CONFIRM"
    POLICY_FULL_AUTONOMY = "POLICY_FULL_AUTONOMY"
    RISK_ABOVE_THRESHOLD = "RISK_ABOVE_THRESHOLD"
    RISK_BELOW_THRESHOLD = "RISK_BELOW_THRESHOLD"
    CONFIDENCE_BELOW_THRESHOLD = "CONFIDENCE_BELOW_THRESHOLD"
    CONFIDENCE_ABOVE_THRESHOLD = "CONFIDENCE_ABOVE_THRESHOLD"
    RULE_IRREVERSIBLE_OR_EXTERNAL = "RULE_IRREVERSIBLE_OR_EXTERNAL"
    RULE_UNCERTAIN_REVERSIBLE = "RULE_UNCERTAIN_REVERSIBLE"
    LEARNED_MODEL_ABOVE_THRESHOLD = "LEARNED_MODEL_ABOVE_THRESHOLD"
    LEARNED_MODEL_BELOW_THRESHOLD = "LEARNED_MODEL_BELOW_THRESHOLD"
    # Data quality
    MISSING_SIGNAL_DEFAULTED = "MISSING_SIGNAL_DEFAULTED"
    CONTRADICTORY_SIGNALS = "CONTRADICTORY_SIGNALS"


PHRASES: dict[ReasonCode, str] = {
    ReasonCode.LOW_AGENT_CONFIDENCE: "the agent is not confident it is doing this correctly",
    ReasonCode.LOW_INTENT_CONFIDENCE: "your instruction did not clearly specify what you want here",
    ReasonCode.AMBIGUOUS_ASSUMPTION: "the agent had to guess part of what you meant",
    ReasonCode.HIGH_SEVERITY: "a mistake here would be costly",
    ReasonCode.IRREVERSIBLE_ACTION: "the action is difficult to undo",
    ReasonCode.EXTERNAL_CONSEQUENCE: "it affects people or systems outside this task",
    ReasonCode.FINANCIAL_CONSEQUENCE: "money is involved",
    ReasonCode.PRIVACY_RISK: "personal or confidential data would be shared",
    ReasonCode.DATA_LOSS_RISK: "data could be permanently lost",
    ReasonCode.COMMITMENT_POINT: "this is the last moment to check before a step that cannot be undone",
    ReasonCode.DEPENDENT_COMMITMENT: "a later step that cannot be undone depends on the answer",
    ReasonCode.AT_BREAKPOINT: "you are at a natural pause between parts of the task",
    ReasonCode.BATCHED_QUESTIONS: "several open questions could be combined into one interruption",
    ReasonCode.USER_HISTORY_DISAGREES: "you have corrected the agent on similar actions before",
    ReasonCode.LOW_RISK_ACTION: "a mistake here would be cheap",
    ReasonCode.READ_ONLY_ACTION: "the action only reads information and changes nothing",
    ReasonCode.REVERSIBLE_ACTION: "the action can easily be undone",
    ReasonCode.HIGH_CONFIDENCE: "the agent is confident and your intent is clear",
    ReasonCode.ASKING_NOT_WORTH_IT: "interrupting you would cost more than the risk it removes",
    ReasonCode.USER_HISTORY_APPROVES: "you have consistently approved similar actions",
    ReasonCode.MID_TASK: "you are in the middle of a sub-task, so interrupting now is more disruptive",
    ReasonCode.HIGH_COGNITIVE_LOAD: "you appear to be busy, so interrupting now is more disruptive",
    ReasonCode.HABITUATION_RISK: "you have been interrupted often recently, which makes each prompt less effective",
    ReasonCode.DEFERRED_TO_BREAKPOINT: "the question can safely wait for a better moment",
    ReasonCode.CATASTROPHIC_RISK: "the action is high-stakes, cannot be undone, and is probably wrong",
    ReasonCode.REQUIRES_HUMAN_INPUT: "the step needs something only you can provide",
    ReasonCode.USER_RULE_ALWAYS_ASK: "you asked to always be consulted for this kind of action",
    ReasonCode.USER_RULE_NEVER_ASK: "you allowed this kind of action to run without asking",
    ReasonCode.USER_RULE_BLOCK: "you disallowed this kind of action",
    ReasonCode.USER_RULE_IRREVERSIBLE: "you asked to be consulted before irreversible actions",
    ReasonCode.USER_RULE_EXTERNAL: "you asked to be consulted before external communication",
    ReasonCode.USER_RULE_LOW_RISK_AUTONOMY: "you allowed low-risk actions to run autonomously",
    ReasonCode.INTERRUPTION_BUDGET_EXHAUSTED: "the interruption budget you set for this task is used up",
    ReasonCode.POLICY_ALWAYS_CONFIRM: "the always-confirm policy asks before every meaningful action",
    ReasonCode.POLICY_FULL_AUTONOMY: "the full-autonomy policy never asks",
    ReasonCode.RISK_ABOVE_THRESHOLD: "the action's risk is above the fixed threshold",
    ReasonCode.RISK_BELOW_THRESHOLD: "the action's risk is below the fixed threshold",
    ReasonCode.CONFIDENCE_BELOW_THRESHOLD: "confidence is below the fixed threshold",
    ReasonCode.CONFIDENCE_ABOVE_THRESHOLD: "confidence is above the fixed threshold",
    ReasonCode.RULE_IRREVERSIBLE_OR_EXTERNAL: "the rules require confirmation for irreversible or external actions",
    ReasonCode.RULE_UNCERTAIN_REVERSIBLE: "the action is reversible but the agent is unsure",
    ReasonCode.LEARNED_MODEL_ABOVE_THRESHOLD: "the learned model predicts that intervention is likely needed",
    ReasonCode.LEARNED_MODEL_BELOW_THRESHOLD: "the learned model predicts that intervention is unlikely to be needed",
    ReasonCode.MISSING_SIGNAL_DEFAULTED: "some information was missing and default values were used",
    ReasonCode.CONTRADICTORY_SIGNALS: "some of the information provided was contradictory",
}

# Codes that describe data quality rather than a reason for the decision.
DATA_QUALITY_CODES = frozenset({ReasonCode.MISSING_SIGNAL_DEFAULTED, ReasonCode.CONTRADICTORY_SIGNALS})


def phrase(code: str) -> str:
    try:
        return PHRASES[ReasonCode(code)]
    except ValueError:
        return code.replace("_", " ").lower()

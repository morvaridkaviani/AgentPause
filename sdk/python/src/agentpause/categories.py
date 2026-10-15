"""Default priors per consequence category.

RESEARCH ASSUMPTION: these numbers are *documented priors chosen by the authors*, not
empirical measurements. They are used only when the caller does not supply ``severity`` /
``recoverability``, and every value used this way is tagged ``Provenance.DEFAULT``.

Scale conventions (used throughout the engine):

* ``severity`` ∈ [0, 1]: harm if the action is wrong and nobody intervenes, relative to the
  worst outcome the deployment cares about (1.0). Example anchors: a wrong web search ≈ 0.02;
  a wrong external email ≈ 0.45; a wrong €850 non-refundable purchase ≈ 0.8.
* ``recoverability`` ∈ [0, 1]: how completely a wrong action can be undone (1 = trivially,
  0 = not at all).

To calibrate these priors for a real deployment, replace them with labels from a risk dataset
(e.g. WebGuard's SAFE/LOW/HIGH labels) or with estimates from your own logged user decisions.
"""

from __future__ import annotations

from dataclasses import dataclass

from .types import ConsequenceCategory


@dataclass(frozen=True)
class CategoryPrior:
    severity: float
    recoverability: float
    external: bool
    description: str


CATEGORY_PRIORS: dict[ConsequenceCategory, CategoryPrior] = {
    ConsequenceCategory.READ_ONLY: CategoryPrior(0.02, 1.0, False, "Reads or searches; no side effects"),
    ConsequenceCategory.INTERNAL_DRAFT: CategoryPrior(0.05, 1.0, False, "Drafts or notes visible only to the user"),
    ConsequenceCategory.DATA_ENTRY: CategoryPrior(0.15, 0.9, False, "Fills in forms that are not yet submitted"),
    ConsequenceCategory.LOCAL_MODIFICATION: CategoryPrior(
        0.25, 0.8, False, "Changes local data that can usually be restored (move, rename, edit)"
    ),
    ConsequenceCategory.SCHEDULING: CategoryPrior(
        0.30, 0.6, True, "Calendar changes that notify other people; can be cancelled, but they will have seen it"
    ),
    ConsequenceCategory.EXTERNAL_COMMUNICATION: CategoryPrior(
        0.45, 0.05, True, "Messages that leave the user's control (email, chat, posts); cannot be unsent"
    ),
    ConsequenceCategory.ACCOUNT_CHANGE: CategoryPrior(0.50, 0.4, False, "Settings, subscriptions, permissions"),
    ConsequenceCategory.DATA_DELETION: CategoryPrior(0.60, 0.2, False, "Permanent deletion of user data"),
    ConsequenceCategory.DATA_SHARING: CategoryPrior(
        0.65, 0.05, True, "Disclosing personal or confidential data to third parties"
    ),
    ConsequenceCategory.FINANCIAL_TRANSACTION: CategoryPrior(
        0.80, 0.1, True, "Purchases, payments, bookings with money at stake"
    ),
    ConsequenceCategory.OTHER: CategoryPrior(0.30, 0.5, False, "Uncategorized action (neutral prior)"),
}

# Friendly aliases accepted by the SDK (e.g. ``consequence="external communication"``).
_ALIASES: dict[str, ConsequenceCategory] = {
    "read": ConsequenceCategory.READ_ONLY,
    "search": ConsequenceCategory.READ_ONLY,
    "draft": ConsequenceCategory.INTERNAL_DRAFT,
    "email": ConsequenceCategory.EXTERNAL_COMMUNICATION,
    "message": ConsequenceCategory.EXTERNAL_COMMUNICATION,
    "communication": ConsequenceCategory.EXTERNAL_COMMUNICATION,
    "external": ConsequenceCategory.EXTERNAL_COMMUNICATION,
    "payment": ConsequenceCategory.FINANCIAL_TRANSACTION,
    "purchase": ConsequenceCategory.FINANCIAL_TRANSACTION,
    "financial": ConsequenceCategory.FINANCIAL_TRANSACTION,
    "delete": ConsequenceCategory.DATA_DELETION,
    "deletion": ConsequenceCategory.DATA_DELETION,
    "share": ConsequenceCategory.DATA_SHARING,
    "privacy": ConsequenceCategory.DATA_SHARING,
    "calendar": ConsequenceCategory.SCHEDULING,
    "schedule": ConsequenceCategory.SCHEDULING,
    "form": ConsequenceCategory.DATA_ENTRY,
    "modify": ConsequenceCategory.LOCAL_MODIFICATION,
    "file": ConsequenceCategory.LOCAL_MODIFICATION,
    "settings": ConsequenceCategory.ACCOUNT_CHANGE,
    "account": ConsequenceCategory.ACCOUNT_CHANGE,
}


def parse_category(value: ConsequenceCategory | str | None) -> ConsequenceCategory:
    """Parse a category from an enum, its value, or a friendly alias.

    ``"external communication"``, ``"external_communication"`` and ``"EXTERNAL-COMMUNICATION"``
    all map to :attr:`ConsequenceCategory.EXTERNAL_COMMUNICATION`. Unknown values map to
    ``OTHER`` instead of raising, because the agent's vocabulary is open-ended.
    """
    if value is None:
        return ConsequenceCategory.OTHER
    if isinstance(value, ConsequenceCategory):
        return value
    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    try:
        return ConsequenceCategory(normalized)
    except ValueError:
        pass
    if normalized in _ALIASES:
        return _ALIASES[normalized]
    for token in normalized.split("_"):
        if token in _ALIASES:
            return _ALIASES[token]
    return ConsequenceCategory.OTHER


def prior_for(category: ConsequenceCategory) -> CategoryPrior:
    return CATEGORY_PRIORS[category]

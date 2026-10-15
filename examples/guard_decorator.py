"""Wrap a tool with ``guard`` so every call is checked by AgentPause first.

Run:  python examples/guard_decorator.py          (asks you in the terminal)
      python examples/guard_decorator.py --yes    (approves automatically, for CI)
"""

import sys

from agentpause import AgentPause
from agentpause.integrations.guard import ActionBlocked, ActionRejected, guard

AUTO_APPROVE = "--yes" in sys.argv
pause = AgentPause(policy="adaptive")


def ask_user(decision) -> bool:
    print(f"\nAgentPause: {decision.explanation}")
    if AUTO_APPROVE:
        print("(auto-approved)")
        return True
    return input("Approve? [y/N] ").strip().lower() == "y"


@guard(
    pause,
    signals={"consequence": "external_communication", "reversible": False},
    # Metadata only: never pass message bodies or secrets to AgentPause.
    context_fn=lambda to, body: {"description": f"Send an email to {to}", "agent_confidence": 0.8},
    on_ask=ask_user,
)
def send_email(to: str, body: str) -> str:
    return f"(simulated) sent {len(body)} characters to {to}"


@guard(pause, signals={"consequence": "read_only"})
def search_inbox(query: str) -> list[str]:
    return [f"(simulated) result for {query!r}"]


print(search_inbox("camera-ready deadline"))  # read-only: runs without asking
try:
    print(send_email("j.smith@uni.example", "Here is the revised draft."))
except ActionRejected:
    print("Not sent: you rejected it.")
except ActionBlocked as blocked:
    print(f"Blocked: {blocked}")

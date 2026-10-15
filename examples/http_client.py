"""Use the REST API from Python via the bundled HTTP client (stdlib only).

Start the server first:  uvicorn app.main:app --app-dir backend --port 8000
Run:                     python examples/http_client.py [http://localhost:8000]
"""

import sys

from agentpause import AgentPauseClient

client = AgentPauseClient(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000")
print("server:", client.health()["status"])

# Stateless evaluation of one action.
decision = client.evaluate(
    action="delete_files",
    consequence="data_deletion",
    reversible=False,
    agent_confidence=0.7,
    description="Delete 120 files in ~/Downloads older than 30 days",
)
print(decision.decision.value, "-", decision.explanation)

# A stateful session for your own agent: AgentPause keeps history (interruptions, plan, assumptions).
session = client.create_session(mode="api", policy="adaptive")
for action, consequence in [
    ("read_calendar", "read_only"),
    ("create_event", "scheduling"),
    ("send_invites", "external_communication"),
]:
    d = client.submit_action(session["id"], action, consequence=consequence, agent_confidence=0.85)
    print(f"{action:14s} -> {d.decision.value}")
    if d.should_ask:
        # Show the intervention to your user; here we approve on their behalf.
        client.submit_intervention(session["id"], "approve")
print("events logged:", len(client.get_events(session["id"])))

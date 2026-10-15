"""A minimal agent loop with AgentPause (no server needed).

Run:  python examples/python_quickstart.py

The "agent" here is a hard-coded plan for writing and sending an email. Before each step it
asks AgentPause whether to continue, ask the user, or schedule a question for later. All
actions are simulated: nothing is sent.
"""

from agentpause import AgentPause

pause = AgentPause(policy="adaptive")  # also: "always_confirm", "fixed_threshold", "full_autonomy", ...

# The agent had to interpret "send the slides to the team": which team?
pause.declare_assumption(
    "recipients",
    "'the team' means the project mailing list",
    confidence=0.6,
    options=["project mailing list", "whole department"],
    agent_value="project mailing list",
)

# The whole plan (with absolute step indices) lets AgentPause look ahead: it can wait to ask
# about "recipients" until just before the irreversible step that depends on it.
plan = [
    {"step": 0, "action": "find_slides", "consequence": "read_only", "at_breakpoint": True},
    {"step": 1, "action": "draft_email", "consequence": "internal_draft", "depends_on": ["recipients"]},
    {"step": 2, "action": "attach_slides", "consequence": "internal_draft", "at_breakpoint": True},
    {
        "step": 3,
        "action": "send_email",
        "consequence": "external_communication",
        "reversible": False,
        "depends_on": ["recipients"],
    },
]
pause.set_plan(plan)

for step in plan:
    decision = pause.evaluate(
        **step,
        agent_confidence=0.9,
        task_progress=step["step"] / len(plan),
    )
    print(f"\n[{step['action']}] {decision.decision.value}  (score {decision.score:.2f})")
    print("  " + decision.explanation)
    if decision.timing is not None:
        print("  why now:  " + decision.timing.why_now)

    if decision.should_ask:
        # A real agent would show an intervention card here. We approve and confirm the guess.
        answers = {q.assumption_id: q.agent_value for q in decision.questions if q.assumption_id and q.agent_value}
        pause.respond(decision, "answer" if answers else "approve", answers=answers)
        print(f"  user responded: {'answered ' + str(answers) if answers else 'approved'}")
    elif decision.deferred:
        for q in decision.deferred:
            print(f"  scheduled question ({q.description}) before step {q.target_step + 1}")

print("\nOpen questions still pending:", [q.assumption_id for q in pause.pending_questions])

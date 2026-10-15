"""EXAMPLE integration: AgentPause as a Claude Code ``PreToolUse`` hook.

Claude Code hooks receive a JSON event on stdin and may answer with a permission decision.
This adapter maps AgentPause decisions onto that vocabulary:

=================  ===========================================================
AgentPause         Claude Code ``permissionDecision``
=================  ===========================================================
CONTINUE, DEFER    ``allow``
CLARIFY, ASK       ``ask`` (the explanation is shown to the user in the prompt)
BLOCK              ``deny`` (the explanation is returned to the model)
=================  ===========================================================

Limitations (read before using):

* Tool → category mapping is a **coarse heuristic** over tool names and shell commands. It is
  not a security boundary; keep Claude Code's own permission rules and sandboxing.
* A hook cannot postpone a question to a later step, so DEFER maps to ``allow``.
* State (recent interruptions, user history) is kept per Claude Code session in
  ``~/.cache/agentpause/claude-code/``. Only action metadata is stored, never file contents.

Install (example ``.claude/settings.json``)::

    {"hooks": {"PreToolUse": [{"matcher": "*", "hooks": [
        {"type": "command", "command": "agentpause-claude-hook"}]}]}}
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from ..session import AgentPause
from ..types import ConsequenceCategory, DecisionType

_READ_TOOLS = {"Read", "Grep", "Glob", "LS", "WebSearch", "WebFetch", "TodoWrite", "NotebookRead"}
_EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
_DESTRUCTIVE = re.compile(
    r"\b(rm\s+-[a-z]*r|rm\s+-[a-z]*f|git\s+reset\s+--hard|git\s+clean|drop\s+table|truncate\s+table|mkfs|dd\s+if=)",
    re.I,
)
_EXTERNAL = re.compile(
    r"\b(git\s+push|npm\s+publish|twine\s+upload|curl\s+.*-X\s*(POST|PUT|DELETE)|gh\s+(pr|issue)\s+(create|comment|merge)|kubectl\s+(apply|delete)|terraform\s+apply)",
    re.I,
)
_READ_ONLY_CMD = re.compile(
    r"^\s*(ls|cat|head|tail|grep|rg|find|pwd|echo|git\s+(status|diff|log|show)|wc|which)\b", re.I
)


def classify(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """Map a Claude Code tool call to AgentPause signals (heuristic)."""
    if tool_name in _READ_TOOLS:
        return {"consequence": ConsequenceCategory.READ_ONLY, "agent_confidence": 0.95}
    if tool_name in _EDIT_TOOLS:
        return {"consequence": ConsequenceCategory.LOCAL_MODIFICATION, "recoverability": 0.8}
    if tool_name == "Bash":
        command = str(tool_input.get("command", ""))
        if _DESTRUCTIVE.search(command):
            return {"consequence": ConsequenceCategory.DATA_DELETION, "recoverability": 0.1, "severity": 0.7}
        if _EXTERNAL.search(command):
            return {"consequence": ConsequenceCategory.EXTERNAL_COMMUNICATION, "recoverability": 0.2, "severity": 0.5}
        if _READ_ONLY_CMD.search(command):
            return {"consequence": ConsequenceCategory.READ_ONLY}
        return {"consequence": ConsequenceCategory.LOCAL_MODIFICATION, "recoverability": 0.6}
    if tool_name.startswith("mcp__") and re.search(r"(send|post|create|delete|update|publish)", tool_name, re.I):
        return {"consequence": ConsequenceCategory.EXTERNAL_COMMUNICATION}
    return {"consequence": ConsequenceCategory.OTHER}


def _state_path(session_id: str) -> Path:
    base = Path(os.environ.get("AGENTPAUSE_CACHE_DIR", Path.home() / ".cache" / "agentpause" / "claude-code"))
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "default")
    return base / f"{safe}.json"


def handle(event: dict[str, Any], *, policy: str = "adaptive") -> dict[str, Any]:
    session_id = str(event.get("session_id", "default"))
    path = _state_path(session_id)
    pause = AgentPause(policy, explain="light")
    if path.exists():
        saved = AgentPause.from_dict(json.loads(path.read_text(encoding="utf-8")))
        if saved.policy.registry_key == pause.policy.registry_key:
            pause = saved
        else:
            # AGENTPAUSE_POLICY changed since the state file was created: keep the history, switch policy.
            pause.state = saved.state
    tool_name = str(event.get("tool_name", "unknown"))
    signals = classify(tool_name, dict(event.get("tool_input") or {}))
    decision = pause.evaluate(f"{tool_name}", description=f"Run {tool_name}", **signals)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pause.to_dict()), encoding="utf-8")

    if decision.decision in (DecisionType.CONTINUE, DecisionType.DEFER):
        permission = "allow"
    elif decision.decision == DecisionType.BLOCK:
        permission = "deny"
    else:
        permission = "ask"
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": permission,
            "permissionDecisionReason": f"[AgentPause] {decision.explanation}",
        }
    }


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # not our event; let Claude Code proceed with its own rules
    json.dump(handle(event, policy=os.environ.get("AGENTPAUSE_POLICY", "adaptive")), sys.stdout)


if __name__ == "__main__":
    main()

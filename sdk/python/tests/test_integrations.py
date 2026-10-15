import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from agentpause import AgentPauseAPIError, AgentPauseClient, ConsequenceCategory
from agentpause.integrations.claude_code import classify, handle


# ---------------------------------------------------------------- Claude Code hook adapter
@pytest.mark.parametrize(
    "tool,tool_input,category",
    [
        ("Read", {"file_path": "a.py"}, ConsequenceCategory.READ_ONLY),
        ("Edit", {"file_path": "a.py"}, ConsequenceCategory.LOCAL_MODIFICATION),
        ("Bash", {"command": "ls -la"}, ConsequenceCategory.READ_ONLY),
        ("Bash", {"command": "rm -rf build"}, ConsequenceCategory.DATA_DELETION),
        ("Bash", {"command": "git push origin main"}, ConsequenceCategory.EXTERNAL_COMMUNICATION),
        ("mcp__gmail__send_email", {}, ConsequenceCategory.EXTERNAL_COMMUNICATION),
        ("SomethingElse", {}, ConsequenceCategory.OTHER),
    ],
)
def test_classify(tool, tool_input, category):
    assert classify(tool, tool_input)["consequence"] == category


def test_hook_output_shape_and_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTPAUSE_CACHE_DIR", str(tmp_path))
    out = handle({"session_id": "abc", "tool_name": "Read", "tool_input": {}})
    spec = out["hookSpecificOutput"]
    assert spec["hookEventName"] == "PreToolUse"
    assert spec["permissionDecision"] == "allow"
    risky = handle(
        {"session_id": "abc", "tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}}
    )
    assert risky["hookSpecificOutput"]["permissionDecision"] in ("ask", "deny")
    assert risky["hookSpecificOutput"]["permissionDecisionReason"].startswith("[AgentPause]")
    assert (tmp_path / "abc.json").exists()
    stored = json.loads((tmp_path / "abc.json").read_text())
    assert len(stored["state"]["history"]) == 2


def test_hook_follows_a_changed_policy_setting(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTPAUSE_CACHE_DIR", str(tmp_path))
    handle({"session_id": "s", "tool_name": "Write", "tool_input": {"file_path": "notes.md"}}, policy="adaptive")
    out = handle(
        {"session_id": "s", "tool_name": "Write", "tool_input": {"file_path": "notes.md"}}, policy="always_confirm"
    )
    assert out["hookSpecificOutput"]["permissionDecision"] == "ask"
    stored = json.loads((tmp_path / "s.json").read_text())
    assert stored["policy"]["policy"] == "always_confirm"
    assert len(stored["state"]["history"]) == 2, "history is kept when the policy changes"


# ---------------------------------------------------------------- REST client (against a stub server)
class _Stub(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silence test output
        pass

    def _send(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/api/v1/health"):
            self._send(200, {"status": "ok", "auth": self.headers.get("Authorization")})
        elif self.path.startswith("/api/v1/metrics"):
            self._send(200, {"query": self.path})
        else:
            self._send(404, {"detail": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        if self.path == "/api/v1/evaluate":
            self._send(
                200,
                {
                    "decision": "ASK_HUMAN",
                    "score": 0.8,
                    "policy": body["policy"]["name"],
                    "action": body["context"]["action"],
                    "step": 0,
                },
            )
        else:
            self._send(422, {"detail": [{"msg": "bad"}]})


@pytest.fixture
def stub_url():
    server = HTTPServer(("127.0.0.1", 0), _Stub)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_client_requests(stub_url):
    client = AgentPauseClient(stub_url, token="secret")
    assert client.health()["auth"] == "Bearer secret"
    d = client.evaluate("send_email", policy="adaptive", consequence="external_communication")
    assert d.decision.value == "ASK_HUMAN" and d.action == "send_email"
    assert "scenario=email" in client.metrics(scenario="email", policy=None)["query"]


def test_client_errors(stub_url):
    client = AgentPauseClient(stub_url)
    with pytest.raises(AgentPauseAPIError) as err:
        client.create_session(policy="adaptive")
    assert err.value.status == 422
    with pytest.raises(AgentPauseAPIError) as err:
        client.get_session("nope")
    assert err.value.status == 404

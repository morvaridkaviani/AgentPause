"""REST client for an AgentPause server, using only the standard library."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .decision import Decision


class AgentPauseAPIError(RuntimeError):
    def __init__(self, status: int, detail: Any) -> None:
        super().__init__(f"AgentPause API error {status}: {detail}")
        self.status = status
        self.detail = detail


class AgentPauseClient:
    """Talk to a running AgentPause server (``uvicorn app.main:app``).

    >>> client = AgentPauseClient("http://localhost:8000")          # doctest: +SKIP
    >>> d = client.evaluate("send_email", consequence="external_communication",
    ...                     reversible=False, intent_confidence=0.72)  # doctest: +SKIP
    """

    def __init__(
        self, base_url: str = "http://localhost:8000", *, token: str | None = None, timeout: float = 15.0
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    # ---- low level ----------------------------------------------------------------------
    def request(self, method: str, path: str, body: Any = None, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as err:
            try:
                detail = json.loads(err.read() or b"{}").get("detail")
            except (ValueError, AttributeError):
                detail = err.reason
            raise AgentPauseAPIError(err.code, detail) from err

    def _object(self, method: str, path: str, body: Any = None, params: dict[str, Any] | None = None) -> dict[str, Any]:
        data = self.request(method, path, body, params)
        if not isinstance(data, dict):
            raise AgentPauseAPIError(200, f"expected a JSON object from {path}")
        return data

    def _list(self, method: str, path: str) -> list[dict[str, Any]]:
        data = self.request(method, path)
        if not isinstance(data, list):
            raise AgentPauseAPIError(200, f"expected a JSON array from {path}")
        return data

    # ---- endpoints ----------------------------------------------------------------------
    def health(self) -> dict[str, Any]:
        return self._object("GET", "/api/v1/health")

    def policies(self) -> list[dict[str, Any]]:
        return self._list("GET", "/api/v1/policies")

    def evaluate(
        self,
        action: str,
        *,
        policy: str = "adaptive",
        policy_config: dict[str, Any] | None = None,
        preferences: dict[str, Any] | None = None,
        explain: str = "full",
        **signals: Any,
    ) -> Decision:
        """Stateless evaluation of one action (``POST /api/v1/evaluate``)."""
        body = {
            "policy": {"name": policy, "config": policy_config or {}},
            "preferences": preferences,
            "explain": explain,
            "context": {"action": action, **signals},
        }
        return Decision.from_dict(self._object("POST", "/api/v1/evaluate", body))

    def create_session(self, **kwargs: Any) -> dict[str, Any]:
        """Create a session (``POST /api/v1/session``). See the API docs for fields."""
        return self._object("POST", "/api/v1/session", kwargs)

    def submit_action(self, session_id: str, action: str, **signals: Any) -> Decision:
        """Evaluate an action within a session (``POST /api/v1/action``)."""
        result = self._object(
            "POST", "/api/v1/action", {"session_id": session_id, "context": {"action": action, **signals}}
        )
        return Decision.from_dict(result["decision"])

    def submit_intervention(
        self,
        session_id: str,
        response: str,
        *,
        intervention_id: str | None = None,
        answers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        body = {
            "session_id": session_id,
            "intervention_id": intervention_id,
            "response": response,
            "answers": answers or {},
        }
        return self._object("POST", "/api/v1/intervention", body)

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._object("GET", f"/api/v1/session/{session_id}")

    def get_events(self, session_id: str) -> list[dict[str, Any]]:
        return self._list("GET", f"/api/v1/session/{session_id}/events")

    def metrics(self, **filters: Any) -> dict[str, Any]:
        return self._object("GET", "/api/v1/metrics", params=filters)

    def create_experiment(self, config: dict[str, Any]) -> dict[str, Any]:
        return self._object("POST", "/api/v1/experiments", config)

    def get_experiment(self, experiment_id: str) -> dict[str, Any]:
        return self._object("GET", f"/api/v1/experiments/{experiment_id}")

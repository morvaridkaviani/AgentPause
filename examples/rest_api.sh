#!/usr/bin/env bash
# REST API walkthrough with curl. Start the server first:
#   uvicorn app.main:app --app-dir backend --port 8000
# Usage: bash examples/rest_api.sh [base-url]      (needs curl; jq optional for pretty output)
set -euo pipefail
API="${1:-http://localhost:8000}/api/v1"
pretty() { if command -v jq >/dev/null; then jq "$@"; else cat; fi; }

echo "== 1. Stateless evaluation of one proposed action"
curl -sS -X POST "$API/evaluate" -H 'Content-Type: application/json' -d '{
  "policy": "adaptive",
  "context": {
    "action": "send_email",
    "description": "Send the drafted email to Professor Smith",
    "consequence": "external_communication",
    "reversible": false,
    "agent_confidence": 0.86,
    "intent_confidence": 0.72,
    "task_progress": 0.9
  }
}' | pretty '{decision, score, reason_codes, explanation}'

echo "== 2. A session for your own agent"
SESSION=$(curl -sS -X POST "$API/session" -H 'Content-Type: application/json' -d '{"mode": "api", "policy": "adaptive"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
echo "session $SESSION"

echo "== 3. Submit the agent's next action"
RESULT=$(curl -sS -X POST "$API/action" -H 'Content-Type: application/json' -d "{
  \"session_id\": \"$SESSION\",
  \"context\": {\"action\": \"purchase_ticket\", \"consequence\": \"financial_transaction\", \"reversible\": false, \"agent_confidence\": 0.8}
}")
echo "$RESULT" | pretty '{decision: .decision.decision, intervention_id, explanation: .decision.explanation}'

echo "== 4. Record the human's response (if AgentPause asked)"
INTERVENTION=$(echo "$RESULT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("intervention_id") or "")')
if [ -n "$INTERVENTION" ]; then
  curl -sS -X POST "$API/intervention" -H 'Content-Type: application/json' \
    -d "{\"session_id\": \"$SESSION\", \"intervention_id\": \"$INTERVENTION\", \"response\": \"approve\"}" \
    | pretty '{status: .session.status}'
fi

echo "== 5. Session events and aggregate metrics"
curl -sS "$API/session/$SESSION/events" | pretty 'map({seq, type, decision, user_response})'
curl -sS "$API/metrics?source=sessions" | pretty '{n_episodes, note}'

echo "== 6. A small simulated experiment (runs in the background)"
EXP=$(curl -sS -X POST "$API/experiments" -H 'Content-Type: application/json' -d '{
  "name": "curl-demo", "scenarios": ["email"], "policies": ["always_confirm", "adaptive"], "episodes": 20, "seed": 1
}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
for _ in $(seq 1 30); do
  STATUS=$(curl -sS "$API/experiments/$EXP" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')
  [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ] && break
  sleep 1
done
curl -sS "$API/experiments/$EXP" | pretty '{status, result_hash: .result.result_hash, note: .result.note, interventions: [.result.aggregates[] | {policy, interventions, harm}]}'
echo "Interactive API docs: ${1:-http://localhost:8000}/docs"

# @agentpause/sdk

Typed TypeScript/JavaScript client for the **AgentPause** REST API. AgentPause decides when an AI
agent should keep going on its own and when it should pause and involve a human.

- Covers every public endpoint under `/api/v1`: evaluation, sessions, interventions, live events,
  metrics, experiments, and study mode.
- `guard()` helper that runs a function only when AgentPause allows it, and asks the human first
  when needed.
- No runtime dependencies. Uses the global `fetch`. ESM only. Ships with type declarations.

> **AgentPause is not a security boundary.** It decides *when to involve a human*. It does not
> sandbox, authorize, or audit what your agent does. Keep your own permission checks, sandboxing,
> and least-privilege credentials, and treat its decisions as advice about timing.

## Install

The package is **not published to npm yet**. Install it from this repository.

Inside this monorepo, npm workspaces already link it:

```bash
npm install                               # at the repository root
npm run build --workspace sdk/typescript  # emits sdk/typescript/dist
```

```ts
import { AgentPauseClient } from "@agentpause/sdk";
```

From another project, build it first, then install from the local path (or from a tarball made
with `npm pack`):

```bash
cd /path/to/AgentPause/sdk/typescript && npm run build
cd /path/to/your-project && npm install /path/to/AgentPause/sdk/typescript
```

Requirements: Node.js 18+ (or any runtime with `fetch`: browsers, Deno, Bun), and a running
AgentPause server:

```bash
uvicorn app.main:app --reload --app-dir backend   # http://localhost:8000, docs at /docs
```

## Quick start

```ts
import { AgentPauseClient, shouldProceed } from "@agentpause/sdk";

const client = new AgentPauseClient({ baseUrl: "http://localhost:8000" });

const decision = await client.evaluate({
  action: "send_email",
  description: "Send the drafted email to Professor Smith",
  consequence: "external_communication",
  reversible: false,
  intent_confidence: 0.72,
  agent_confidence: 0.86,
  provenance: { intent_confidence: "estimated" },
});

console.log(decision.decision);    // e.g. "ASK_HUMAN"
console.log(decision.explanation); // plain-language reason
console.log(decision.factors);     // each signal's contribution
console.log(decision.timing?.why_now);
if (shouldProceed(decision)) {
  // CONTINUE or DEFER: run the action
}
```

`evaluate()` is stateless and stores nothing. Only `action` is required. Missing signals fall back
to documented category priors, and the decision lists them in `signals.missing`. Unit-interval
signals (`severity`, `recoverability`, `agent_confidence`, `intent_confidence`, `task_progress`,
`cognitive_load`) must be in `[0, 1]`.

**Send metadata only.** Never send passwords, tokens, or private message content to AgentPause.

## Decision types

| Decision    | Meaning                                                                                       | What your agent should do                                             |
| ----------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `CONTINUE`  | Low enough risk and uncertainty to act autonomously.                                          | Run the action.                                                       |
| `CLARIFY`   | An intent assumption is worth checking before acting. `decision.questions` lists the questions. | Ask the questions and record the answers (`response: "answer"`).      |
| `ASK_HUMAN` | The human should approve, edit, or reject this specific action.                               | Show the action and explanation, then wait for approval.             |
| `DEFER`     | The action is reversible. A question was scheduled for a later, better moment (`decision.deferred`). | Run the action now. AgentPause asks before the first irreversible action that depends on it. |
| `BLOCK`     | Hard constraint or unacceptable risk.                                                         | Do not run it. Hand control back to the human (`takeover`/`override`). |

Helpers: `shouldProceed(d)` (CONTINUE/DEFER), `shouldAsk(d)` (CLARIFY/ASK_HUMAN), `isBlocked(d)`,
`interrupts(d)` (CLARIFY/ASK_HUMAN/BLOCK).

## Sessions for your own agent

An `api` session keeps history on the server: recent interruptions (habituation), open
assumptions, deferred questions, and the human's responses.

```ts
const session = await client.createSession({ mode: "api", policy: "adaptive" });

const { decision, intervention_id } = await client.submitAction(session.id, {
  action: "book_flight",
  consequence: "financial_transaction",
  reversible: false,
  assumptions: [{ id: "dates", description: "Travel May 3-7", confidence: 0.6, kind: "input" }],
});

if (intervention_id) {
  // The session now waits for the human. Record their response before the next action.
  await client.respond(session.id, "answer", {
    interventionId: intervention_id,
    answers: { dates: "May 4-8" },
  });
}
```

Responses: `approve`, `edit`, `reject`, `answer` (with `answers`), `takeover` / `override` (after
BLOCK), `cancel_task`, `timeout`, and `ask_why`. `ask_why` is logged but leaves the intervention
pending.

## `guard()`: gate a function

```ts
import { ActionBlockedError, ActionRejectedError, guard } from "@agentpause/sdk";

try {
  const receipt = await guard(
    client,
    session.id, // or { sessionId }, or evaluate options such as { policy: "adaptive" } for stateless use
    { action: "send_email", consequence: "external_communication", reversible: false, intent_confidence: 0.7 },
    () => sendEmail(draft), // runs only if allowed
    {
      onAsk: async (decision, { interventionId }) => {
        const ok = await ui.confirm(decision.explanation, decision.questions);
        return ok; // true → "approve", false → "reject"; or a response name, or { response: "answer", answers }
      },
    },
  );
} catch (err) {
  if (err instanceof ActionBlockedError) { /* BLOCK: hand control back to the human */ }
  else if (err instanceof ActionRejectedError) { /* the human said no: err.response */ }
  else throw err;
}
```

This mirrors the Python SDK's `agentpause.integrations.guard`:

| Decision              | `guard()` behavior                                                                                                        |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `CONTINUE`, `DEFER`   | Runs `fn` and returns its result.                                                                                          |
| `CLARIFY`, `ASK_HUMAN`| Calls `onAsk`. In session mode it records the response with `POST /api/v1/intervention`. `approve`, `edit`, `answer`, and `override` run `fn`. Any other response throws `ActionRejectedError`. Without `onAsk` it throws `InterventionRequiredError`. |
| `BLOCK`               | Throws `ActionBlockedError` and does not call `fn` or `onAsk`.                                                            |

All guard errors extend `AgentPauseGuardError` and carry `decision`, `sessionId`, and
`interventionId`. In session mode, `ActionBlockedError` and `InterventionRequiredError` leave the
intervention pending on the server. Resolve it with
`client.respond(err.sessionId, response, { interventionId: err.interventionId })` before you
submit the next action. In stateless mode (evaluate options as the target), nothing is recorded.

`withGuard()` wraps a function once, like the Python `@pause.guard(...)` decorator:

```ts
import { withGuard } from "@agentpause/sdk";

const sendEmail = withGuard(
  client,
  session.id,
  {
    signals: { consequence: "external_communication", reversible: false },
    contextFn: (to: string, body: string, confidence: number) => ({ agent_confidence: confidence }), // metadata only
    onAsk,
  },
  async function sendEmail(to: string, body: string, confidence: number) { /* ... */ },
);
await sendEmail("prof@example.edu", draft, 0.8); // action name defaults to the function name
```

## Client options and errors

```ts
const client = new AgentPauseClient({
  baseUrl: "http://localhost:8000", // default
  token: process.env.AGENTPAUSE_ADMIN_TOKEN, // sent as "Authorization: Bearer <token>"
  fetch: customFetch,               // default: global fetch
  timeoutMs: 15_000,                // default; 0 disables the timeout
});

await client.health({ signal: controller.signal, timeoutMs: 2_000 }); // per-request overrides
```

When `AGENTPAUSE_ADMIN_TOKEN` is set on the server, the researcher endpoints require the token:
`listSessions`, `deleteSession`, `listEvents`, `exportEventsCsv`, `exportExperiment`,
`deleteExperiment`, `updateStudyConfig`, and `exportStudy`. All other endpoints are open.

| Error                        | When                                                                                                                       |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `AgentPauseError`            | Non-2xx response. `status` is the HTTP status. `detail` is the server's `detail` (a string, or a list of `{ loc, msg }` for 422). |
| `AgentPauseTimeoutError`     | The request exceeded `timeoutMs`, or `waitForExperiment` exceeded `maxWaitMs`. `status` is 0.                             |
| `AgentPauseConnectionError`  | The server could not be reached. `status` is 0, and `cause` holds the underlying error.                                   |

Both subclasses extend `AgentPauseError`. If you abort a request with your own `signal`, it
rejects with the signal's reason.

## API reference

| Method                                         | HTTP                                              |
| ---------------------------------------------- | ------------------------------------------------- |
| `health()`                                     | `GET /api/v1/health`                              |
| `policies()`                                   | `GET /api/v1/policies`                            |
| `model()`                                      | `GET /api/v1/model`                               |
| `scenarios()`                                  | `GET /api/v1/scenarios`                           |
| `getScenario(id)`                              | `GET /api/v1/scenarios/{id}`                      |
| `evaluate(context, { policy, preferences, explain, state })` | `POST /api/v1/evaluate`             |
| `createSession(body)`                          | `POST /api/v1/session`                            |
| `getSession(id)`                               | `GET /api/v1/session/{id}`                        |
| `sessionEvents(id, { since })`                 | `GET /api/v1/session/{id}/events`                 |
| `streamSession(id, { since, signal })`         | `GET /api/v1/session/{id}/stream` (SSE, async iterator) |
| `stepSession(id, until)`                       | `POST /api/v1/session/{id}/step`                  |
| `submitAction(sessionId, context)`             | `POST /api/v1/action`                             |
| `respond(sessionId, response, { interventionId, answers })` | `POST /api/v1/intervention`          |
| `listSessions(filters)`                        | `GET /api/v1/sessions`                            |
| `deleteSession(id)`                            | `DELETE /api/v1/session/{id}`                     |
| `listEvents(filters)`                          | `GET /api/v1/events`                              |
| `exportEventsCsv(filters)`                     | `GET /api/v1/events?format=csv`                   |
| `metrics(filters)`                             | `GET /api/v1/metrics`                             |
| `compare(body)`                                | `POST /api/v1/compare`                            |
| `createExperiment(body, { wait })`             | `POST /api/v1/experiments`                        |
| `listExperiments({ limit })`                   | `GET /api/v1/experiments`                         |
| `getExperiment(id)`                            | `GET /api/v1/experiments/{id}`                    |
| `waitForExperiment(id, { pollIntervalMs, maxWaitMs })` | polls `GET /api/v1/experiments/{id}`      |
| `exportExperiment(id, { table, format })`      | `GET /api/v1/experiments/{id}/export`             |
| `deleteExperiment(id)`                         | `DELETE /api/v1/experiments/{id}`                 |
| `getStudyConfig()`                             | `GET /api/v1/study/config`                        |
| `updateStudyConfig(config)`                    | `PUT /api/v1/study/config`                        |
| `createParticipant()`                          | `POST /api/v1/study/participants`                 |
| `getParticipant(code)`                         | `GET /api/v1/study/participants/{code}`           |
| `updateParticipant(code, update)`              | `PATCH /api/v1/study/participants/{code}`         |
| `startStudySession(code, block)`               | `POST /api/v1/study/sessions`                     |
| `instruments()`                                | `GET /api/v1/study/instruments`                   |
| `submitQuestionnaire(body)`                    | `POST /api/v1/study/responses`                    |
| `exportStudy({ format })`                      | `GET /api/v1/study/export`                        |
| `request(method, path, { body, query, responseType })` | any endpoint (low level)                  |

Every method also accepts `signal` and `timeoutMs`. Request and response field names match the API
(snake_case), so the interactive docs at `/docs` apply directly.

Live events:

```ts
for await (const event of client.streamSession(session.id)) {
  console.log(event.seq, event.type, event.decision);
}
```

Experiments and comparisons run the bundled simulator. Their results are **simulated**. They were
not evaluated with human participants.

```ts
const experiment = await client.createExperiment({ name: "pilot", policies: ["adaptive", "always_confirm"], episodes: 50 });
const done = await client.waitForExperiment(experiment.id, { maxWaitMs: 120_000 });
const metrics = await client.metrics({ experiment_id: done.id });
```

## Development

```bash
npm run build      # tsc -p tsconfig.build.json → dist/
npm run typecheck  # tsc --noEmit (sources and tests)
npm run lint       # tsc --noEmit -p tsconfig.json
npm test           # vitest run (mocked fetch, no server needed)
```

## License

MIT

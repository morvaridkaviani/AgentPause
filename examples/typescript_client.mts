/**
 * Use AgentPause from TypeScript (Node 22.18+ runs TypeScript files directly).
 *
 *   npm install && npm run build --workspace sdk/typescript
 *   uvicorn app.main:app --app-dir backend --port 8000
 *   node examples/typescript_client.mts [http://localhost:8000]
 *
 * All actions are simulated: nothing is sent, bought, or deleted.
 */
import { ActionRejectedError, AgentPauseClient, guard } from "@agentpause/sdk";

const client = new AgentPauseClient({ baseUrl: process.argv[2] ?? "http://localhost:8000" });

// 1. Stateless: ask whether one proposed action needs the human.
const decision = await client.evaluate({
  action: "send_email",
  description: "Send the drafted reply to Professor Smith",
  consequence: "external_communication",
  reversible: false,
  agent_confidence: 0.86,
  intent_confidence: 0.72,
  provenance: { intent_confidence: "estimated" },
});
console.log(`${decision.decision}: ${decision.explanation}`);
if (decision.timing) console.log(`why now: ${decision.timing.why_now}`);

// 2. In a session: guard each tool call. AgentPause keeps the history (interruptions, plan).
const session = await client.createSession({ mode: "api", policy: "adaptive" });

const searchResults = await guard(client, session.id, { action: "search_flights", consequence: "read_only" }, () => [
  "(simulated) BER→VIE 08:10, €189",
]);
console.log("search:", searchResults);

try {
  const receipt = await guard(
    client,
    session.id,
    { action: "purchase_ticket", consequence: "financial_transaction", reversible: false, agent_confidence: 0.8 },
    () => "(simulated) ticket purchased",
    {
      // Show your own intervention UI here. This example approves automatically.
      onAsk: (d) => {
        console.log(`AgentPause asks: ${d.explanation}`);
        return "approve";
      },
    },
  );
  console.log(receipt);
} catch (error) {
  if (error instanceof ActionRejectedError) console.log("Not purchased: the user rejected it.");
  else throw error;
}

const events = await client.sessionEvents(session.id);
console.log(`${events.length} events logged for session ${session.id}`);

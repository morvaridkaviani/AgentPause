# Examples

Each example is short and runnable. Every action is simulated: nothing is sent, bought, or deleted.

| File | What it shows | Needs the server? |
|---|---|---|
| [python_quickstart.py](python_quickstart.py) | An agent loop with a plan and an assumption. AgentPause defers the clarification to the irreversible step and batches it with the approval | No |
| [guard_decorator.py](guard_decorator.py) | Wrapping tools with `@guard` so every call is checked first (`--yes` auto-approves) | No |
| [http_client.py](http_client.py) | The Python HTTP client: stateless evaluation and a session for your own agent | Yes |
| [rest_api.sh](rest_api.sh) | The REST API with curl: evaluate, session, action, intervention, events, metrics, experiments | Yes |
| [typescript_client.mts](typescript_client.mts) | The TypeScript SDK: `evaluate` and `guard` in a session | Yes |
| [claude_code_settings.json](claude_code_settings.json) | Using AgentPause as a Claude Code `PreToolUse` hook (`agentpause-claude-hook`) | No |

Start the server for the examples that need it:

```bash
uvicorn app.main:app --app-dir backend --port 8000
```

Run them from the repository root:

```bash
python examples/python_quickstart.py
python examples/guard_decorator.py --yes
python examples/http_client.py
bash examples/rest_api.sh
npm run build --workspace sdk/typescript && node examples/typescript_client.mts
```

## Claude Code hook

[`claude_code_settings.json`](claude_code_settings.json) goes in your project's `.claude/settings.json`. It registers the hook installed by `pip install -e sdk/python`. Choose the policy with `AGENTPAUSE_POLICY` (default `adaptive`).

The hook classifies tools with a coarse heuristic. It is **not a security boundary**, so keep Claude Code's own permission rules and sandboxing. A hook cannot postpone a question to a later step, so DEFER maps to `allow`. See [docs/sdk.md](../docs/sdk.md).

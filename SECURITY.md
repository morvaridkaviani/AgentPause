# Security Policy

## Scope and threat model

AgentPause is a **research toolkit and simulator**. It is designed for:

- running simulated agent scenarios, in which every "purchase", "email", "deletion", and
  "booking" is fake and labelled as simulated;
- evaluating intervention policies offline;
- running user studies with pseudonymous participants.

AgentPause is **not** a security boundary. Its decision engine estimates whether asking
a human is *worthwhile*. It is not an access-control system, sandbox, or prompt-injection
defense. If you embed AgentPause in a real agent, also enforce permissions with a proper
authorization layer, sandbox tool execution, and validate tool inputs. A `CONTINUE`
decision is never proof that an action is safe.

## Data handling

- The default configuration stores only synthetic scenario data and pseudonymous
  participant codes in a local SQLite database.
- The API rejects nothing by content, so do not send passwords, tokens, financial
  credentials, or private message bodies to it. The SDK's `AgentPause.evaluate()` only
  needs *metadata* about an action (category, reversibility, confidences), not its content.
- Exports (CSV/JSON) contain no personally identifiable information by design. Do not add
  identifiers to participant codes.

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Report vulnerabilities privately through GitHub's
[private vulnerability reporting](https://github.com/morvaridkaviani/AgentPause/security/advisories/new)
on the repository. Include:

1. a description of the issue and its impact;
2. steps to reproduce, or a proof of concept;
3. affected versions and configuration.

We aim to acknowledge reports within 7 days and to publish a fix or mitigation within
90 days, coordinated with the reporter.

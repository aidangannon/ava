# AVA

Autonomous coding agent.

- Receives commands via SQS
- Stores job state and checkpoints in local SQLite
- Raises PRs on completion
- Pauses and asks for human input when blocked

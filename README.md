# AVA

Local GitHub issue agent. Polls assigned issues, runs Claude Code on each one, and manages its own PRs.

The Python automation layer only does two things: detects events (a new assigned issue, a reply from the repo owner, new PR activity) and invokes the agent. Everything that actually touches GitHub — raising a PR, pushing a branch, commenting, replying to review comments, merging, closing the issue — is done by the agent itself via the `gh` CLI (or the GitHub MCP server, if configured), as declared in `ava/skill/ava.md`. Resolving review threads is the repo owner's call, not the agent's — the agent only replies once it has addressed a comment.

The agent's stdout only needs two tags: `[HISTORY]` (a short cache of decisions and open questions — not a changelog, git and GitHub already have that) and `[STATUS]` (`NEEDS_INPUT`, `IN_REVIEW`, or `DONE`), parsed in `ava/application/stdout.py`. Mapping `[STATUS]` to the next state and validating the transition is legal (e.g. SEARCHING can't jump straight to DONE — it has to go through REVIEW) is each state handler's own responsibility, via a `VALID_STATES` set in `ava/application/states/*.py`.

## States

Transitions:

SEARCHING → SEARCHING — no issue found, keep looking
SEARCHING → PENDING — issue found but agent needs context from the user before proceeding
SEARCHING → REVIEW — agent completed work and raised a PR itself
PENDING → PENDING — more input needed, still waiting
PENDING → REVIEW — context provided, agent resumes and updates/raises the PR itself
REVIEW → REVIEW — PR has unresolved comments that need to be addressed
REVIEW → PENDING — agent needs more context from the user before continuing
REVIEW → SEARCHING — PR approved; agent merged it, closed the issue, and history was cleared

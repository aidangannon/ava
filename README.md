# AVA

Local GitHub issue agent. Polls assigned issues every 5 minutes, runs Claude Code on each one, and raises a PR when done.

## States

Transitions:

SEARCHING → SEARCHING — no issue found, keep looking
SEARCHING → PENDING — issue found but agent needs context from the user before proceeding
SEARCHING → REVIEW — agent completed work and raised a PR
PENDING → PENDING — more input needed, still waiting
PENDING → REVIEW — context provided, agent resumes and updates/raises PR
REVIEW → REVIEW — PR has comments that need to be addressed
REVIEW → DONE — PR approved, work complete

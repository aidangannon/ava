from ava.crosscutting.result import Ok, Result
from ava.application.model import History
from ava.crosscutting.config import Config
from ava.application import ports, states

HISTORY = "[HISTORY]"
STATUS = "[STATUS]"

ALL_TAGS = [HISTORY, STATUS]

NEEDS_INPUT = "NEEDS_INPUT"
IN_REVIEW = "IN_REVIEW"
DONE = "DONE"

VALID_STATUSES = {NEEDS_INPUT, IN_REVIEW, DONE}


def _extract(stdout: str, tag: str) -> str | None:
    if tag not in stdout:
        return None
    content = stdout.split(tag, 1)[1]
    for other in ALL_TAGS:
        if other != tag and other in content:
            content = content.split(other, 1)[0]
    return content.strip() or None


def handle(config: Config, issue: str, stdout: str) -> Result:
    """
    The agent owns every GitHub write (PRs, replies, resolving comments,
    merging, closing) via the GitHub MCP/CLI, declared in the skill.
    All that's left for the automation layer is: cache the decision
    history to disk, and move the state machine on based on [STATUS].
    """
    history = _extract(stdout, HISTORY)
    if not history:
        raise Exception(f"Invalid stdout: [HISTORY] missing or empty\n{stdout}")

    ports.config_repository.add_history(
        History(issue=issue, repository=config.repo, content=history)
    )

    status = _extract(stdout, STATUS)
    if status not in VALID_STATUSES:
        raise Exception(f"Invalid stdout: [STATUS] missing or not one of {sorted(VALID_STATUSES)}\n{stdout}")

    if status == DONE:
        ports.config_repository.clear_history().throw_if_failed()
        ports.config_repository.set_state(states.SEARCHING).throw_if_failed()
    elif status == NEEDS_INPUT:
        ports.config_repository.set_state(states.PENDING).throw_if_failed()
    else:
        ports.config_repository.set_state(states.REVIEW).throw_if_failed()

    return Ok()

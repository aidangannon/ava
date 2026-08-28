from ava.crosscutting.result import Ok, Result
from ava.application.model import History
from ava.crosscutting.config import Config
from ava.application import ports, states

HISTORY = "[HISTORY]"
STATUS = "[STATUS]"

NEEDS_INPUT = "NEEDS_INPUT"
IN_REVIEW = "IN_REVIEW"
DONE = "DONE"

VALID_STATUSES = {NEEDS_INPUT, IN_REVIEW, DONE}


def _extract(stdout: str, tag: str, other_tag: str) -> str | None:
    if tag not in stdout:
        return None
    content = stdout.split(tag, 1)[1]
    if other_tag in content:
        content = content.split(other_tag, 1)[0]
    return content.strip() or None


def handle(config: Config, issue: str, stdout: str) -> Result:
    history = _extract(stdout, HISTORY, STATUS)
    if not history:
        raise Exception(f"Invalid stdout: [HISTORY] missing or empty\n{stdout}")

    ports.config_repository.add_history(
        History(issue=issue, repository=config.repo, content=history)
    )

    status = _extract(stdout, STATUS, HISTORY)
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

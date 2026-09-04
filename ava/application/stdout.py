from ava.application import states

HISTORY = "[HISTORY]"
STATUS = "[STATUS]"

NEEDS_INPUT = "NEEDS_INPUT"
IN_REVIEW = "IN_REVIEW"
DONE = "DONE"

_STATUS_TO_STATE = {
    NEEDS_INPUT: states.PENDING,
    IN_REVIEW: states.REVIEW,
    DONE: states.SEARCHING,
}


def _extract(text: str, tag: str, other_tag: str) -> str | None:
    if tag not in text:
        return None
    content = text.split(tag, 1)[1]
    if other_tag in content:
        content = content.split(other_tag, 1)[0]
    return content.strip() or None


def parse(stdout: str) -> tuple[str, str]:
    """Parses the agent's stdout into (history, target_state). Each state handler decides whether target_state is a valid transition for itself."""
    history = _extract(stdout, HISTORY, STATUS)
    if not history:
        raise Exception(f"Invalid stdout: [HISTORY] missing or empty\n{stdout}")

    status = _extract(stdout, STATUS, HISTORY)
    if status not in _STATUS_TO_STATE:
        raise Exception(f"Invalid stdout: [STATUS] missing or not one of {sorted(_STATUS_TO_STATE)}\n{stdout}")

    return history, _STATUS_TO_STATE[status]

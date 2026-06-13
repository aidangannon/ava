from ava.crosscutting.result import Error, Ok, Result
from ava.application.model import History
from ava.crosscutting.config import Config
from ava.application import ports, states

HISTORY = "[HISTORY]"
REPLY = "[REPLY]"
PR_TITLE = "[PR-TITLE]"
PR_DESCRIPTION = "[PR-DESCRIPTION]"

ALL_TAGS = [HISTORY, REPLY, PR_TITLE, PR_DESCRIPTION]


def _extract(stdout: str, tag: str) -> str | None:
    if tag not in stdout:
        return None
    content = stdout.split(tag, 1)[1]
    for other in ALL_TAGS:
        if other != tag and other in content:
            content = content.split(other, 1)[0]
    return content.strip() or None


def handle(config: Config, issue: str, stdout: str) -> Result:
    history = _extract(stdout, HISTORY)
    if not history:
        raise Exception(f"Invalid stdout: [HISTORY] missing or empty\n{stdout}")

    ports.config_repository.add_history(
        History(issue=issue, repository=config.repo, content=history)
    )

    reply = _extract(stdout, REPLY)
    if reply:
        ports.issue_inbox.post_comment(config.repo, issue, reply)
        if ports.config_repository.get_state().unwrap() == states.SEARCHING:
            ports.config_repository.set_state(states.PENDING)
        return Ok()

    pr_title = _extract(stdout, PR_TITLE)
    pr_description = _extract(stdout, PR_DESCRIPTION)

    if pr_title and not pr_description:
        raise Exception(f"Invalid stdout: [PR-TITLE] without [PR-DESCRIPTION]\n{stdout}")
    if pr_description and not pr_title:
        raise Exception(f"Invalid stdout: [PR-DESCRIPTION] without [PR-TITLE]\n{stdout}")

    if pr_title and pr_description:
        ports.review_inbox.create_pr(
            repository=config.repo,
            issue_num=issue,
            repo_path=config.repos_dest,
            title=pr_title,
            body=pr_description
        )
        ports.config_repository.set_state(states.REVIEW)

    return Ok()

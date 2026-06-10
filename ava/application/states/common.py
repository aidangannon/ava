from ava.crosscutting.result import Error
from ava.crosscutting.result import Result
from ava.crosscutting.result import Ok
from ava.application import states
from ava.application.model import History
from ava.crosscutting.config import Config
from ava.application import ports

# sections that are from stdout in agent
REPLY = "[REPLY]"
PAUSED = "[PAUSED]"
PR_TITLE = "[PR-TITLE]"
PR_DESCRIPTION = "[PR-DESCRIPTION]"

def handle_reply(config: Config, issue: str, stdout: str) -> Result:
    if REPLY not in stdout:
        return Error("No reply")

    if PAUSED not in stdout:
        raise Exception(f"Invalid state: [REPLY] without [PAUSED]\n{stdout}")

    summary = stdout.split(PAUSED, 1)[1].split(REPLY, 1)[0].strip()
    reply_text = stdout.split(REPLY, 1)[1].strip()

    if not summary:
        raise Exception(f"Invalid state: empty [PAUSED] summary\n{stdout}")

    if not reply_text:
        raise Exception(f"Invalid state: empty [REPLY] content\n{stdout}")

    ports.issue_inbox.post_comment(config.repo, issue, reply_text)
    ports.config_repository.add_history(
        History(issue=issue, repository=config.repo, content=summary)
    )
    ports.config_repository.set_state(states.PENDING)

    return Ok()

def handle_pr(config: Config, issue: str, stdout: str) -> Result:
    if PR_TITLE not in stdout:
        return Error("No pr")

    if PR_DESCRIPTION not in stdout:
        raise Exception(f"Invalid state: [PR-TITLE] without [PR-DESCRIPTION]\n{stdout}")

    pr_title = stdout.split(PR_TITLE, 1)[1].split(PR_DESCRIPTION, 1)[0].strip()
    pr_description = stdout.split(PR_DESCRIPTION, 1)[1].strip()

    if not pr_title:
        raise Exception(f"Invalid state: empty [PR-TITLE]\n{stdout}")

    if not pr_description:
        raise Exception(f"Invalid state: empty [PR-DESCRIPTION]\n{stdout}")

    ports.review_inbox.create_pr(
        repository=config.repo,
        issue_num=issue,
        title=pr_title,
        body=pr_description
    )
    ports.config_repository.set_state(states.REVIEW)

    return Ok()

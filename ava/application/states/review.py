from ava.application.states import common
from ava.crosscutting.config import Config
from ava.crosscutting import logging
from ava.application import ports


def _describe_event(config: Config, history) -> str | None:
    """
    REVIEW is event-driven: only invoke the agent when something on the
    PR or issue actually changed. The agent decides what to do about it
    (address + resolve comments, merge + close) via the GitHub MCP/CLI.
    """
    pr_status_result = ports.review_inbox.get_pr_status(
        repository=history.repository, issue_num=history.issue
    )

    if not pr_status_result.has_failed():
        pr_status = pr_status_result.unwrap()

        if pr_status.approved:
            return "The PR has been approved. Merge it, close the issue, and confirm."

        if pr_status.unresolved_comments > 0:
            return f"The PR has {pr_status.unresolved_comments} unresolved review comment(s). Address them and resolve each thread once done."
    else:
        logging.logger.warning(pr_status_result.msg)

    reply_result = ports.issue_inbox.get_latest_comment_by(
        repository=config.repo,
        issue_num=history.issue,
        user=config.manager_username
    )

    if not reply_result.has_failed():
        return f"New comment on the issue from {config.manager_username}: {reply_result.unwrap()}"

    return None


def run(config: Config) -> None:
    history = ports.config_repository.get_active_history().unwrap()

    event = _describe_event(config, history)
    if event is None:
        logging.logger.info("No new activity on the PR or issue, waiting")
        return

    basic_prompt = f"Repo:{config.repo}\nRepoPath:{config.repos_dest}\nIssue:{history.issue}\nAuthorForCommits:{config.manager_email}\nReviewEvent:{event}"

    run_result = ports \
        .run_agent(
            skill="ava",
            prompt=basic_prompt,
            history=history.content
        )

    if run_result.has_failed():
        logging.logger.error(run_result.msg)
        return

    stdout = run_result.unwrap()
    if not stdout:
        return

    common.handle(config, history.issue, stdout)

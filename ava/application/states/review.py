from ava.application.states import common
from ava.crosscutting.config import Config
from ava.crosscutting import logging
from ava.application import ports


def run(config: Config) -> None:
    history = ports.config_repository.get_active_history().unwrap()

    pr_status_result = ports.review_inbox.get_pr_status(
        repository=history.repository, issue_num=history.issue
    )
    if pr_status_result.has_failed():
        logging.logger.warning(pr_status_result.msg)
        return

    pr_status = pr_status_result.unwrap()
    if pr_status.approved:
        event = "The PR has been approved. Merge it, close the issue, and confirm."
    elif pr_status.unresolved_comments > 0:
        event = f"The PR has {pr_status.unresolved_comments} unresolved review comment(s). Address them and resolve each thread once done."
    else:
        logging.logger.info("No new activity on the PR, waiting")
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

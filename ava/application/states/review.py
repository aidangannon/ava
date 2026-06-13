from ava.application.states import common
from ava.application import states
from ava.crosscutting.config import Config
from ava.crosscutting import logging
from ava.application import ports


def run(config: Config) -> None:
    history = ports.config_repository.get_active_history().unwrap()
    reply = None

    pr_status = ports \
        .review_inbox \
        .get_latest_pr_status(repository=history.repository, issue_num=history.issue) \
        .unwrap()

    if pr_status == "merged":
        logging.logger.info("Task complete")

        if ports.config_repository.clear_history().has_failed():
            raise Exception("History failed to clear!!! Clear manually and restart, task complete")

        return

    reply_result = ports \
        .issue_inbox \
        .get_latest_comment_by(
            repository=config.repo,
            issue_num=history.issue,
            user=config.manager_username
        )

    if reply_result.has_failed():
        logging.logger.warning(reply_result.msg)
        logging.logger.info(f"Waiting for reply for '{config.manager_username}'")

        return

    reply = reply_result.unwrap()

    if "[Review]" not in reply:
        logging.logger.warning("There is a message but has no [Review] tag")
        logging.logger.info(f"Waiting for reply for '{config.manager_username}'")

        return

    basic_prompt = f"Repo:{config.repo}\nRepoPath:{config.repos_dest}\nIssue:{history.issue}\nAuthorForCommits:{config.manager_email}\nPrUp:True\nReply: {reply}"

    run_result = ports \
        .run_agent(
            skill="ava",
            prompt=basic_prompt,
            history=None if history is None else history.content
        )

    if run_result.has_failed():
        logging.logger.error(run_result.msg)
        return

    stdout = run_result.unwrap()
    if not stdout:
        return

    common.handle(config, history.issue, stdout)
    common.handle_reply(config, history.issue, stdout)

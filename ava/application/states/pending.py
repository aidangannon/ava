from ava.application.states import common
from ava.crosscutting.config import Config
from ava.crosscutting import logging
from ava.application import ports


def run(config: Config) -> None:
    history = ports.config_repository.get_active_history().unwrap()

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

    basic_prompt = f"Repo:{config.repo}\nRepoPath:{config.repos_dest}\nIssue:{history.issue}\nAuthorForCommits:{config.manager_email}\nReplyEvent:{config.manager_username} replied on the issue — go read it via gh/MCP and continue"

    run_result = ports \
        .run_agent(
            skill="ava",
            prompt=basic_prompt,
            history=None if history is None else history.content
        )

    stdout = run_result.unwrap()
    if not stdout:
        raise Exception("Stdout from agent does not exist")

    common.handle(config, history.issue, stdout)

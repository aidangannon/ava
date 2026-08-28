from ava.application.stdout import parse
from ava.crosscutting.config import Config
from ava.crosscutting import logging
from ava.application import ports, states
from ava.application.model import History

VALID_STATES = {states.PENDING, states.REVIEW}


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
            history=history.content
        )

    stdout = run_result.unwrap()
    if not stdout:
        raise Exception("Stdout from agent does not exist")

    new_history, target_state = parse(stdout)
    if target_state not in VALID_STATES:
        raise Exception(f"Invalid transition from PENDING to {target_state}")

    ports.config_repository.add_history(
        History(issue=history.issue, repository=config.repo, content=new_history)
    )
    ports.config_repository.set_state(target_state).throw_if_failed()

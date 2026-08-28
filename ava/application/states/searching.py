from ava.application.stdout import parse
from ava.crosscutting.config import Config
from ava.crosscutting import logging
from pathlib import Path
from ava.application import ports, states
from ava.application.model import History

VALID_STATES = {states.PENDING, states.REVIEW}


def run(config: Config) -> None:
    get_first_issue_result = ports.issue_inbox.get_first_assigned_issue(
        assignee=config.agent_username,
        repository=config.repo
    )

    if get_first_issue_result.has_failed():
        logging.logger.warning(get_first_issue_result.msg)
        logging.logger.info(f"No first issue found for {config.agent_username}, will keep scanning")

        return

    issue = get_first_issue_result.unwrap()

    if not Path(config.repos_dest).exists():
        clone_result = ports.clone_repo(config.repo, config.repos_dest)
        clone_result.throw_if_failed()
    else:
        logging.logger.info(f"repo '{config.repos_dest}' is already cloned")

    basic_prompt = f"Repo:{config.repo}\nRepoPath:{config.repos_dest}\nIssue:{issue}\nAuthorForCommits:{config.manager_email}"

    run_result = ports \
        .run_agent(
            skill="ava",
            prompt=basic_prompt,
            history=None
        )

    stdout = run_result.unwrap()
    if not stdout:
        raise Exception("Stdout from agent does not exist")

    history, target_state = parse(stdout)
    if target_state not in VALID_STATES:
        raise Exception(f"Invalid transition from SEARCHING to {target_state}")

    ports.config_repository.add_history(
        History(issue=issue, repository=config.repo, content=history)
    )
    ports.config_repository.set_state(target_state).throw_if_failed()

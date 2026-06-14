from ava.application.states import common
from ava.crosscutting.config import Config
from ava.crosscutting import logging
from pathlib import Path
from ava.application import ports


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

    basic_prompt = f"Repo:{config.repo}\nRepoPath:{config.repos_dest}\nIssue:{issue}\nAuthorForCommits:{config.manager_email}\nPrUp:False"

    run_result = ports \
        .run_agent(
            skill="ava",
            prompt=basic_prompt,
            history=None
        )

    stdout = run_result.unwrap()
    if not stdout:
        raise Exception("Stdout from agent does not exist")
    
    common.handle(config, issue, stdout)

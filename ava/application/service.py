from ava.crosscutting import logging
from ava.crosscutting.result import TypeOk
from ava.crosscutting.result import TypeError
from ava.crosscutting.result import TypeResult
from pathlib import Path
from ava.application import ports
from ava.application.model import History


def ava_routine() -> None:
    config = ports.config_repository.get_config().unwrap()

    repo: str = config["Repo"]
    repos_dest: Path = Path(config["ReposDest"])
    agent_username: str = config["Agent"]
    manager_username: str = config["Author"]
    manager_email: str = config["AuthorEmail"]

    logging.logger.info(f"ava_routine: repo={repo} repos_dest={repos_dest} agent={agent_username} author={manager_username} author_email={manager_email}")

    history_result = ports.config_repository.get_active_history()
    reply = None

    if not history_result.has_failed():
        history = history_result.unwrap()
        logging.logger.info(f"Active history for repo '{repo}'")
        issue = history.issue
    else:
        history = None
        issue_result = get_first_issue(agent_username=agent_username, repo=repo, repos_dest=repos_dest)

        if issue_result.has_failed():
            logging.logger.error(issue_result.msg)
            return

        issue = issue_result.unwrap()

        reply = ports \
            .issue_inbox \
            .get_latest_comment_by(repository=repo, issue_num=issue, user=manager_username)

    basic_prompt = f"Repo:{repo}\nRepoPath:{repos_dest}\nIssue:{issue}\nAuthorForCommits:{manager_email}"

    if reply is not None:
        basic_prompt += f"\nReply: {reply}"

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

    if "[REPLY]" in stdout:
        reply_text = stdout.split("[REPLY]", 1)[1].split("[PAUSED]", 1)[0].strip()
        if reply_text:
            ports.issue_inbox.post_comment(repo, issue, reply_text)

    if stdout.startswith("[PAUSED]") or "[PAUSED]" in stdout:
        summary = stdout.split("[PAUSED]", 1)[1].strip()
        if summary:
            ports.config_repository.add_history(
                History(issue=issue, repository=repo, content=summary)
            )

def get_first_issue(agent_username: str, repo: str, repos_dest: Path) -> TypeResult[str]:
    get_first_issue_result = ports.issue_inbox.get_first_assigned_issue(
        assignee=agent_username, repository=repo
    )

    if get_first_issue_result.has_failed():
        logging.logger.error(get_first_issue_result.msg)
        return TypeError("No first issue found")

    issue = get_first_issue_result.unwrap()

    if not (repos_dest).exists():
        clone_result = ports.clone_repo(repo, str(repos_dest))
        if clone_result.has_failed():
            return TypeError[str](clone_result.msg)

    return TypeOk[str](issue)

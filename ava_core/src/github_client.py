import subprocess

from github import Github, GithubException


class GithubError(Exception):
    pass


def _token() -> str:
    try:
        r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise GithubError("Run 'gh auth login' to authenticate") from e


def _repo(owner: str, repo_name: str):
    try:
        return Github(_token()).get_repo(f"{owner}/{repo_name}")
    except GithubException as e:
        raise GithubError(f"Cannot access {owner}/{repo_name}: {e}") from e


def get_assigned_issues(owner: str, repo_name: str, username: str) -> list:
    try:
        return list(_repo(owner, repo_name).get_issues(state="open", assignee=username))
    except GithubError:
        raise
    except GithubException as e:
        raise GithubError(f"Cannot list issues for {owner}/{repo_name}: {e}") from e


def get_user_reply_after_bot(owner: str, repo_name: str, issue_number: int, bot_user: str) -> str | None:
    try:
        comments = list(_repo(owner, repo_name).get_issue(issue_number).get_comments())
    except GithubException as e:
        raise GithubError(f"Cannot read comments for {owner}/{repo_name}#{issue_number}: {e}") from e

    last_waiting_idx = None
    for i, c in enumerate(comments):
        if c.user.login == bot_user and "[AVA:WAITING]" in c.body:
            last_waiting_idx = i

    if last_waiting_idx is None:
        return None

    for c in comments[last_waiting_idx + 1 :]:
        if c.user.login != bot_user:
            return c.body

    return None


def issue_accessible(owner: str, repo_name: str, issue_number: int) -> bool:
    try:
        _repo(owner, repo_name).get_issue(issue_number)
        return True
    except (GithubException, GithubError):
        return False

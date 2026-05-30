import os
import subprocess

from github import Github, GithubException


class GithubError(Exception):
    pass


def _token() -> str | None:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return None


class GithubClient:
    def __init__(self, owner: str, repo_name: str):
        self._gh = Github(_token())
        self.owner = owner
        self.repo_name = repo_name
        try:
            self._repo = self._gh.get_repo(f"{owner}/{repo_name}")
        except GithubException as e:
            raise GithubError(f"Cannot access {owner}/{repo_name}: {e}") from e

    def get_assigned_issues(self, username: str) -> list:
        try:
            return list(self._repo.get_issues(state="open", assignee=username))
        except GithubException as e:
            raise GithubError(f"Cannot list issues for {self.owner}/{self.repo_name}: {e}") from e

    def get_user_reply_after_bot(self, issue_number: int, bot_user: str) -> str | None:
        """Return the first user comment that appears after the last [AVA:WAITING] bot comment."""
        try:
            comments = list(self._repo.get_issue(issue_number).get_comments())
        except GithubException as e:
            raise GithubError(f"Cannot read comments for #{issue_number}: {e}") from e

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

    def issue_accessible(self, issue_number: int) -> bool:
        try:
            self._repo.get_issue(issue_number)
            return True
        except GithubException:
            return False

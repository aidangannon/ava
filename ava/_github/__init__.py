from ava.crosscutting import logging
import subprocess
from dataclasses import dataclass, field

from github import Github, UnknownObjectException

from ava.application import ports
from ava.crosscutting.result import Ok, Error, Result, TypeOk, TypeError, TypeResult


@dataclass(slots=True)
class GithubIssueInbox:
    _client: Github | None = field(default=None)

    def get_first_assigned_issue(self, repository: str, assignee: str) -> TypeResult[str]:
        try:
            repo = self.client.get_repo(full_name_or_id=repository)
        except UnknownObjectException:
            return TypeError[str](f"Repository '{repository}' not found")

        _debug = repo.get_issues(state="open")[0].assignees[0].login
        logging.logger.info(f"Debug log username of issue assiginee {_debug}")
        issues = repo.get_issues(assignee=assignee, state="open")
        if issues.totalCount == 0:
            return TypeError[str](f"No open issues assigned to '{assignee}' for '{repository}'")

        return TypeOk[str](str(issues[0].number))

    def get_latest_comment_by(self,
        repository: str,
        issue_num: str,
        user: str) -> TypeResult[str]:
        try:
            repo = self.client.get_repo(full_name_or_id=repository)
        except UnknownObjectException:
            return TypeError[str](f"Repository '{repository}' not found")

        try:
            issue = repo.get_issue(number=int(issue_num))
        except UnknownObjectException:
            return TypeError[str](f"Issue #{issue_num} not found")

        comments = list(issue.get_comments())
        if not comments:
            return TypeError[str]("No comments on issue")

        last_comment = comments[-1]

        if last_comment.user.login == user:
            return TypeOk[str](last_comment.body)

        return TypeError[str](f"Last comment was by '{last_comment.user.login}' not by '{user}'")

    def post_comment(self, repository: str, issue_num: str, text: str) -> Result:
        try:
            repo = self.client.get_repo(full_name_or_id=repository)
        except UnknownObjectException:
            return Error(f"Repository '{repository}' not found")

        try:
            issue = repo.get_issue(number=int(issue_num))
        except UnknownObjectException:
            return Error(f"Issue #{issue_num} not found")

        issue.create_comment(text)
        return Ok()

    @property
    def client(self) -> Github:
        if not self._client:
            config = ports \
                .config_repository \
                .get_config() \
                .unwrap()
            self._client = Github(config["Github"]["Token"])
        return self._client


github_issue_inbox = GithubIssueInbox()

def clone_github_repo(repo_full_name: str, dest: str) -> Result:
    result = subprocess.run(
        ["git", "clone", f"git@github.com:{repo_full_name}.git", dest],
        capture_output=True, text=True
    )
    if result.returncode == 128:
        return Error(f"Access denied to '{repo_full_name}': {result.stderr.strip()}")
    result.check_returncode()
    return Ok()

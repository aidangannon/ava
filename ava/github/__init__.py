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

        issues = repo.get_issues(assignee=assignee, state="open")
        if issues.totalCount == 0:
            return TypeError[str](f"No open issues assigned to '{assignee}'")

        return TypeOk[str](str(issues[0].number))

    def get_latest_comment(self, repository: str, issue_num: str) -> TypeResult[str]:
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

        return TypeOk[str](comments[-1].body)

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

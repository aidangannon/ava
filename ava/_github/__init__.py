from ava.crosscutting import logging
import subprocess
from dataclasses import dataclass

from github import Github, UnknownObjectException

from ava.application import ports
from ava.crosscutting.result import Ok, Error, Result, TypeOk, TypeError, TypeResult

_client: Github | None = None

def _get_client() -> Github:
    global _client
    if not _client:
        config = ports.config_repository.get_config().unwrap()
        _client = Github(config["github_token"])
    return _client


@dataclass(slots=True)
class GithubIssueInbox:

    def get_first_assigned_issue(self, repository: str, assignee: str) -> TypeResult[str]:
        try:
            repo = _get_client().get_repo(full_name_or_id=repository)
        except UnknownObjectException:
            return TypeError[str](f"Repository '{repository}' not found")

        _debug = repo.get_issues(state="open")[0].assignees[0].login
        logging.logger.info(f"Debug log username of issue assiginee {_debug}")
        issues = repo.get_issues(assignee=assignee, state="open")
        if issues.totalCount == 0:
            return TypeError[str](f"No open issues assigned to '{assignee}' for '{repository}'")

        return TypeOk[str](str(issues[0].number))

    def get_latest_comment_by(self, repository: str, issue_num: str, user: str) -> TypeResult[str]:
        try:
            repo = _get_client().get_repo(full_name_or_id=repository)
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
            repo = _get_client().get_repo(full_name_or_id=repository)
        except UnknownObjectException:
            return Error(f"Repository '{repository}' not found")

        try:
            issue = repo.get_issue(number=int(issue_num))
        except UnknownObjectException:
            return Error(f"Issue #{issue_num} not found")

        issue.create_comment(text)
        return Ok()


@dataclass(slots=True)
class GithubReviewInbox:

    def get_latest_pr_status(self, repository: str, issue_num: str) -> TypeResult[str]:
        try:
            repo = _get_client().get_repo(full_name_or_id=repository)
        except UnknownObjectException:
            return TypeError[str](f"Repository '{repository}' not found")

        prs = [pr for pr in repo.get_pulls(state="open") if pr.head.ref == issue_num]
        if not prs:
            return TypeError[str](f"No open PR found for issue #{issue_num}")

        pr = prs[0]
        if pr.mergeable:
            return TypeOk[str]("ready_to_merge")
        return TypeOk[str]("open")

    def create_pr(self, repository: str, issue_num: str, title: str, body: str) -> Result:
        try:
            repo = _get_client().get_repo(full_name_or_id=repository)
        except UnknownObjectException:
            return Error(f"Repository '{repository}' not found")

        repo.create_pull(
            title=title,
            body=body,
            head=issue_num,
            base=repo.default_branch
        )
        return Ok()

    def merge(self, repository: str, issue_num: str) -> Result:
        try:
            repo = _get_client().get_repo(full_name_or_id=repository)
        except UnknownObjectException:
            return Error(f"Repository '{repository}' not found")

        prs = [pr for pr in repo.get_pulls(state="open") if pr.head.ref == issue_num]
        if not prs:
            return Error(f"No open PR found for issue #{issue_num}")

        prs[0].merge()
        return Ok()

github_issue_inbox = GithubIssueInbox()
github_review_inbox = GithubReviewInbox()


def clone_github_repo(repo_full_name: str, dest: str) -> Result:
    result = subprocess.run(
        ["git", "clone", f"git@github.com:{repo_full_name}.git", dest],
        capture_output=True, text=True
    )
    if result.returncode == 128:
        return Error(f"Access denied to '{repo_full_name}': {result.stderr.strip()}")
    result.check_returncode()
    return Ok()

import json
import os
import subprocess
from dataclasses import dataclass

from github import Github, UnknownObjectException

from ava.application import ports
from ava.application.model import PrStatus
from ava.crosscutting.result import Ok, Error, Result, TypeOk, TypeError, TypeResult

_client: Github | None = None

def _get_client() -> Github:
    global _client
    if not _client:
        config = ports.config_repository.get_config().unwrap()
        _client = Github(config["github_token"])
    return _client


_UNRESOLVED_THREADS_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes { isResolved }
      }
    }
  }
}
"""


def _unresolved_review_thread_count(repository: str, pr_number: int) -> int:
    """
    Whether a review thread is resolved isn't exposed by the REST API,
    only GraphQL — shell out to `gh` (already required for the skill's
    own PR interactions) rather than hand-rolling a GraphQL client.
    """
    owner, name = repository.split("/", 1)
    config = ports.config_repository.get_config().unwrap()

    result = subprocess.run(
        ["gh", "api", "graphql",
         "-f", f"query={_UNRESOLVED_THREADS_QUERY}",
         "-F", f"owner={owner}",
         "-F", f"name={name}",
         "-F", f"number={pr_number}"],
        capture_output=True,
        text=True,
        env={**os.environ, "GH_TOKEN": config["github_token"]}
    )
    result.check_returncode()

    threads = json.loads(result.stdout)["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    return sum(1 for thread in threads if not thread["isResolved"])


@dataclass(slots=True)
class GithubIssueInbox:

    def get_first_assigned_issue(self, repository: str, assignee: str) -> TypeResult[str]:
        try:
            repo = _get_client().get_repo(full_name_or_id=repository)
        except UnknownObjectException:
            return TypeError[str](f"Repository '{repository}' not found")

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


@dataclass(slots=True)
class GithubReviewInbox:

    def get_pr_status(self, repository: str, issue_num: str) -> TypeResult[PrStatus]:
        try:
            repo = _get_client().get_repo(full_name_or_id=repository)
        except UnknownObjectException:
            return TypeError[PrStatus](f"Repository '{repository}' not found")

        prs = [pr for pr in repo.get_pulls(state="open") if pr.head.ref == issue_num]
        if not prs:
            return TypeError[PrStatus](f"No open PR found for issue #{issue_num}")

        pr = prs[0]
        config = ports.config_repository.get_config().unwrap()

        reviews = list(pr.get_reviews())
        approved = bool(reviews) \
            and reviews[-1].user.login == config["manager_username"] \
            and reviews[-1].state == "APPROVED"

        unresolved = _unresolved_review_thread_count(repository, pr.number)

        return TypeOk[PrStatus](PrStatus(approved=approved, unresolved_comments=unresolved))

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

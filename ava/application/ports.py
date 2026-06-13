from typing import Protocol

from ava.application.model import History
from ava.crosscutting.result import Result, TypeResult

class ReviewInbox(Protocol):

    def get_latest_pr_status(self, repository: str, issue_num: str) -> TypeResult[str]:
        ...

    def create_pr(self, repository: str, issue_num: str, repo_path: str, title: str, body: str) -> Result:
        ...

    def merge(self, repository: str, issue_num: str) -> Result:
        ...

class IssueInbox(Protocol):

    def get_first_assigned_issue(self, repository: str, assignee: str) -> TypeResult[str]:
        ...

    def get_latest_comment_by(self,
        repository: str,
        issue_num: str,
        user: str) -> TypeResult[str]:
        ...

    def post_comment(self, repository: str, issue_num: str, text: str) -> Result:
        ...

class AgentRunner(Protocol):

    def __call__(self,
        skill: str,
        prompt: str,
        history: str | None = None) -> TypeResult[str | None]:
        ...

class RepoCloner(Protocol):

    def __call__(self, repo_full_name: str, dest: str) -> Result:
        ...

class ConfigRepository(Protocol):

    def get_active_history(self) -> TypeResult[History]:
        ...

    def add_history(self, history: History) -> Result:
        ...

    def get_config(self) -> TypeResult[dict]:
        ...

    def get_state(self) -> TypeResult[str]:
        ...

    def set_state(self, state: str) -> Result:
        ...

    def clear_history(self) -> Result:
        ...

issue_inbox: IssueInbox
review_inbox: ReviewInbox
run_agent: AgentRunner
config_repository: ConfigRepository
clone_repo: RepoCloner

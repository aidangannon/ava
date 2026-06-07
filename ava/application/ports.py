from typing import Protocol

from ava.application.model import History
from ava.crosscutting.result import Result, TypeResult

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

issue_inbox: IssueInbox
run_agent: AgentRunner
config_repository: ConfigRepository
clone_repo: RepoCloner

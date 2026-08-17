from typing import Protocol

from ava.application.model import History, PrStatus
from ava.crosscutting.result import Result, TypeResult

class ReviewInbox(Protocol):
    """
    Read-only signals used to decide whether the REVIEW state has new
    work to hand to the agent. Everything that changes GitHub state
    (raising/updating PRs, replying, resolving comments, merging) is
    done by the agent itself via the GitHub MCP/CLI, per the skill.
    """

    def get_pr_status(self, repository: str, issue_num: str) -> TypeResult[PrStatus]:
        ...

class IssueInbox(Protocol):

    def get_first_assigned_issue(self, repository: str, assignee: str) -> TypeResult[str]:
        ...

    def get_latest_comment_by(self,
        repository: str,
        issue_num: str,
        user: str) -> TypeResult[str]:
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

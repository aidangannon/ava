from typing import Protocol

from ava.application.model import History
from ava.crosscutting.result import Result, TypeResult

class IssueInbox(Protocol):

    def search(self, repository: str, assignee: str) -> TypeResult[str]:
        ...

    def get_reply(self, repository: str, issue_num: str) -> TypeResult[str]:
        ...

    def reply(self, repository: str, issue_num: str) -> TypeResult[str]:
        ...

class AgentRunner(Protocol):

    def run(self,
        skill: str,
        history: str | None = None) -> Result:
        ...

class ConfigRepository(Protocol):

    def get_active_history(self) -> TypeResult[History]:
        ...

    def add_history(self, issue_num: str, history: History) -> Result:
        ...

    def get_config(self) -> TypeResult[dict]:
        ...

issue_inbox: IssueInbox
agent_runner: AgentRunner
config_repository: ConfigRepository

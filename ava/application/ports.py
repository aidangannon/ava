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
        history: str | None) -> Result:
        ...

class HistoryRepository(Protocol):

    def get_active(self) -> TypeResult[History]:
        ...

    def add(self, issue_num) ->

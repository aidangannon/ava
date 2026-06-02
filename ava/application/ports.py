from typing import Protocol

from ava.crosscutting.result import Result

class IssueInbox(Protocol):

    def search(self, assignee: str) -> Result[str]:
        ...

    def get_reply(self, issue_num: str) -> Result[str]:
        ...

    def reply(self, issue_num: str) -> Result[str]:
        ...

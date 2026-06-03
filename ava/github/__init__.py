from dataclasses import dataclass, field

from ava.crosscutting.result import TypeResult

@dataclass(slots=True)
class GithubIssueInbox:
    _github: Github  = field(default=None)
    token: str | None = None

    def search(self, repository: str, assignee: str) -> TypeResult[str]:
        ...

    def get_reply(self, repository: str, issue_num: str) -> TypeResult[str]:
        ...

    def reply(self, repository: str, issue_num: str) -> TypeResult[str]:


    def set_token(self):
        if not self.token:
            config = ports \
                .config_repository \
                .get_config() \
                .unwrap()
            self.token = config["Github"]["Token"]


github_issue_inbox = GithubIssueInbox():

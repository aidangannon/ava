from dataclasses import dataclass


@dataclass(slots=True)
class History:
    issue: str
    repository: str
    content: str

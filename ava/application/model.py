from dataclasses import dataclass


@dataclass(slots=True)
class History:
    issue: str
    repository: str
    content: str


@dataclass(slots=True, frozen=True)
class PrStatus:
    approved: bool
    unresolved_comments: int

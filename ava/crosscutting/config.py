from pathlib import Path
from dataclasses import dataclass

@dataclass(slots=True)
class Config:
    repo: str
    repos_dest: str
    agent_username: str
    manager_username: str
    manager_email: str

import json
from dataclasses import dataclass
from pathlib import Path

from ava.application.model import History
from ava.crosscutting.result import Error, Ok, Result, TypeError, TypeOk, TypeResult


@dataclass(slots=True)
class FileConfigRepository:
    config_path: Path = Path.home() / ".config" / "ava"
    history_file: Path = config_path / "history.md"
    state_file: Path = config_path / "state.json"
    config_file: Path = config_path / "config.json"

    def get_active_history(self) -> TypeResult[History]:
        with open(self.state_file) as f:
            contents = json.load(f)
        
        if "active_repo" not in contents:
            return TypeError[History]("No active history")

        with open(self.history_file) as f:
            history_contents = f.read() 
        
        return TypeOk[History](
            History(
                repository=contents["active_repo"],
                issue=contents["active_issue"],
                content=history_contents
            )
        )

    def add_history(self, history: History) -> Result:
        with open(self.history_file, "w") as f:
            f.write(history.content)

        with open(self.state_file) as f:
            state = json.load(f)

        state["active_repo"] = history.repository
        state["active_issue"] = history.issue

        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

        return Ok()

    def clear_history(self) -> Result:
        with open(self.state_file, "w") as f:
            json.dump({}, f, indent=2)
        with open(self.history_file, "w") as f:
            f.write("")
        return Ok()

    def get_state(self) -> TypeResult[str]:
        if not self.state_file.exists():
            return TypeError[str]("State file not found")
        with open(self.state_file) as f:
            contents = json.load(f)
        if "state" not in contents:
            return TypeError[str]("No state in state file")
        return TypeOk[str](contents["state"])

    def set_state(self, state: str) -> Result:
        with open(self.state_file) as f:
            contents = json.load(f)
        contents["state"] = state
        with open(self.state_file, "w") as f:
            json.dump(contents, f, indent=2)
        return Ok()

    def get_config(self) -> TypeResult[dict]:
        with open(self.config_file) as f:
            return TypeOk[dict](json.load(f))

file_config_repository = FileConfigRepository()

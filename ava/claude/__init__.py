import subprocess
import os
from dataclasses import dataclass
from ava.application import ports
from ava.crosscutting.result import TypeError, TypeOk, TypeResult


@dataclass(slots=True)
class ClaudeAgentRunner:

    def run(self, skill: str, prompt: str, history: str | None = None) -> TypeResult[str | None]:
        config = ports.config_repository.get_config()
        if config.has_failed():
            return TypeError[str | None]("Failed to load config")

        env = {**os.environ, "ANTHROPIC_API_KEY": config.unwrap()["Anthropic"]["Token"]}
        stdin = f"{prompt}\n\n{history}" if history else prompt

        result = subprocess.run(
            ["claude", "-p", f"/{skill}", "--dangerously-skip-permissions"],
            env=env,
            input=stdin,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return TypeError[str | None](result.stderr)

        stdout = result.stdout.strip() or None
        return TypeOk[str | None](stdout)


claude_agent_runner = ClaudeAgentRunner()

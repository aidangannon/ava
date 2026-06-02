import subprocess
from pathlib import Path

from loguru import logger

WORKDIRS = Path.home() / ".config" / "ava" / "workdirs"


def prepare_workdir(owner: str, repo_name: str, git_email: str | None) -> Path:
    workdir = WORKDIRS / owner / repo_name
    ssh_url = f"git@github.com:{owner}/{repo_name}.git"

    if not workdir.exists():
        workdir.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["git", "clone", ssh_url, str(workdir)], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"git clone failed for {owner}/{repo_name}: {r.stderr.strip()}")
    else:
        subprocess.run(["git", "checkout", "main"], cwd=workdir, capture_output=True)
        subprocess.run(["git", "pull"], cwd=workdir, capture_output=True)

    if git_email:
        subprocess.run(["git", "config", "user.email", git_email], cwd=workdir)

    return workdir


def run_claude(
    owner: str,
    repo_name: str,
    issue_number: int,
    skill: str,
    config: dict,
    reply: str | None = None,
    history: str | None = None,
) -> tuple[str, str]:
    """Run claude on the issue. Returns (status, output) where status is 'done' or 'waiting'."""
    try:
        workdir = prepare_workdir(owner, repo_name, config.get("git_email"))
    except RuntimeError as e:
        logger.error(str(e))
        return "error", ""

    parts = []
    if skill:
        parts.append(skill)
        parts.append("---")

    parts.append(f"Repository: {owner}/{repo_name}")
    parts.append(f"Issue: #{issue_number}")
    parts.append(f"Get full issue details with: gh issue view {issue_number}")

    if history:
        parts.append("\n## Previous context\n" + history)

    if reply:
        parts.append(f"\n## User replied to your question\n{reply}\n\nResume where you left off.")
    else:
        parts.append("\nStart working on this issue now.")

    prompt = "\n\n".join(parts)
    history_path = Path.home() / ".config" / "ava" / "history" / owner / repo_name / f"{issue_number}.md"

    logger.info(f"Running claude on {owner}/{repo_name}#{issue_number}")
    result = subprocess.run(
        ["claude", "--dangerously-skip-permissions", "-p", prompt],
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=3600,
    )

    output = result.stdout
    if result.returncode != 0:
        logger.warning(f"Claude exited {result.returncode} for {owner}/{repo_name}#{issue_number}")

    # Save output as history context for future resumptions
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(output)

    status = "waiting" if "[AVA:WAITING]" in output else "done"
    return status, output

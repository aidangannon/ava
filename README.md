# AVA

Local GitHub issue agent. Polls assigned issues every 5 minutes, runs Claude Code on each one, and raises a PR when done.

## Config

```
~/.config/ava/config.toml   # required
~/.config/ava/repos          # one owner/repo per line
~/.config/ava/skills/ava.md  # your base skill/system prompt
```

### config.toml

```toml
github_user   = "your-github-username"
git_email     = "you@example.com"   # optional override for commits
poll_interval = 300                  # seconds (default 300)
```

### repos

```
owner/repo-one
owner/repo-two
```

### skills/ava.md

Write your instructions for Claude here. End with:

- Post a GitHub comment starting with `[AVA:WAITING]` when you need a decision from the user, then stop.
- Raise a PR and output `[AVA:DONE]` when the task is complete.

## Auth

Set `GITHUB_TOKEN` or ensure `gh auth login` is done. SSH key must have push access to the repos.

## Run

```sh
cd ava_core
uv run ava
```

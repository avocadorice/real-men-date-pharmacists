# agy-template

This is the base template for all Antigravity (agy) projects.

## What's included

- **Auto-logging hooks** — every prompt and the agent's final response are appended to `logs/session.log` automatically via Antigravity workspace-level lifecycle hooks.
- **`new-project` skill** — the agent can interactively walk you through bootstrapping a new project when you ask to create/bootstrap a new project.

## Starting a new project

Just tell the agent:
> "Bootstrap a new project" or "Use the new-project skill"

The agent will load the `new-project` skill, ask you a few questions (name, goal, tech stack, and GitHub repo configuration), and then run the script `scripts/new-project.sh` to create the project under `~/dev/gdrive/`.

## Session log

`logs/session.log` is updated automatically via hooks configured in `.agents/hooks.json`:
- **`PreInvocation`** (runs `log-prompt.py`): Logs your prompt.
- **`Stop`** (runs `log-session-end.py`): Captures the last response from the transcript and appends it.

Use this to review what was discussed across sessions without re-reading full transcripts.

## Updating the template

Make changes here in `~/dev/gdrive/agy-template`. New projects cloned after the change will pick them up. Existing projects won't auto-update (by design).

# Example: Basic DevBoard Setup

This example shows how to set up a DevBoard for a small project.

## Initialize

```bash
cd /path/to/your/project
devboard init --name "My Project"
```

This creates:
- `config.yml` — Board configuration
- `tasks/` — Task directory
- `MASTER.SCHEDULE.md` — Auto-generated status tracking

## Add Tasks

```bash
devboard add "Set up CI pipeline" --priority high --project myapp --tags devops
devboard add "Fix login bug" --priority critical --project myapp --tags bug,auth
devboard add "Write API docs" --priority medium --project myapp --tags docs
```

## Work on Tasks

```bash
# Pick the next available task
devboard pick --agent my-name

# See what's on the board
devboard status

# Move a task to review
devboard move 1 review --agent my-name

# Complete a task
devboard complete 1 --agent my-name
```

## Multi-Agent Workflow

```bash
# Agent 1 picks a task
devboard pick --agent agent-1
# → Picked task 2: Fix login bug

# Agent 2 picks a task
devboard pick --agent agent-2
# → Picked task 1: Set up CI pipeline

# Agent 1 completes their task
devboard complete 2 --agent agent-1

# Agent 2 check the log
devboard log
```

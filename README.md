# DEVBOARD — Multi-Agent Shared Task Board

## Overview
A file-based kanban system for coordinating work across multiple AI agents and human developers. Each task is a file. Folders represent workflow stages. `MASTER.SCHEDULE.md` is the single source of truth.

## Folder Structure
```
DevBoard/
├─ InProgress/       # Tasks currently being worked on (one per agent)
├─ JobStart/         # Tasks started but not yet in progress
├─ JobEnd/           # Completed tasks (archived)
├─ AllPhases/        # Master copy of all tasks, organized by phase
├─ README.md         # This file
├─ TEMPLATE.md       # Task file template
├─ STRUCTURE.md      # Detailed documentation
└─ MASTER.SCHEDULE.md # Single source of truth for all task status
```

## Workflow
1. **Create** a task file using `TEMPLATE.md` and place it in `AllPhases/[Phase]/`
2. **Assign** a task by copying it to `InProgress/` with the agent name prefix
3. **Start work** — move to `JobStart/` when an agent picks it up
4. **Complete** — move to `JobEnd/` when done, update `MASTER.SCHEDULE.md`

## Task Status
- `[ ]` = NOT STARTED
- `[~]` = IN PROGRESS (assigned to an agent)
- `[x]` = COMPLETED
- `[!]` = BLOCKED (dependency not met)

## Agent Coordination
- Each task file has an `Agent:` field showing who's working on it
- Only one agent per task at a time
- Check `MASTER.SCHEDULE.md` before starting new work to avoid conflicts
- Use `Dependencies:` field to track task ordering

## Key Files
- **MASTER.SCHEDULE.md** — Task-level status tracking with `[ ]`/`[~]`/`[x]`/`[!]` markers.
- **TEMPLATE.md** — Template for new task files.
- **STRUCTURE.md** — Detailed folder layout and naming conventions.

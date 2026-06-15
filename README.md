# DevBoard — Multi-Agent Shared Task Board

A file-based kanban system for coordinating work across multiple AI agents and human developers.

## Quick Start
1. Check `__TASKS.md` for current task status
2. Pick an available task (status `[ ]`)
3. Claim it by changing `[ ]` to `[~]` and adding your name
4. Create a task file in `AllPhases/[Phase]/` using `TEMPLATE.md`
5. Move task file through: `AllPhases/` → `InProgress/` → `JobStart/` → `JobEnd/`
6. Update `MASTER.SCHEDULE.md` and `__TASKS.md` on completion

## Folder Structure
- `AllPhases/` — Master copy of all tasks, organized by phase
- `InProgress/` — Tasks currently being worked on
- `JobStart/` — Tasks started but not yet in progress
- `JobEnd/` — Completed tasks (archived)
- `__TASKS.md` — Shared task board (check before starting any work)
- `MASTER.SCHEDULE.md` — Single source of truth for progress tracking
- `TEMPLATE.md` — Task file template
- `STRUCTURE.md` — Detailed documentation

## Agent Protocol
See `STRUCTURE.md` for full coordination rules. Key points:
- **Never** start a task marked `[~]` (another agent is working on it)
- **Always** update `__TASKS.md` before doing any work
- **Never** modify another agent's task file
- **Commit** with message: `devboard: [TASK_ID] [status] — [description]`

## License
Internal tool — RapidWebs Enterprise, LLC

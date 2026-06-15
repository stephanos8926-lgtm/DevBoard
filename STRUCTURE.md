# DEVBOARD Structure Documentation

## Directory Layout
```
DevBoard/
├─ InProgress/                     # Tasks currently being worked on
│   ├─ NA-0042_fix-tui-streaming   # Prefixed with project + task ID
│   └─ AT-0007_add-module-imports
├─ JobStart/                       # Tasks started but not yet in progress
├─ JobEnd/                         # Completed tasks (archived)
│   ├─ NA-0001_project-setup
│   └─ NA-0002_core-architecture
├─ AllPhases/                      # Master copy of all tasks
│   ├─ Refactoring/
│   │   ├─ NA-0001_project-setup
│   │   ├─ NA-0002_core-architecture
│   │   └─ NA-0003_tool-registration
│   ├─ Feature-Work/
│   │   ├─ NA-0042_fix-tui-streaming
│   │   └─ NA-0043_search-providers
│   └─ Bug-Fixes/
│       ├─ NA-0050_word-wrap-fix
│       └─ NA-0051_tool-call-display
├─ README.md                       # Overview and usage instructions
├─ TEMPLATE.md                     # Task file template
├─ STRUCTURE.md                    # This documentation file
└─ MASTER.SCHEDULE.md              # Single source of truth for progress tracking
```

## Workflow Rules
1. **One agent per task** — only one agent works on a task at a time
2. **Check before starting** — always check `MASTER.SCHEDULE.md` before picking up a new task
3. **Dependency check** — verify all dependencies are `[x]` before starting a task
4. **Update on completion** — when moving a task to `JobEnd/`, update `MASTER.SCHEDULE.md`
5. **No code in DevBoard** — DevBOARD contains only planning artifacts. Actual source code lives in project directories.

## Naming Convention
- Task files: `[TASK_ID]_[task-name-with-dashes]`
- Phase folders: `[Phase-Name-With-Dashes]` (under `AllPhases/`)
- No spaces in file or folder names — use dashes
- Task IDs are unique across all projects

## Multi-Agent Coordination
- Before starting any task, check `MASTER.SCHEDULE.md` for:
  - Is it already `[~]` (in progress by another agent)?
  - Are all dependencies `[x]` (completed)?
  - Is the priority appropriate for current goals?
- When an agent picks up a task:
  1. Update `Agent:` field in the task file
  2. Change status from `[ ]` to `[~]` in `MASTER.SCHEDULE.md`
  3. Copy task to `InProgress/`
- When an agent completes a task:
  1. Change status from `[~]` to `[x]` in `MASTER.SCHEDULE.md`
  2. Move task file to `JobEnd/`
  3. Commit changes to git

## Git Integration
- DevBoard is git-tracked
- Commit message format: `devboard: [TASK_ID] [status] — [brief description]`
- Example: `devboard: NA-0042 [~] — Lucien starting TUI streaming fix`

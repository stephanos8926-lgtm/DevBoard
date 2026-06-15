# __TASKS.md — DevBoard Multi-Agent Coordination

> **Shared task board for all agents.** Check this file before starting any work.
> Format: `[STATUS] [TASK_ID] — [DESCRIPTION] | Agent: [NAME] | Project: [PROJECT]`
> Status: `[ ]` not started | `[~]` in progress | `[x]` done | `[!]` blocked

---

## 🔴 ACTIVE TASKS
_If a task is marked `[~]`, another agent is working on it. Do NOT start it._

| Status | Task ID | Description | Agent | Project |
|--------|---------|-------------|-------|---------|
| (all complete) | — | — | — | — |

---

## 🟡 IN PROGRESS
_Tasks currently being worked on. Only one agent per task._

| Status | Task ID | Description | Agent | Project |
|--------|---------|-------------|-------|---------|
| (none) | — | — | — | — |

---

## 🟢 COMPLETED
_Finished tasks moved to JobEnd/_

| Status | Task ID | Description | Agent | Project |
|--------|---------|-------------|-------|---------|
| [x] | DB-0001 | Set up DevBoard folder structure | Lucien | DevBoard |
| [x] | DB-0002 | Create task template | Lucien | DevBoard |
| [x] | DB-0003 | Create MASTER.SCHEDULE.md | OWL | DevBoard |
| [x] | DB-0004 | Strip ForgeAgent context, create sample tasks | OWL | DevBoard |
| [x] | DB-0005 | Add agent coordination protocol to STRUCTURE.md | OWL | DevBoard |
| [x] | DB-0006 | Initialize git repo + commit | Lucien+OWL | DevBoard |

---

## 📋 PROJECT TASK BACKLOG
_Tasks organized by project. Add new tasks here, then move to CRITICAL when ready to start._

### NexusAgent
| Task ID | Description | Priority | Dependencies |
|---------|-------------|----------|--------------|
| NA-0001 | Fix TUI word wrapping bug | HIGH | — |
| NA-0002 | Fix tool call display (raw JSON) | HIGH | — |
| NA-0003 | Verify search providers wired correctly | MEDIUM | — |
| NA-0004 | Unify memory system (SQLite + file + vector) | MEDIUM | — |
| NA-0005 | Add integration test harness | MEDIUM | — |
| NA-0006 | Set up CI/CD pipeline | LOW | — |

### ast-tools
| Task ID | Description | Priority | Dependencies |
|---------|-------------|----------|--------------|
| AT-0001 | Add module_imports MCP tool | DONE | — |

### DevBoard
| Task ID | Description | Priority | Dependencies |
|---------|-------------|----------|--------------|
| DB-0001 | Set up DevBoard folder structure | CRITICAL | — |
| DB-0002 | Create task template | CRITICAL | DB-0001 |
| DB-0003 | Create MASTER.SCHEDULE.md | CRITICAL | DB-0001 |
| DB-0004 | Migrate NexusAgent tasks | HIGH | DB-0003 |
| DB-0005 | Add agent coordination protocol | HIGH | DB-0001 |

---

## 🤖 AGENT PROTOCOL

### Before Starting Any Task
1. **Check this file** — is the task already `[~]`? If yes, pick a different task.
2. **Check dependencies** — are all `[x]`? If no, pick a different task.
3. **Claim the task** — change `[ ]` to `[~]`, add your name in the `Agent` column.
4. **Create task file** — use `TEMPLATE.md`, place in `AllPhases/[Phase]/`.

### While Working
- Keep task file in `InProgress/` with your agent name prefix
- Update `MASTER.SCHEDULE.md` with progress notes
- If blocked, change status to `[!]` and note the blocker

### After Completion
1. Change `[~]` to `[x]` in this file
2. Move task file to `JobEnd/`
3. Update `MASTER.SCHEDULE.md`
4. Commit with message: `devboard: [TASK_ID] [x] — [brief description]`

### Coordination Rules
- **Never modify a task file that belongs to another agent** (check `Agent:` field)
- **Never start a task marked `[~]`** — find something else
- **Always update this file first** before doing any work
- **If you see a conflict** (both agents want the same task), the agent who claimed it first wins

"""DevBoard — Multi-agent shared task board."""

from __future__ import annotations

__version__ = "1.0.0"

import json
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

import yaml


# ─── Data Models ───────────────────────────────────────────────────────────

@dataclass
class Task:
    """A single task in the DevBoard."""
    task_id: str
    name: str
    phase: str
    priority: str = "MEDIUM"
    description: str = ""
    agent: str = "Unassigned"
    status: str = " "  # " " = not started, "~" = in progress, "x" = done, "!" = blocked
    dependencies: list[str] = field(default_factory=list)
    project: str = ""
    files_to_modify: list[str] = field(default_factory=list)
    files_to_create: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()
        self.updated_at = datetime.now(UTC).isoformat()

    @property
    def status_marker(self) -> str:
        return f"[{self.status}]"

    @property
    def is_available(self) -> bool:
        return self.status == " "

    @property
    def is_in_progress(self) -> bool:
        return self.status == "~"

    @property
    def is_done(self) -> bool:
        return self.status == "x"

    @property
    def is_blocked(self) -> str:
        return self.status == "!"

    def to_file_content(self) -> str:
        """Serialize to task file format."""
        lines = [
            self.task_id,
            self.name,
            self.phase,
            self.priority,
            "",
            self.description,
            "",
            "## AGENT",
            self.agent,
            "",
            "## DEPENDENCIES",
        ]
        if self.dependencies:
            for dep in self.dependencies:
                lines.append(f"- {dep}")
        else:
            lines.append("- (none)")

        lines.extend([
            "",
            "## PROJECT",
            self.project,
            "",
            "## FILES TO MODIFY",
        ])
        if self.files_to_modify:
            for f in self.files_to_modify:
                lines.append(f"- {f}")
        else:
            lines.append("- (none)")

        lines.extend([
            "",
            "## FILES TO CREATE",
        ])
        if self.files_to_create:
            for f in self.files_to_create:
                lines.append(f"- {f}")
        else:
            lines.append("- (none)")

        lines.extend([
            "",
            "## ACCEPTANCE CRITERIA",
        ])
        if self.acceptance_criteria:
            for c in self.acceptance_criteria:
                lines.append(f"- [ ] {c}")
        else:
            lines.append("- (none)")

        lines.extend([
            "",
            "## NOTES",
            self.notes if self.notes else "(none)",
        ])

        return "\n".join(lines)

    @classmethod
    def from_file(cls, path: Path) -> Task:
        """Parse a task from a task file."""
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Parse header (first 4 lines)
        task_id = lines[0].strip() if len(lines) > 0 else ""
        name = lines[1].strip() if len(lines) > 1 else ""
        phase = lines[2].strip() if len(lines) > 2 else ""
        priority = lines[3].strip() if len(lines) > 3 else "MEDIUM"

        # Parse sections
        description = ""
        agent = "Unassigned"
        dependencies = []
        project = ""
        files_to_modify = []
        files_to_create = []
        acceptance_criteria = []
        notes = ""

        current_section = None
        for line in lines[4:]:
            stripped = line.strip()
            if stripped.startswith("## "):
                current_section = stripped[3:].upper()
                continue

            if current_section == "DESCRIPTION" or (current_section is None and stripped and not stripped.startswith("#")):
                description += stripped + "\n"
            elif current_section == "AGENT":
                if stripped and not stripped.startswith("-"):
                    agent = stripped
            elif current_section == "DEPENDENCIES":
                if stripped.startswith("- "):
                    dep = stripped[2:].strip()
                    if dep != "(none)":
                        dependencies.append(dep)
            elif current_section == "PROJECT":
                if stripped and not stripped.startswith("-"):
                    project = stripped
            elif current_section == "FILES TO MODIFY":
                if stripped.startswith("- "):
                    f = stripped[2:].strip()
                    if f != "(none)":
                        files_to_modify.append(f)
            elif current_section == "FILES TO CREATE":
                if stripped.startswith("- "):
                    f = stripped[2:].strip()
                    if f != "(none)":
                        files_to_create.append(f)
            elif current_section == "ACCEPTANCE CRITERIA":
                if stripped.startswith("- [ ] "):
                    acceptance_criteria.append(stripped[6:].strip())
            elif current_section == "NOTES":
                if stripped != "(none)":
                    notes += stripped + "\n"

        return cls(
            task_id=task_id,
            name=name,
            phase=phase,
            priority=priority,
            description=description.strip(),
            agent=agent,
            dependencies=dependencies,
            project=project,
            files_to_modify=files_to_modify,
            files_to_create=files_to_create,
            acceptance_criteria=acceptance_criteria,
            notes=notes.strip(),
        )


@dataclass
class BoardStats:
    """Statistics for a DevBoard."""
    total: int = 0
    not_started: int = 0
    in_progress: int = 0
    done: int = 0
    blocked: int = 0
    by_project: dict[str, int] = field(default_factory=dict)
    by_phase: dict[str, int] = field(default_factory=dict)
    by_agent: dict[str, int] = field(default_factory=dict)


# ─── Board Manager ─────────────────────────────────────────────────────────

class DevBoard:
    """Manages a DevBoard directory."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.in_progress_dir = self.root / "InProgress"
        self.job_start_dir = self.root / "JobStart"
        self.job_end_dir = self.root / "JobEnd"
        self.all_phases_dir = self.root / "AllPhases"
        self.tasks_file = self.root / "__TASKS.md"
        self.master_file = self.root / "MASTER.SCHEDULE.md"

    def exists(self) -> bool:
        return self.root.is_dir() and self.tasks_file.exists()

    def init(self) -> None:
        """Initialize a new DevBoard directory."""
        for d in [self.in_progress_dir, self.job_start_dir, self.job_end_dir, self.all_phases_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Write __TASKS.md
        if not self.tasks_file.exists():
            self.tasks_file.write_text(_TEMPLATE_TASKS, encoding="utf-8")

        # Write MASTER.SCHEDULE.md
        if not self.master_file.exists():
            self.master_file.write_text(_TEMPLATE_MASTER, encoding="utf-8")

        # Write TEMPLATE.md
        template_file = self.root / "TEMPLATE.md"
        if not template_file.exists():
            template_file.write_text(_TEMPLATE_TASK_FILE, encoding="utf-8")

    def load_tasks(self) -> list[Task]:
        """Load all task files from AllPhases/."""
        tasks = []
        if not self.all_phases_dir.exists():
            return tasks

        for phase_dir in sorted(self.all_phases_dir.iterdir()):
            if not phase_dir.is_dir():
                continue
            for task_file in sorted(phase_dir.iterdir()):
                if task_file.is_file() and not task_file.name.startswith("."):
                    try:
                        task = Task.from_file(task_file)
                        # Check if there's a status override in InProgress/JobStart/JobEnd
                        task.status = self._get_task_status(task.task_id)
                        tasks.append(task)
                    except Exception:
                        continue

        return tasks

    def _get_task_status(self, task_id: str) -> str:
        """Determine task status from file location."""
        if (self.job_end_dir / task_id).exists():
            return "x"
        if (self.job_start_dir / task_id).exists():
            return "~"
        if (self.in_progress_dir / task_id).exists():
            return "~"
        return " "

    def get_stats(self) -> BoardStats:
        """Get board statistics."""
        tasks = self.load_tasks()
        stats = BoardStats(total=len(tasks))

        for task in tasks:
            if task.status == " ":
                stats.not_started += 1
            elif task.status == "~":
                stats.in_progress += 1
            elif task.status == "x":
                stats.done += 1
            elif task.status == "!":
                stats.blocked += 1

            stats.by_project[task.project] = stats.by_project.get(task.project, 0) + 1
            stats.by_phase[task.phase] = stats.by_phase.get(task.phase, 0) + 1
            if task.agent != "Unassigned":
                stats.by_agent[task.agent] = stats.by_agent.get(task.agent, 0) + 1

        return stats

    def add_task(self, task: Task) -> Path:
        """Add a new task to the board."""
        phase_dir = self.all_phases_dir / task.phase
        phase_dir.mkdir(parents=True, exist_ok=True)
        task_path = phase_dir / f"{task.task_id}_{task.name.replace(' ', '-')}"
        task_path.write_text(task.to_file_content(), encoding="utf-8")
        self._update_master()
        return task_path

    def claim_task(self, task_id: str, agent: str) -> Optional[Path]:
        """Claim a task for an agent. Returns path or None if unavailable."""
        # Find the task file
        task_file = self._find_task_file(task_id)
        if not task_file:
            return None

        task = Task.from_file(task_file)
        if not task.is_available:
            return None

        # Update task
        task.status = "~"
        task.agent = agent
        task_path = self.in_progress_dir / f"{task_id}_{task.name.replace(' ', '-')}"
        task_path.write_text(task.to_file_content(), encoding="utf-8")

        self._update_tasks_file(task)
        self._update_master()
        return task_path

    def complete_task(self, task_id: str) -> Optional[Path]:
        """Mark a task as completed."""
        task_file = self._find_task_file(task_id)
        if not task_file:
            return None

        task = Task.from_file(task_file)
        task.status = "x"
        task.updated_at = datetime.now(UTC).isoformat()

        # Move to JobEnd
        dest = self.job_end_dir / f"{task_id}_{task.name.replace(' ', '-')}"
        dest.write_text(task.to_file_content(), encoding="utf-8")

        # Remove from InProgress/JobStart
        for d in [self.in_progress_dir, self.job_start_dir]:
            for f in d.iterdir():
                if f.name.startswith(task_id):
                    f.unlink()

        self._update_tasks_file(task)
        self._update_master()
        return dest

    def _find_task_file(self, task_id: str) -> Optional[Path]:
        """Find a task file by ID across all directories."""
        for base in [self.all_phases_dir, self.in_progress_dir, self.job_start_dir, self.job_end_dir]:
            if not base.exists():
                continue
            if base == self.all_phases_dir:
                for phase_dir in base.iterdir():
                    if phase_dir.is_dir():
                        for f in phase_dir.iterdir():
                            if f.name.startswith(task_id):
                                return f
            else:
                for f in base.iterdir():
                    if f.name.startswith(task_id):
                        return f
        return None

    def _update_tasks_file(self, task: Task) -> None:
        """Update a single task entry in __TASKS.md."""
        if not self.tasks_file.exists():
            return

        content = self.tasks_file.read_text(encoding="utf-8")
        # Find and replace the task line
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if task.task_id in line and ("|" in line or line.strip().startswith("|")):
                # Update status in the line
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    parts[0] = f"[{task.status}]"
                    parts[3] = task.agent
                    lines[i] = " | ".join(parts)
                break

        self.tasks_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _update_master(self) -> None:
        """Regenerate MASTER.SCHEDULE.md from current tasks."""
        tasks = self.load_tasks()
        stats = self.get_stats()

        lines = [
            "# MASTER.SCHEDULE.md — DevBoard Progress Tracking",
            "",
            f"> Last updated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"> Total: {stats.total} | Not started: {stats.not_started} | In progress: {stats.in_progress} | Done: {stats.done} | Blocked: {stats.blocked}",
            "",
            "## Legend",
            "- `[ ]` = NOT STARTED",
            "- `[~]` = IN PROGRESS",
            "- `[x]` = COMPLETED",
            "- `[!]` = BLOCKED",
            "",
        ]

        # Group by project
        by_project: dict[str, list[Task]] = {}
        for task in tasks:
            by_project.setdefault(task.project, []).append(task)

        for project, project_tasks in sorted(by_project.items()):
            lines.append(f"## {project}")
            lines.append("")
            lines.append("| Task | Description | Status | Agent |")
            lines.append("|------|-------------|--------|-------|")
            for task in sorted(project_tasks, key=lambda t: t.task_id):
                lines.append(f"| {task.task_id} | {task.name} | [{task.status}] | {task.agent} |")
            lines.append("")

        self.master_file.write_text("\n".join(lines), encoding="utf-8")


# ─── Templates ─────────────────────────────────────────────────────────────

_TEMPLATE_TASKS = """# __TASKS.md — DevBoard Multi-Agent Coordination

> **Shared task board for all agents.** Check this file before starting any work.
> Format: `[STATUS] [TASK_ID] — [DESCRIPTION] | Agent: [NAME] | Project: [PROJECT]`
> Status: `[ ]` not started | `[~]` in progress | `[x]` done | `[!]` blocked

---

## 🔴 CRITICAL — Do Not Touch (Other Agent Working)
_If a task is marked `[~]`, another agent is working on it. Do NOT start it._

| Status | Task ID | Description | Agent | Project |
|--------|---------|-------------|-------|---------|

---

## 🟡 IN PROGRESS
_Tasks currently being worked on. Only one agent per task._

| Status | Task ID | Description | Agent | Project |
|--------|---------|-------------|-------|---------|

---

## 🟢 COMPLETED
_Finished tasks moved to JobEnd/_

| Status | Task ID | Description | Agent | Project |
|--------|---------|-------------|-------|---------|

---

## 📋 PROJECT TASK BACKLOG
_Tasks organized by project. Add new tasks here, then move to CRITICAL when ready to start._

### NexusAgent
| Task ID | Description | Priority | Dependencies |
|---------|-------------|----------|--------------|

### ast-tools
| Task ID | Description | Priority | Dependencies |
|---------|-------------|----------|--------------|

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
"""

_TEMPLATE_MASTER = """# MASTER.SCHEDULE.md — DevBoard Progress Tracking

> Single source of truth for all task status. Updated by agents as work progresses.
> Check `__TASKS.md` for the full coordination board.

## Legend
- `[ ]` = NOT STARTED
- `[~]` = IN PROGRESS
- `[x]` = COMPLETED
- `[!]` = BLOCKED

## All Tasks

| Task | Description | Status | Agent | Project |
|------|-------------|--------|-------|---------|
"""

_TEMPLATE_TASK_FILE = """# TASK FILE TEMPLATE

```
[TASK_ID]
[TASK_NAME]
[PHASE]
[PRIORITY]

[DESCRIPTION OF WHAT THIS TASK WILL DO]

## AGENT
[Agent name or "Unassigned"]

## DEPENDENCIES
- [TASK_ID] [TASK_NAME] (must be completed first)

## PROJECT
[Project name or path, e.g., "NexusAgent", "ast-tools"]

## FILES TO MODIFY
- (list files this task will modify)

## FILES TO CREATE
- (list files that will be created)

## ACCEPTANCE CRITERIA
- [ ] (checkable condition 1)
- [ ] (checkable condition 2)

## NOTES
(additional context, constraints, or links)
```

## Field Descriptions

| Field | Description |
|-------|-------------|
| `TASK_ID` | Unique ID (e.g., `NA-0042` for NexusAgent task 42, `AT-0007` for ast-tools task 7) |
| `TASK_NAME` | Short, descriptive name |
| `PHASE` | Project phase or milestone (e.g., `Refactoring`, `Feature Work`, `Bug Fixes`) |
| `PRIORITY` | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `AGENT` | Name of the agent or developer working on this task |
| `DEPENDENCIES` | List of task IDs that must be completed before this one |
| `PROJECT` | Which project this task belongs to |
| `FILES TO MODIFY` | Existing files that will be changed |
| `FILES TO CREATE` | New files that will be created |
| `ACCEPTANCE CRITERIA` | Checkable list of conditions for completion |
| `NOTES` | Any additional context |

## Task ID Convention
- Format: `XX-NNNN` where `XX` is the project abbreviation and `NNNN` is a sequential number
- Project abbreviations: `NA` = NexusAgent, `AT` = ast-tools, `HB` = Hermes, `DB` = DevBoard, `FORGE` = FORGE, `CAT` = CATALYST
- Keep a running counter per project in `MASTER.SCHEDULE.md`
"""

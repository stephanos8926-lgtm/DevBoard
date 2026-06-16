"""DevBoard — Multi-agent shared task board.

File-based kanban with atomic claims, dependency enforcement,
WIP limits, and configurable workflow states.

Reference architecture: kanban-md (antopolskiy/kanban-md)
Task format: YAML frontmatter + Markdown body
Config: config.yml with statuses, priorities, WIP limits, claim_timeout
"""

from __future__ import annotations

__version__ = "1.1.0"

import json
import logging
import os
import random
import re
import string
from dataclasses import dataclass, field
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# ─── Constants ─────────────────────────────────────────────────────────────

CONFIG_FILE = "config.yml"
TASKS_DIR = "tasks"
CLAIM_TIMEOUT_DEFAULT = timedelta(hours=1)

# ─── Classes of Service ────────────────────────────────────────────────────
# Reference: kanban-md classes of service
# Each class has a visual indicator and optional SLA (max time in a status).

CLASS_OF_SERVICE = {
    "expedite": {
        "label": "🚨 Expedite",
        "color": "red",
        "sla_hours": 4,          # Must be completed within 4 hours
        "description": "Drop everything — critical fix needed now",
        "wip_bypass": True,      # Expedite tasks bypass WIP limits
    },
    "fixed-date": {
        "label": "📅 Fixed Date",
        "color": "yellow",
        "sla_hours": None,       # SLA is the due date itself
        "description": "Must be done by a specific date",
        "wip_bypass": False,
    },
    "standard": {
        "label": "📋 Standard",
        "color": "white",
        "sla_hours": 48,         # 2-day SLA
        "description": "Normal priority work",
        "wip_bypass": False,
    },
    "intangible": {
        "label": "💡 Intangible",
        "color": "blue",
        "sla_hours": 168,        # 1-week SLA
        "description": "Tech debt, refactoring, nice-to-have",
        "wip_bypass": False,
    },
}

DEFAULT_CLASS = "standard"

# ─── Data Models ───────────────────────────────────────────────────────────

@dataclass
class Task:
    """A single task in the DevBoard.

    Stored as a Markdown file with YAML frontmatter.
    Reference: kanban-md internal/task/task.go
    """
    task_id: str
    name: str
    status: str = "backlog"
    priority: str = "medium"
    created: str = ""
    updated: str = ""
    started: str = ""
    completed: str = ""
    agent: str = "Unassigned"
    claimed_by: str = ""
    claimed_at: str = ""
    dependencies: list[str] = field(default_factory=list)
    project: str = ""
    cos: str = "standard"  # class of service: expedite, fixed-date, standard, intangible
    tags: list[str] = field(default_factory=list)
    due: str = ""
    body: str = ""
    file_path: str = ""

    def __post_init__(self):
        now = datetime.now(UTC).isoformat()
        if not self.created:
            self.created = now
        self.updated = now

    # ── Status helpers ──

    @property
    def is_available(self) -> bool:
        return self.status == "backlog" and not self.claimed_by

    @property
    def is_claimed(self) -> bool:
        return bool(self.claimed_by)

    @property
    def is_done(self) -> bool:
        return self.status in ("done", "archived")

    @property
    def is_blocked(self) -> bool:
        return self.status == "blocked"

    @property
    def claim_expired(self) -> bool:
        """Check if the claim has expired (based on claimed_at timestamp)."""
        if not self.claimed_at:
            return False
        try:
            claimed_time = datetime.fromisoformat(self.claimed_at)
            return datetime.now(UTC) - claimed_time > CLAIM_TIMEOUT_DEFAULT
        except (ValueError, TypeError):
            return False

    @property
    def is_effectively_available(self) -> bool:
        """Available if unclaimed OR claim has expired."""
        if not self.claimed_by:
            return True
        return self.claim_expired

    # ── Serialization ──

    def to_file_content(self) -> str:
        """Serialize to Markdown file with YAML frontmatter."""
        data = {
            "id": self.task_id,
            "title": self.name,
            "status": self.status,
            "priority": self.priority,
            "created": self.created,
            "updated": self.updated,
        }
        if self.started:
            data["started"] = self.started
        if self.completed:
            data["completed"] = self.completed
        if self.agent and self.agent != "Unassigned":
            data["agent"] = self.agent
        if self.claimed_by:
            data["claimed_by"] = self.claimed_by
            data["claimed_at"] = self.claimed_at
        if self.dependencies:
            data["depends_on"] = self.dependencies
        if self.project:
            data["project"] = self.project
        if self.cos and self.cos != DEFAULT_CLASS:
            data["cos"] = self.cos
        if self.tags:
            data["tags"] = self.tags
        if self.due:
            data["due"] = self.due

        yaml_str = yaml.dump(data, default_flow_style=False, allow_unicode=True)
        content = f"---\n{yaml_str}---\n"
        if self.body:
            content += f"\n{self.body}\n"
        return content

    @classmethod
    def from_file(cls, path: Path) -> Task:
        """Parse a task from a Markdown file with YAML frontmatter."""
        content = path.read_text(encoding="utf-8")

        # Split frontmatter
        if not content.startswith("---\n"):
            raise ValueError(f"Task file {path} does not start with YAML frontmatter")

        parts = content.split("---\n", 2)
        if len(parts) < 3:
            raise ValueError(f"Task file {path} has unclosed frontmatter")

        fm_text = parts[1]
        body = parts[2].lstrip("\n").rstrip("\n")

        data = yaml.safe_load(fm_text) or {}

        return cls(
            task_id=str(data.get("id", "")),
            name=data.get("title", ""),
            status=data.get("status", "backlog"),
            priority=data.get("priority", "medium"),
            created=data.get("created", ""),
            updated=data.get("updated", ""),
            started=data.get("started", ""),
            completed=data.get("completed", ""),
            agent=data.get("agent", "Unassigned"),
            claimed_by=data.get("claimed_by", ""),
            claimed_at=data.get("claimed_at", ""),
            dependencies=data.get("depends_on", []) or [],
            project=data.get("project", ""),
            cos=data.get("cos", "standard"),
            tags=data.get("tags", []) or [],
            due=data.get("due", ""),
            body=body,
            file_path=str(path),
        )


@dataclass
class BoardStats:
    """Statistics for a DevBoard."""
    total: int = 0
    backlog: int = 0
    in_progress: int = 0
    review: int = 0
    done: int = 0
    blocked: int = 0
    by_project: dict[str, int] = field(default_factory=dict)
    by_priority: dict[str, int] = field(default_factory=dict)
    by_agent: dict[str, int] = field(default_factory=dict)
    by_cos: dict[str, int] = field(default_factory=dict)


@dataclass
class FlowStats:
    """Flow metrics for a DevBoard (throughput, lead time, cycle time).

    Reference: kanban flow metrics + Theory of Constraints
    - throughput: tasks completed per time period
    - lead time: creation → completion (total time in system)
    - cycle time: start → completion (active work time)
    - wip: current work in progress
    - littles_law: throughput * lead_time ≈ wip
    """
    throughput_7d: float = 0.0      # tasks completed in last 7 days
    throughput_30d: float = 0.0     # tasks completed in last 30 days
    avg_lead_time_hours: float = 0.0
    avg_cycle_time_hours: float = 0.0
    median_lead_time_hours: float = 0.0
    median_cycle_time_hours: float = 0.0
    current_wip: int = 0
    littles_law_wip: float = 0.0    # predicted WIP from throughput * lead_time
    sla_breaches: int = 0           # count of tasks past SLA
    sla_compliance_pct: float = 100.0


@dataclass
class ActivityEvent:
    """A single activity log entry."""
    timestamp: str = ""
    action: str = ""       # create, claim, complete, move, edit, block, unblock, release
    task_id: str = ""
    agent: str = ""
    detail: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "task_id": self.task_id,
            "agent": self.agent,
            "detail": self.detail,
        }


# ─── Board Manager ─────────────────────────────────────────────────────────

class DevBoard:
    """Manages a DevBoard directory.

    Directory structure (reference: kanban-md):
        DevBoard/
        ├── config.yml          # Board configuration
        ├── tasks/              # Task files (one per task)
        │   ├── 001-fix-tui-streaming.md
        │   └── 002-add-search.md
        ├── activity.jsonl      # Append-only activity log
        ├── __TASKS.md          # Human-readable coordination board
        └── MASTER.SCHEDULE.md  # Auto-generated status tracking
    """

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.tasks_dir = self.root / TASKS_DIR
        self.config_file = self.root / CONFIG_FILE
        self.activity_file = self.root / "activity.jsonl"
        self.tasks_file = self.root / "__TASKS.md"
        self.master_file = self.root / "MASTER.SCHEDULE.md"

    def exists(self) -> bool:
        return self.root.is_dir() and self.config_file.exists()

    # ── Init ──

    def init(self, name: str = "DevBoard") -> None:
        """Initialize a new DevBoard directory."""
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

        # Write config
        if not self.config_file.exists():
            config = {
                "version": 1,
                "board": {"name": name},
                "statuses": ["backlog", "in-progress", "review", "done"],
                "priorities": ["low", "medium", "high", "critical"],
                "wip_limits": {"in-progress": 3, "review": 2},
                "claim_timeout": "1h",
                "defaults": {"status": "backlog", "priority": "medium"},
                "next_id": 1,
            }
            self.config_file.write_text(yaml.dump(config, default_flow_style=False), encoding="utf-8")

        # Write __TASKS.md
        if not self.tasks_file.exists():
            self.tasks_file.write_text(self._template_tasks(), encoding="utf-8")

        # Write MASTER.SCHEDULE.md
        if not self.master_file.exists():
            self.master_file.write_text(self._template_master(), encoding="utf-8")

    # ── Config ──

    def load_config(self) -> dict:
        """Load board configuration with validation."""
        if not self.config_file.exists():
            return {}
        config = yaml.safe_load(self.config_file.read_text()) or {}
        # Validate required keys
        required = ["statuses", "priorities"]
        for key in required:
            if key not in config:
                logger.warning("Config missing required key '%s', using defaults", key)
        return config

    def validate_config(self) -> list[str]:
        """Validate the current config. Returns list of issues."""
        config = self.load_config()
        issues = []
        if not config:
            issues.append("config.yml is empty or missing")
            return issues
        statuses = config.get("statuses", [])
        if not statuses:
            issues.append("statuses is empty")
        wip_limits = config.get("wip_limits", {})
        for status, limit in wip_limits.items():
            if status not in statuses:
                issues.append(f"WIP limit for '{status}' references non-existent status")
            if not isinstance(limit, int) or limit < 0:
                issues.append(f"WIP limit for '{status}' must be a non-negative integer")
        priorities = config.get("priorities", [])
        if not priorities:
            issues.append("priorities is empty")
        for cos_name, cos_cfg in CLASS_OF_SERVICE.items():
            if "sla_hours" in cos_cfg and cos_cfg["sla_hours"] is not None:
                if not isinstance(cos_cfg["sla_hours"], (int, float)) or cos_cfg["sla_hours"] <= 0:
                    issues.append(f"Class of service '{cos_name}' has invalid sla_hours")
        return issues

    def validate_status(self, status: str) -> bool:
        """Check if a status is valid per config."""
        config = self.load_config()
        statuses = config.get("statuses", ["backlog", "in-progress", "review", "done"])
        return status in statuses

    def save_config(self, config: dict) -> None:
        """Save board configuration."""
        self.config_file.write_text(yaml.dump(config, default_flow_style=False), encoding="utf-8")

    def next_id(self) -> int:
        """Get and increment the next task ID."""
        config = self.load_config()
        nid = config.get("next_id", 1)
        config["next_id"] = nid + 1
        self.save_config(config)
        return nid

    # ── Task CRUD ──

    def load_tasks(self) -> list[Task]:
        """Load all task files from tasks directory."""
        tasks = []
        if not self.tasks_dir.exists():
            return tasks

        for task_file in sorted(self.tasks_dir.iterdir()):
            if task_file.suffix == ".md" and not task_file.name.startswith("."):
                try:
                    task = Task.from_file(task_file)
                    tasks.append(task)
                except Exception as e:
                    logger.warning("Skipping malformed task file %s: %s", task_file.name, e)
        return tasks

    def find_task(self, task_id: str) -> Optional[Task]:
        """Find a task by ID."""
        for task in self.load_tasks():
            if task.task_id == task_id:
                return task
        return None

    def save_task(self, task: Task) -> Path:
        """Save a task to a file. Handles renames by removing old file."""
        # Generate filename: 001-task-name.md
        safe_name = re.sub(r"[^a-z0-9]+", "-", task.name.lower()).strip("-")
        filename = f"{task.task_id}_{safe_name}.md"
        path = self.tasks_dir / filename

        # Remove old file if filename changed
        if task.file_path:
            old_path = Path(task.file_path)
            if old_path.exists() and old_path != path:
                old_path.unlink()

        path.write_text(task.to_file_content(), encoding="utf-8")
        task.file_path = str(path)
        return path

    # ── Claim (atomic) ──

    def claim_task(self, task_id: str, agent: str, timeout: timedelta = CLAIM_TIMEOUT_DEFAULT) -> Optional[Path]:
        """Claim a task for an agent. Returns path or None if unavailable.

        Uses atomic check-and-write to prevent TOCTOU races.
        Reference: kanban-md cmd/pick.go executePick()
        """
        task = self.find_task(task_id)
        if not task:
            return None

        # Check availability (including claim expiration)
        if not task.is_effectively_available:
            return None

        # Check dependencies
        if not self._deps_satisfied(task):
            return None

        # Check WIP limits (expedite tasks bypass WIP limits)
        config = self.load_config()
        wip_limits = config.get("wip_limits", {})
        cos_config = CLASS_OF_SERVICE.get(task.cos, CLASS_OF_SERVICE[DEFAULT_CLASS])
        if not cos_config.get("wip_bypass", False):
            current_ip = sum(1 for t in self.load_tasks() if t.status == "in-progress" and t.claimed_by == agent)
            agent_limit = wip_limits.get("in-progress", 0)
            if agent_limit > 0 and current_ip >= agent_limit:
                logger.info("Agent %s at WIP limit (%d/%d)", agent, current_ip, agent_limit)
                return None

        # Claim the task
        now = datetime.now(UTC)
        task.claimed_by = agent
        task.claimed_at = now.isoformat()
        task.agent = agent
        task.status = "in-progress"
        task.started = now.isoformat()
        task.updated = now.isoformat()

        path = self.save_task(task)
        self._log_activity("claim", task_id, agent)
        self._update_master()
        return path

    def release_claim(self, task_id: str, agent: str) -> bool:
        """Release a claim on a task."""
        task = self.find_task(task_id)
        if not task or task.claimed_by != agent:
            return False

        task.claimed_by = ""
        task.claimed_at = ""
        task.updated = datetime.now(UTC).isoformat()
        self.save_task(task)
        self._log_activity("release", task_id, agent)
        return True

    # ── Complete ──

    def complete_task(self, task_id: str, agent: str) -> Optional[Path]:
        """Mark a task as completed. Only the claiming agent can complete."""
        task = self.find_task(task_id)
        if not task:
            return None
        if task.claimed_by != agent:
            logger.warning("Agent %s cannot complete task %s (claimed by %s)", agent, task_id, task.claimed_by)
            return None

        now = datetime.now(UTC)
        task.status = "done"
        task.completed = now.isoformat()
        task.updated = now.isoformat()

        path = self.save_task(task)
        self._log_activity("complete", task_id, agent)

        # Auto-unblock tasks that depend on this one
        self._auto_unblock(task_id)

        self._update_master()
        return path

    # ── Dependencies ──

    def _deps_satisfied(self, task: Task) -> bool:
        """Check if all dependencies are in 'done' status."""
        if not task.dependencies:
            return True
        for dep_id in task.dependencies:
            dep = self.find_task(dep_id)
            if not dep or dep.status != "done":
                return False
        return True

    def _detect_cycle(self, task_id: str, visited: set[str] | None = None) -> bool:
        """Detect if adding/keeping a dependency would create a cycle. Returns True if cycle found."""
        if visited is None:
            visited = set()
        if task_id in visited:
            return True
        visited.add(task_id)
        task = self.find_task(task_id)
        if not task:
            return False
        for dep_id in task.dependencies:
            if self._detect_cycle(dep_id, visited.copy()):
                return True
        return False

    def check_dependency_cycles(self) -> list[str]:
        """Check all tasks for dependency cycles. Returns list of task IDs with cycles."""
        cycles = []
        for task in self.load_tasks():
            if self._detect_cycle(task.task_id):
                cycles.append(task.task_id)
        return cycles

    def _auto_unblock(self, completed_task_id: str) -> None:
        """Auto-unblock tasks whose dependencies are now satisfied."""
        for task in self.load_tasks():
            if task.status == "blocked" and completed_task_id in task.dependencies:
                if self._deps_satisfied(task):
                    task.status = "backlog"
                    task.updated = datetime.now(UTC).isoformat()
                    self.save_task(task)
                    self._log_activity("unblock", task.task_id, "system", f"Dependency {completed_task_id} completed")

    # ── Move ──

    def move_task(self, task_id: str, new_status: str, agent: str = "") -> bool:
        """Move a task to a new status. Validates status against config."""
        task = self.find_task(task_id)
        if not task:
            return False

        # Validate the new status
        if not self.validate_status(new_status):
            logger.warning("Invalid status '%s' — not in configured statuses", new_status)
            return False

        old_status = task.status
        task.status = new_status
        task.updated = datetime.now(UTC).isoformat()

        # Auto-set timestamps
        if new_status == "in-progress" and not task.started:
            task.started = datetime.now(UTC).isoformat()
        if new_status == "done":
            task.completed = datetime.now(UTC).isoformat()
            self._auto_unblock(task_id)

        self.save_task(task)
        self._log_activity("move", task_id, agent, f"{old_status} -> {new_status}")
        self._update_master()
        return True

    # ── Add ──

    def add_task(self, name: str, phase: str = "", priority: str = "medium",
                 description: str = "", project: str = "", agent: str = "Unassigned",
                 dependencies: Optional[list[str]] = None, tags: Optional[list[str]] = None,
                 cos: str = DEFAULT_CLASS, due: str = "") -> Task:
        """Add a new task to the board."""
        task_id = str(self.next_id())
        task = Task(
            task_id=task_id,
            name=name,
            status="backlog",
            priority=priority,
            project=project,
            agent=agent,
            dependencies=dependencies or [],
            tags=tags or [],
            cos=cos,
            body=description,
            due=due,
        )
        self.save_task(task)
        self._log_activity("create", task_id, agent)
        self._update_master()
        return task

    # ── Pick (atomic find + claim) ──

    def pick_task(self, agent: str, status: str = "backlog", tags: Optional[list[str]] = None) -> Optional[Task]:
        """Atomically find and claim the next available task.

        Reference: kanban-md internal/board/pick.go Pick()
        Priority: critical > high > medium > low
        """
        tasks = self.load_tasks()
        candidates = []

        for task in tasks:
            if task.status != status:
                continue
            if not task.is_effectively_available:
                continue
            if not self._deps_satisfied(task):
                continue
            if tags and not any(t in task.tags for t in tags):
                continue
            candidates.append(task)

        if not candidates:
            return None

        # Sort by priority (critical first)
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        candidates.sort(key=lambda t: priority_order.get(t.priority, 99))

        # Claim the highest-priority task
        best = candidates[0]
        result = self.claim_task(best.task_id, agent)
        if result:
            return best
        return None

    # ── Stats ──

    def get_stats(self) -> BoardStats:
        """Get board statistics."""
        tasks = self.load_tasks()
        stats = BoardStats(total=len(tasks))

        for task in tasks:
            if task.status == "backlog":
                stats.backlog += 1
            elif task.status == "in-progress":
                stats.in_progress += 1
            elif task.status == "review":
                stats.review += 1
            elif task.status == "done":
                stats.done += 1
            elif task.status == "blocked":
                stats.blocked += 1

            stats.by_project[task.project] = stats.by_project.get(task.project, 0) + 1
            stats.by_priority[task.priority] = stats.by_priority.get(task.priority, 0) + 1
            if task.agent and task.agent != "Unassigned":
                stats.by_agent[task.agent] = stats.by_agent.get(task.agent, 0) + 1
            if task.cos:
                stats.by_cos[task.cos] = stats.by_cos.get(task.cos, 0) + 1

        return stats

    # ── Flow Metrics ──────────────────────────────────────────────────────────

    def get_flow_metrics(self, window_days: int = 30) -> FlowStats:
        """Calculate flow metrics for the board.

        Reference: Actionable Agile / kanban flow metrics
        - Throughput: completed per day
        - Lead time: created → done (hours)
        - Cycle time: started → done (hours)
        - SLA compliance: % of tasks within class-of-service SLA
        """
        import statistics

        tasks = self.load_tasks()
        stats = FlowStats()
        now = datetime.now(UTC)

        # Current WIP
        stats.current_wip = sum(1 for t in tasks if t.status == "in-progress")

        # Completed tasks in window
        completed_tasks = []
        for t in tasks:
            if not t.completed or t.status != "done":
                continue
            try:
                completed_at = datetime.fromisoformat(t.completed)
                age_days = (now - completed_at).total_seconds() / 86400
                if age_days <= window_days:
                    completed_tasks.append((t, completed_at))
            except (ValueError, TypeError):
                continue

        # Throughput
        cutoff_7d = now - timedelta(days=7)
        cutoff_30d = now - timedelta(days=30)
        count_7d = sum(1 for _, ca in completed_tasks if ca >= cutoff_7d)
        count_30d = sum(1 for _, ca in completed_tasks if ca >= cutoff_30d)
        stats.throughput_7d = round(count_7d / 7, 2)
        stats.throughput_30d = round(count_30d / 30, 2)

        # Lead time and cycle time
        lead_times = []
        cycle_times = []
        sla_breaches = 0
        sla_total = 0

        for t, completed_at in completed_tasks:
            try:
                created_at = datetime.fromisoformat(t.created) if t.created else None
                started_at = datetime.fromisoformat(t.started) if t.started else None

                if created_at:
                    lt_hours = (completed_at - created_at).total_seconds() / 3600
                    lead_times.append(lt_hours)

                    # SLA check
                    sla_total += 1
                    cos_cfg = CLASS_OF_SERVICE.get(t.cos, CLASS_OF_SERVICE[DEFAULT_CLASS])
                    sla_hours = cos_cfg.get("sla_hours")
                    if sla_hours and lt_hours > sla_hours:
                        sla_breaches += 1

                if started_at:
                    ct_hours = (completed_at - started_at).total_seconds() / 3600
                    cycle_times.append(ct_hours)
            except (ValueError, TypeError):
                continue

        if lead_times:
            stats.avg_lead_time_hours = round(statistics.mean(lead_times), 1)
            stats.median_lead_time_hours = round(statistics.median(lead_times), 1)
        if cycle_times:
            stats.avg_cycle_time_hours = round(statistics.mean(cycle_times), 1)
            stats.median_cycle_time_hours = round(statistics.median(cycle_times), 1)

        # Little's Law: predicted WIP = throughput * lead_time
        if stats.avg_lead_time_hours > 0 and stats.throughput_30d > 0:
            daily_throughput = stats.throughput_30d
            stats.littles_law_wip = round(daily_throughput * (stats.avg_lead_time_hours / 24), 1)

        stats.sla_breaches = sla_breaches
        if sla_total > 0:
            stats.sla_compliance_pct = round((sla_total - sla_breaches) / sla_total * 100, 1)

        return stats

    # ── Activity Log ──

    def _log_activity(self, action: str, task_id: str, agent: str = "", detail: str = "") -> None:
        """Append an entry to the activity log."""
        event = ActivityEvent(action=action, task_id=task_id, agent=agent, detail=detail)
        with open(self.activity_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

    def get_activity(self, limit: int = 50, action: str = "", task_id: str = "") -> list[dict]:
        """Get activity log entries."""
        if not self.activity_file.exists():
            return []

        entries = []
        with open(self.activity_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if action and entry.get("action") != action:
                        continue
                    if task_id and entry.get("task_id") != task_id:
                        continue
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue

        return entries[-limit:]

    # ── Agent Identity ──

    def generate_agent_name(self) -> str:
        """Generate a random two-word agent name. Reference: kanban-md cmd/agent_name.go"""
        adjectives = [
            "quiet", "swift", "bright", "calm", "bold", "keen", "warm", "cool",
            "sharp", "soft", "wild", "fast", "slow", "deep", "high", "low",
            "dark", "light", "old", "new", "red", "blue", "green", "gold",
        ]
        nouns = [
            "storm", "river", "flame", "frost", "leaf", "stone", "wave", "wind",
            "cloud", "forest", "meadow", "thunder", "shadow", "sunrise", "moonlight",
            "crystal", "ember", "oak", "maple", "falcon", "wolf", "tiger", "phoenix",
        ]
        return f"{random.choice(adjectives)}-{random.choice(nouns)}"

    # ── Master Update ──

    def _update_master(self) -> None:
        """Regenerate MASTER.SCHEDULE.md from current tasks."""
        tasks = self.load_tasks()
        stats = self.get_stats()

        lines = [
            "# MASTER.SCHEDULE.md — DevBoard Progress Tracking",
            "",
            f"> Last updated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"> Total: {stats.total} | Backlog: {stats.backlog} | In Progress: {stats.in_progress} | Review: {stats.review} | Done: {stats.done} | Blocked: {stats.blocked}",
            "",
            "## Legend",
            "- `[ ]` = Backlog (not started)",
            "- `[~]` = In Progress (claimed by agent)",
            "- `[r]` = Review (waiting for merge/approval)",
            "- `[x]` = Done (completed)",
            "- `[!]` = Blocked",
            "",
        ]

        # Group by project
        by_project: dict[str, list[Task]] = {}
        for task in tasks:
            by_project.setdefault(task.project or "Uncategorized", []).append(task)

        for project, project_tasks in sorted(by_project.items()):
            lines.append(f"## {project}")
            lines.append("")
            lines.append("| ID | Title | Status | Priority | Agent |")
            lines.append("|----|-------|--------|----------|-------|")
            for task in sorted(project_tasks, key=lambda t: t.task_id):
                status_marker = {
                    "backlog": "[ ]",
                    "in-progress": "[~]",
                    "review": "[r]",
                    "done": "[x]",
                    "blocked": "[!]",
                }.get(task.status, "[ ]")
                lines.append(f"| {task.task_id} | {task.name} | {status_marker} | {task.priority} | {task.agent} |")
            lines.append("")

        self.master_file.write_text("\n".join(lines), encoding="utf-8")

    # ── Templates ──

    def _template_tasks(self) -> str:
        return """# __TASKS.md — DevBoard Multi-Agent Coordination

> **Shared task board for all agents.** Check this file before starting any work.
> Status: `[ ]` backlog | `[~]` in progress | `[r]` review | `[x]` done | `[!]` blocked

---

## 🔴 ACTIVE — Do Not Touch (Other Agent Working)
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
_Finished tasks._

| Status | Task ID | Description | Agent | Project |
|--------|---------|-------------|-------|---------|

---

## 🤖 AGENT PROTOCOL

### Before Starting Any Task
1. **Check this file** — is the task already `[~]`? If yes, pick a different task.
2. **Check dependencies** — are all deps `[x]`? If no, pick a different task.
3. **Claim the task** — use `devboard claim <id> --agent <name>` or `devboard pick --agent <name>`.
4. **One task at a time** — respect WIP limits.

### While Working
- Update the task body with progress notes
- If blocked, use `devboard edit <id> --block "reason"`

### After Completion
1. `devboard complete <id>`
2. Commit with message: `devboard: [TASK_ID] [x] — [brief description]`

### Coordination Rules
- **Never modify a task file that belongs to another agent**
- **Never start a task marked `[~]`** — find something else
- **Always update this file first** before doing any work
- **Claims expire after 1 hour** — refresh with `devboard edit <id> --claim <name>`
"""

    def _template_master(self) -> str:
        return """# MASTER.SCHEDULE.md — DevBoard Progress Tracking

> Auto-generated. Do not edit manually.

## Legend
- `[ ]` = Backlog (not started)
- `[~]` = In Progress (claimed by agent)
- `[r]` = Review (waiting for merge/approval)
- `[x]` = Done (completed)
- `[!]` = Blocked

## All Tasks

| ID | Title | Status | Priority | Agent |
|----|-------|--------|----------|-------|
"""

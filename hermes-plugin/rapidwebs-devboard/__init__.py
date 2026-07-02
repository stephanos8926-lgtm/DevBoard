"""DevBoard Hermes Plugin v1.1.0.

Multi-agent shared task board coordination.
Registers LLM-callable tools for task management.
Hooks into session lifecycle to show board status.

Reference: kanban-md v0.33.0 plugin architecture
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from devboard import DevBoard, Task

logger = logging.getLogger(__name__)


# ─── Plugin Entry Point ────────────────────────────────────────────────────

def register(ctx):
    """Register DevBoard tools and hooks with Hermes."""
    ctx.register_tool("devboard_status", _tool_status, _SCHEMA_STATUS)
    ctx.register_tool("devboard_pick", _tool_pick, _SCHEMA_PICK)
    ctx.register_tool("devboard_claim", _tool_claim, _SCHEMA_CLAIM)
    ctx.register_tool("devboard_complete", _tool_complete, _SCHEMA_COMPLETE)
    ctx.register_tool("devboard_add", _tool_add, _SCHEMA_ADD)
    ctx.register_tool("devboard_show", _tool_show, _SCHEMA_SHOW)
    ctx.register_tool("devboard_move", _tool_move, _SCHEMA_MOVE)
    ctx.register_tool("devboard_log", _tool_log, _SCHEMA_LOG)
    ctx.register_tool("devboard_agent_name", _tool_agent_name, _SCHEMA_AGENT_NAME)
    ctx.register_hook("on_session_start", _hook_session_start)
    ctx.register_hook("on_session_end", _hook_session_end)
    logger.info("DevBoard v1.1.0 plugin registered — 8 tools, 2 hooks")


# ─── Tool Schemas ──────────────────────────────────────────────────────────

_SCHEMA_STATUS = {
    "type": "object",
    "properties": {
        "cwd": {"type": "string", "description": "Project root directory"},
        "compact": {"type": "boolean", "description": "Compact output (token-efficient)"},
    },
    "required": [],
}

_SCHEMA_PICK = {
    "type": "object",
    "properties": {
        "claim": {"type": "string", "description": "Agent name to claim as (required)"},
        "status": {"type": "string", "description": "Source status (default: backlog)"},
        "tags": {"type": "string", "description": "Filter by tags (comma-separated)"},
        "cwd": {"type": "string", "description": "Project root directory"},
    },
    "required": ["claim"],
}

_SCHEMA_CLAIM = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string", "description": "Task ID to claim"},
        "claim": {"type": "string", "description": "Agent name"},
        "cwd": {"type": "string", "description": "Project root directory"},
    },
    "required": ["task_id", "claim"],
}

_SCHEMA_COMPLETE = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string", "description": "Task ID to complete"},
        "claim": {"type": "string", "description": "Your agent name (must be claimant)"},
        "cwd": {"type": "string", "description": "Project root directory"},
    },
    "required": ["task_id", "claim"],
}

_SCHEMA_ADD = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Task title (required)"},
        "priority": {"type": "string", "Description": "low, medium, high, critical (default: medium)"},
        "description": {"type": "string", "description": "Task description"},
        "project": {"type": "string", "description": "Project name"},
        "tags": {"type": "string", "description": "Comma-separated tags"},
        "cwd": {"type": "string", "description": "Project root directory"},
    },
    "required": ["title"],
}

_SCHEMA_SHOW = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string", "description": "Task ID to show"},
        "cwd": {"type": "string", "description": "Project root directory"},
    },
    "required": ["task_id"],
}

_SCHEMA_MOVE = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string", "description": "Task ID to move"},
        "status": {"type": "string", "description": "New status (backlog, in-progress, review, done, blocked)"},
        "cwd": {"type": "string", "description": "Project root directory"},
    },
    "required": ["task_id", "status"],
}

_SCHEMA_LOG = {
    "type": "object",
    "properties": {
        "limit": {"type": "integer", "description": "Max entries (default: 20)"},
        "action": {"type": "string", "description": "Filter by action type"},
        "cwd": {"type": "string", "description": "Project root directory"},
    },
    "required": [],
}

_SCHEMA_AGENT_NAME = {
    "type": "object",
    "properties": {
        "cwd": {"type": "string", "description": "Project root directory"},
    },
    "required": [],
}


# ─── Tool Implementations ──────────────────────────────────────────────────

def _find_board(cwd: str) -> DevBoard | None:
    """Find a DevBoard by searching upward from cwd."""
    path = Path(cwd).resolve()
    for p in [path] + list(path.parents):
        board = DevBoard(p)
        if board.exists():
            return board
    return None


def _tool_status(args: dict[str, Any]) -> dict[str, Any]:
    cwd = args.get("cwd", ".")
    compact = args.get("compact", False)
    board = _find_board(cwd)
    if not board:
        return {"error": "No DevBoard found", "hint": "Run 'devboard init' first"}

    stats = board.get_stats()
    if compact:
        return {
            "total": stats.total,
            "backlog": stats.backlog,
            "in_progress": stats.in_progress,
            "done": stats.done,
        }

    tasks = board.load_tasks()
    return {
        "total": stats.total,
        "backlog": stats.backlog,
        "in_progress": stats.in_progress,
        "review": stats.review,
        "done": stats.done,
        "blocked": stats.blocked,
        "tasks": [
            {
                "id": t.task_id,
                "title": t.name,
                "status": t.status,
                "priority": t.priority,
                "agent": t.agent,
                "project": t.project,
            }
            for t in sorted(tasks, key=lambda x: (x.status, x.task_id))
        ],
    }


def _tool_pick(args: dict[str, Any]) -> dict[str, Any]:
    cwd = args.get("cwd", ".")
    agent = args["claim"]
    status = args.get("status", "backlog")
    tags = [t.strip() for t in args.get("tags", "").split(",") if t.strip()] or None

    board = _find_board(cwd)
    if not board:
        return {"error": "No DevBoard found"}

    task = board.pick_task(agent=agent, status=status, tags=tags)
    if task:
        return {
            "success": True,
            "task_id": task.task_id,
            "title": task.name,
            "priority": task.priority,
            "agent": agent,
        }
    return {"success": False, "error": "No unblocked, unclaimed tasks found"}


def _tool_claim(args: dict[str, Any]) -> dict[str, Any]:
    cwd = args.get("cwd", ".")
    task_id = args["task_id"]
    agent = args["claim"]

    board = _find_board(cwd)
    if not board:
        return {"error": "No DevBoard found"}

    result = board.claim_task(task_id, agent)
    if result:
        return {"success": True, "task_id": task_id, "agent": agent}
    return {"success": False, "error": f"Task {task_id} not available"}


def _tool_complete(args: dict[str, Any]) -> dict[str, Any]:
    cwd = args.get("cwd", ".")
    task_id = args["task_id"]
    agent = args["claim"]

    board = _find_board(cwd)
    if not board:
        return {"error": "No DevBoard found"}

    result = board.complete_task(task_id, agent)
    if result:
        return {"success": True, "task_id": task_id}
    return {"success": False, "error": f"Task {task_id} not claimed by {agent} or not found"}


def _tool_add(args: dict[str, Any]) -> dict[str, Any]:
    cwd = args.get("cwd", ".")
    board = _find_board(cwd)
    if not board:
        return {"error": "No DevBoard found"}

    task = board.add_task(
        name=args["title"],
        priority=args.get("priority", "medium"),
        description=args.get("description", ""),
        project=args.get("project", ""),
        tags=[t.strip() for t in args.get("tags", "").split(",") if t.strip()],
    )
    return {"success": True, "task_id": task.task_id, "title": task.name}


def _tool_show(args: dict[str, Any]) -> dict[str, Any]:
    cwd = args.get("cwd", ".")
    task_id = args["task_id"]

    board = _find_board(cwd)
    if not board:
        return {"error": "No DevBoard found"}

    task = board.find_task(task_id)
    if task:
        return {
            "task_id": task.task_id,
            "title": task.name,
            "status": task.status,
            "priority": task.priority,
            "agent": task.agent,
            "project": task.project,
            "claimed_by": task.claimed_by,
            "dependencies": task.dependencies,
            "tags": task.tags,
            "body": task.body,
        }
    return {"error": f"Task {task_id} not found"}


def _tool_move(args: dict[str, Any]) -> dict[str, Any]:
    cwd = args.get("cwd", ".")
    task_id = args["task_id"]
    new_status = args["status"]

    board = _find_board(cwd)
    if not board:
        return {"error": "No DevBoard found"}

    if board.move_task(task_id, new_status):
        return {"success": True, "task_id": task_id, "new_status": new_status}
    return {"error": f"Task {task_id} not found"}


def _tool_log(args: dict[str, Any]) -> dict[str, Any]:
    cwd = args.get("cwd", ".")
    limit = args.get("limit", 20)
    action = args.get("action", "")

    board = _find_board(cwd)
    if not board:
        return {"error": "No DevBoard found"}

    entries = board.get_activity(limit=limit, action=action)
    return {"entries": entries}


def _tool_agent_name(args: dict[str, Any]) -> dict[str, Any]:
    cwd = args.get("cwd", ".")
    board = _find_board(cwd)
    if not board:
        # Generate even without a board
        import random
        adj = ["quiet", "swift", "bright", "calm", "bold", "keen", "warm", "cool"]
        nouns = ["storm", "river", "flame", "frost", "leaf", "stone", "wave"]
        return {"name": f"{random.choice(adj)}-{random.choice(nouns)}"}

    return {"name": board.generate_agent_name()}


# ─── Hooks ─────────────────────────────────────────────────────────────────

def _hook_session_start(session_id: str = "", **kwargs: Any) -> None:
    """Show DevBoard status at session start."""
    board = _find_board(".")
    if not board:
        return
    stats = board.get_stats()
    if stats.total > 0:
        logger.info(
            "DevBoard: %d tasks (%d backlog, %d in-progress, %d done)",
            stats.total, stats.backlog, stats.in_progress, stats.done,
        )


def _hook_session_end(session_id: str = "", completed: bool = True, **kwargs: Any) -> None:
    """Auto-update MASTER.SCHEDULE.md at session end."""
    board = _find_board(".")
    if board and board.exists():
        board._update_master()
        logger.info("DevBoard MASTER.SCHEDULE.md updated")

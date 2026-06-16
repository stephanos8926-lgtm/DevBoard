"""DevBoard CLI — command-line interface for the multi-agent task board.

Commands: init, add, list, show, pick, claim, complete, move, edit, log, board, agent-name
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from devboard import DevBoard, Task, __version__

console = Console()


def get_board() -> DevBoard:
    """Get the DevBoard instance, searching upward from cwd."""
    cwd = Path.cwd()
    for path in [cwd] + list(cwd.parents):
        board = DevBoard(path)
        if board.exists():
            return board
    return DevBoard(cwd)


def output(data: dict, as_json: bool) -> None:
    """Output data as JSON or rich format."""
    if as_json:
        console.print(_json.dumps(data, indent=2, default=str))
    # If not JSON, the caller handles rich output


# ─── Main Group ────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version=__version__)
def main():
    """DevBoard — Multi-agent shared task board."""
    pass


# ─── Init ──────────────────────────────────────────────────────────────────

@main.command()
@click.argument("path", default=".", required=False)
@click.option("--name", default="DevBoard", help="Board name")
@click.option("--statuses", default=None, help="Comma-separated status list")
@click.option("--wip-limit", "wip_limit", default=None, type=int, help="Global WIP limit for in-progress")
@click.option("--claim-timeout", "claim_timeout", default="1h", help="Claim timeout (e.g., 1h, 30m)")
@click.option("--agent", "agent_name", default=None, help="Your agent name (stored in config)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def init(path: str, name: str, statuses: str | None, wip_limit: int | None,
         claim_timeout: str, agent_name: str | None, as_json: bool):
    """Initialize a new DevBoard directory.

    Creates a config.yml, tasks/ directory, and initial board files.
    Run this at the root of your project to start tracking tasks.

    Examples:

        devboard init

        devboard init --name "My Project"

        devboard init --statuses "backlog,todo,doing,done"

        devboard init --wip-limit 5 --claim-timeout 2h
    """
    board = DevBoard(path)
    if board.exists():
        if as_json:
            console.print(_json.dumps({"error": "DevBoard already exists", "path": str(board.root)}))
        else:
            console.print(f"[yellow]DevBoard already exists at {board.root}[/yellow]")
        return

    # Build config
    status_list = [s.strip() for s in statuses.split(",")] if statuses else ["backlog", "in-progress", "review", "done"]
    wip_limits = {"in-progress": 3, "review": 2}
    if wip_limit is not None:
        wip_limits["in-progress"] = wip_limit

    config = {
        "version": 1,
        "board": {"name": name},
        "statuses": status_list,
        "priorities": ["low", "medium", "high", "critical"],
        "wip_limits": wip_limits,
        "claim_timeout": claim_timeout,
        "defaults": {"status": "backlog", "priority": "medium"},
        "next_id": 1,
    }
    if agent_name:
        config["agent"] = agent_name

    # Write config
    board.tasks_dir.mkdir(parents=True, exist_ok=True)
    board.config_file.write_text(
        __import__("yaml").dump(config, default_flow_style=False), encoding="utf-8"
    )

    # Write __TASKS.md
    board.tasks_file.write_text(board._template_tasks(), encoding="utf-8")

    # Write MASTER.SCHEDULE.md
    board.master_file.write_text(board._template_master(), encoding="utf-8")

    if as_json:
        console.print(_json.dumps({
            "success": True,
            "path": str(board.root),
            "config": config,
        }, indent=2))
    else:
        console.print(f"[green]✓ DevBoard initialized at {board.root}[/green]")
        console.print(f"  Statuses: {', '.join(status_list)}")
        console.print(f"  WIP limit (in-progress): {wip_limits['in-progress']}")
        console.print(f"  Claim timeout: {claim_timeout}")
        console.print(f"  Run [bold]devboard status[/bold] to see the board")


# ─── Status ────────────────────────────────────────────────────────────────

@main.command("status")
@click.option("--compact", is_flag=True, help="Compact output (token-efficient)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def cmd_status(compact: bool, as_json: bool):
    """Show the current board status."""
    board = get_board()
    if not board.exists():
        if as_json:
            console.print(_json.dumps({"error": "No DevBoard found", "hint": "Run 'devboard init' first"}))
        else:
            console.print("[red]No DevBoard found. Run 'devboard init' first.[/red]")
        sys.exit(1)

    stats = board.get_stats()

    if as_json:
        tasks = board.load_tasks()
        output({
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
                    "claimed_by": t.claimed_by,
                    "dependencies": t.dependencies,
                    "tags": t.tags,
                    "cos": t.cos,
                }
                for t in sorted(tasks, key=lambda x: (x.status, x.task_id))
            ],
        }, as_json)
        return

    if compact:
        console.print(f"Total: {stats.total} | Backlog: {stats.backlog} | IP: {stats.in_progress} | Done: {stats.done}")
        return

    summary = (
        f"Total: [bold]{stats.total}[/bold] | "
        f"[dim]Backlog: {stats.backlog}[/dim] | "
        f"[yellow]In Progress: {stats.in_progress}[/yellow] | "
        f"[blue]Review: {stats.review}[/blue] | "
        f"[green]Done: {stats.done}[/green] | "
        f"[red]Blocked: {stats.blocked}[/red]"
    )
    console.print(Panel(summary, title="DevBoard Status", border_style="blue"))

    tasks = board.load_tasks()
    if not tasks:
        console.print("\n[dim]No tasks yet. Use 'devboard add' to create one.[/dim]")
        return

    table = Table(box=box.ROUNDED, show_lines=False)
    table.add_column("ID", width=8)
    table.add_column("Title", min_width=20)
    table.add_column("Status", width=12)
    table.add_column("Priority", width=10)
    table.add_column("Agent", width=12)

    for task in sorted(tasks, key=lambda t: (t.status, t.task_id)):
        status_style = {
            "backlog": "dim",
            "in-progress": "yellow",
            "review": "blue",
            "done": "green",
            "blocked": "red",
        }.get(task.status, "white")

        status_label = {
            "backlog": "[ ]",
            "in-progress": "[~]",
            "review": "[r]",
            "done": "[x]",
            "blocked": "[!]",
        }.get(task.status, "[ ]")

        table.add_row(
            task.task_id,
            task.name,
            f"[{status_style}]{status_label} {task.status}[/{status_style}]",
            task.priority,
            task.agent,
        )

    console.print(table)


# ─── Add ───────────────────────────────────────────────────────────────────

@main.command()
@click.argument("title")
@click.option("--priority", default="medium", type=click.Choice(["low", "medium", "high", "critical"]))
@click.option("--project", default="", help="Project name")
@click.option("--description", default="", help="Task description")
@click.option("--agent", default="Unassigned", help="Assigned agent")
@click.option("--tags", default="", help="Comma-separated tags")
@click.option("--depends-on", "depends_on", default="", help="Comma-separated task IDs")
@click.option("--cos", "cos", default="standard", type=click.Choice(["expedite", "fixed-date", "standard", "intangible"]))
@click.option("--due", default="", help="Due date (ISO 8601)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def add(title: str, priority: str, project: str, description: str, agent: str, tags: str,
        depends_on: str, cos: str, due: str, as_json: bool):
    """Add a new task to the board."""
    board = get_board()
    if not board.exists():
        if as_json:
            console.print(_json.dumps({"error": "No DevBoard found"}))
        else:
            console.print("[red]No DevBoard found. Run 'devboard init' first.[/red]")
        sys.exit(1)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    dep_list = [d.strip() for d in depends_on.split(",") if d.strip()] if depends_on else []

    # Check for dependency cycles
    task = board.add_task(
        name=title,
        priority=priority,
        description=description,
        project=project,
        agent=agent,
        dependencies=dep_list,
        tags=tag_list,
        cos=cos,
        due=due,
    )

    # Check if this created a cycle
    cycles = board.check_dependency_cycles()
    if cycles:
        if as_json:
            console.print(_json.dumps({
                "warning": "Dependency cycle detected",
                "cycle_tasks": cycles,
                "task_id": task.task_id,
            }))
        else:
            console.print(f"[yellow]⚠ Dependency cycle detected involving tasks: {', '.join(cycles)}[/yellow]")

    if as_json:
        console.print(_json.dumps({
            "success": True,
            "task_id": task.task_id,
            "title": task.name,
        }, indent=2))
    else:
        console.print(f"[green]✓ Task {task.task_id} added[/green]: {task.name}")


# ─── List ──────────────────────────────────────────────────────────────────

@main.command()
@click.option("--status", default="", help="Filter by status (comma-separated)")
@click.option("--priority", default="", help="Filter by priority")
@click.option("--agent", default="", help="Filter by agent")
@click.option("--project", default="", help="Filter by project")
@click.option("--tag", default="", help="Filter by tag")
@click.option("--blocked", is_flag=True, help="Show only blocked tasks")
@click.option("--sort", default="id", help="Sort by: id, status, priority, created")
@click.option("--reverse", "-r", is_flag=True, help="Reverse sort")
@click.option("--limit", "-n", default=0, help="Max results (0=unlimited)")
@click.option("--compact", is_flag=True, help="Compact one-line per task")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_tasks(status: str, priority: str, agent: str, project: str, tag: str,
               blocked: bool, sort: str, reverse: bool, limit: int, compact: bool, as_json: bool):
    """List tasks with filtering and sorting."""
    board = get_board()
    if not board.exists():
        if as_json:
            console.print(_json.dumps({"error": "No DevBoard found"}))
        else:
            console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    tasks = board.load_tasks()

    # Apply filters
    if status:
        statuses = [s.strip() for s in status.split(",")]
        tasks = [t for t in tasks if t.status in statuses]
    if priority:
        priorities = [p.strip() for p in priority.split(",")]
        tasks = [t for t in tasks if t.priority in priorities]
    if agent:
        tasks = [t for t in tasks if agent.lower() in t.agent.lower()]
    if project:
        tasks = [t for t in tasks if project.lower() in t.project.lower()]
    if tag:
        tasks = [t for t in tasks if tag in t.tags]
    if blocked:
        tasks = [t for t in tasks if t.status == "blocked"]

    # Sort
    sort_key = {
        "id": lambda t: t.task_id,
        "status": lambda t: t.status,
        "priority": lambda t: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(t.priority, 99),
        "created": lambda t: t.created,
    }.get(sort, lambda t: t.task_id)
    tasks.sort(key=sort_key, reverse=reverse)

    if limit > 0:
        tasks = tasks[:limit]

    if as_json:
        console.print(_json.dumps({
            "tasks": [
                {
                    "id": t.task_id,
                    "title": t.name,
                    "status": t.status,
                    "priority": t.priority,
                    "agent": t.agent,
                    "project": t.project,
                    "claimed_by": t.claimed_by,
                    "dependencies": t.dependencies,
                    "tags": t.tags,
                    "cos": t.cos,
                }
                for t in tasks
            ],
            "count": len(tasks),
        }, indent=2))
        return

    if not tasks:
        console.print("[dim]No tasks match the filters.[/dim]")
        return

    if compact:
        for task in tasks:
            status_label = {"backlog": "[ ]", "in-progress": "[~]", "review": "[r]", "done": "[x]", "blocked": "[!]"}.get(task.status, "[ ]")
            console.print(f"{status_label} {task.task_id} {task.name} ({task.priority}) {task.agent}")
        return

    table = Table(box=box.ROUNDED, show_lines=False)
    table.add_column("ID", width=8)
    table.add_column("Title", min_width=20)
    table.add_column("Status", width=12)
    table.add_column("Priority", width=10)
    table.add_column("Agent", width=12)

    for task in tasks:
        table.add_row(task.task_id, task.name, task.status, task.priority, task.agent)

    console.print(table)


# ─── Show ──────────────────────────────────────────────────────────────────

@main.command()
@click.argument("task_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def show(task_id: str, as_json: bool):
    """Show full details of a task."""
    board = get_board()
    if not board.exists():
        if as_json:
            console.print(_json.dumps({"error": "No DevBoard found"}))
        else:
            console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    task = board.find_task(task_id)
    if not task:
        if as_json:
            console.print(_json.dumps({"error": f"Task {task_id} not found"}))
        else:
            console.print(f"[red]Task {task_id} not found[/red]")
        sys.exit(1)

    if as_json:
        console.print(_json.dumps({
            "task_id": task.task_id,
            "title": task.name,
            "status": task.status,
            "priority": task.priority,
            "agent": task.agent,
            "project": task.project,
            "claimed_by": task.claimed_by,
            "claimed_at": task.claimed_at,
            "dependencies": task.dependencies,
            "tags": task.tags,
            "cos": task.cos,
            "due": task.due,
            "body": task.body,
            "created": task.created,
            "updated": task.updated,
            "started": task.started,
            "completed": task.completed,
        }, indent=2, default=str))
        return

    status_label = {
        "backlog": "[ ] Backlog",
        "in-progress": "[~] In Progress",
        "review": "[r] Review",
        "done": "[x] Done",
        "blocked": "[!] Blocked",
    }.get(task.status, task.status)

    content = (
        f"[bold]{task.name}[/bold]\n\n"
        f"ID: {task.task_id}\n"
        f"Status: {status_label}\n"
        f"Priority: {task.priority}\n"
        f"Agent: {task.agent}\n"
    )
    if task.project:
        content += f"Project: {task.project}\n"
    if task.claimed_by:
        content += f"Claimed by: {task.claimed_by}\n"
    if task.dependencies:
        content += f"Dependencies: {', '.join(task.dependencies)}\n"
    if task.tags:
        content += f"Tags: {', '.join(task.tags)}\n"
    if task.cos and task.cos != "standard":
        content += f"Class of Service: {task.cos}\n"
    if task.due:
        content += f"Due: {task.due}\n"
    if task.body:
        content += f"\n[bold]Description:[/bold]\n{task.body}\n"

    console.print(Panel(content, title=f"Task {task_id}", border_style="blue"))


# ─── Pick ──────────────────────────────────────────────────────────────────

@main.command()
@click.option("--claim", required=True, help="Agent name (required)")
@click.option("--status", default="backlog", help="Source status to pick from")
@click.option("--tags", default="", help="Filter by tags (comma-separated)")
@click.option("--no-body", is_flag=True, help="Suppress task details after pick")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def pick(claim: str, status: str, tags: str, no_body: bool, as_json: bool):
    """Atomically pick and claim the next available task."""
    board = get_board()
    if not board.exists():
        if as_json:
            console.print(_json.dumps({"error": "No DevBoard found"}))
        else:
            console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    task = board.pick_task(agent=claim, status=status, tags=tag_list)

    if task:
        if as_json:
            console.print(_json.dumps({
                "success": True,
                "task_id": task.task_id,
                "title": task.name,
                "priority": task.priority,
                "agent": claim,
            }, indent=2))
        else:
            console.print(f"[yellow]✓ Picked task {task.task_id}: {task.name} (claimed by {claim})[/yellow]")
            if not no_body:
                console.print(f"  Priority: {task.priority} | Status: {task.status}")
                if task.body:
                    console.print(f"  {task.body[:200]}")
    else:
        if as_json:
            console.print(_json.dumps({"success": False, "error": "No unblocked, unclaimed tasks found"}))
        else:
            console.print("[dim]No unblocked, unclaimed tasks found[/dim]")
        sys.exit(1)


# ─── Claim ─────────────────────────────────────────────────────────────────

@main.command()
@click.argument("task_id")
@click.option("--claim", "agent", required=True, help="Agent name (required)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def claim(task_id: str, agent: str, as_json: bool):
    """Claim a task for an agent."""
    board = get_board()
    if not board.exists():
        if as_json:
            console.print(_json.dumps({"error": "No DevBoard found"}))
        else:
            console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    result = board.claim_task(task_id, agent)
    if result:
        if as_json:
            console.print(_json.dumps({"success": True, "task_id": task_id, "agent": agent}))
        else:
            console.print(f"[yellow]✓ Task {task_id} claimed by {agent}[/yellow]")
    else:
        if as_json:
            console.print(_json.dumps({"success": False, "error": f"Task {task_id} not available"}))
        else:
            console.print(f"[red]✗ Task {task_id} not available (already claimed or blocked)[/red]")
        sys.exit(1)


# ─── Complete ──────────────────────────────────────────────────────────────

@main.command()
@click.argument("task_id")
@click.option("--claim", "agent", required=True, help="Your agent name (must be the claimant)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def complete(task_id: str, agent: str, as_json: bool):
    """Mark a task as completed. Only the claiming agent can complete."""
    board = get_board()
    if not board.exists():
        if as_json:
            console.print(_json.dumps({"error": "No DevBoard found"}))
        else:
            console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    result = board.complete_task(task_id, agent)
    if result:
        if as_json:
            console.print(_json.dumps({"success": True, "task_id": task_id}))
        else:
            console.print(f"[green]✓ Task {task_id} completed[/green]")
    else:
        if as_json:
            console.print(_json.dumps({"success": False, "error": f"Task {task_id} not found or not claimed by {agent}"}))
        else:
            console.print(f"[red]✗ Task {task_id} not found or not claimed by {agent}[/red]")
        sys.exit(1)


# ─── Move ──────────────────────────────────────────────────────────────────

@main.command()
@click.argument("task_id")
@click.argument("new_status")
@click.option("--claim", "agent", default="", help="Agent name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def move(task_id: str, new_status: str, agent: str, as_json: bool):
    """Move a task to a new status."""
    board = get_board()
    if not board.exists():
        if as_json:
            console.print(_json.dumps({"error": "No DevBoard found"}))
        else:
            console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    if board.move_task(task_id, new_status, agent):
        if as_json:
            console.print(_json.dumps({"success": True, "task_id": task_id, "new_status": new_status}))
        else:
            console.print(f"[green]✓ Task {task_id} moved to {new_status}[/green]")
    else:
        if as_json:
            console.print(_json.dumps({"success": False, "error": f"Task {task_id} not found or invalid status"}))
        else:
            console.print(f"[red]✗ Task {task_id} not found or invalid status '{new_status}'[/red]")
        sys.exit(1)


# ─── Edit ──────────────────────────────────────────────────────────────────

@main.command()
@click.argument("task_id")
@click.option("--title", default=None, help="New title")
@click.option("--priority", default=None, type=click.Choice(["low", "medium", "high", "critical"]))
@click.option("--agent", default=None, help="New agent assignment")
@click.option("--project", default=None, help="New project")
@click.option("--tags", default=None, help="Comma-separated tags (replaces existing)")
@click.option("--add-tag", "add_tag", default=None, help="Add a single tag")
@click.option("--remove-tag", "remove_tag", default=None, help="Remove a single tag")
@click.option("--cos", "cos", default=None, type=click.Choice(["expedite", "fixed-date", "standard", "intangible"]))
@click.option("--due", default=None, help="Due date (ISO 8601)")
@click.option("--body", default=None, help="Task description/body")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def edit(task_id: str, title: str | None, priority: str | None, agent: str | None,
         project: str | None, tags: str | None, add_tag: str | None, remove_tag: str | None,
         cos: str | None, due: str | None, body: str | None, as_json: bool):
    """Edit a task's fields. Only provided fields are updated."""
    board = get_board()
    if not board.exists():
        if as_json:
            console.print(_json.dumps({"error": "No DevBoard found"}))
        else:
            console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    task = board.find_task(task_id)
    if not task:
        if as_json:
            console.print(_json.dumps({"error": f"Task {task_id} not found"}))
        else:
            console.print(f"[red]Task {task_id} not found[/red]")
        sys.exit(1)

    # Apply changes
    if title is not None:
        task.name = title
    if priority is not None:
        task.priority = priority
    if agent is not None:
        task.agent = agent
    if project is not None:
        task.project = project
    if tags is not None:
        task.tags = [t.strip() for t in tags.split(",") if t.strip()]
    if add_tag is not None:
        if add_tag not in task.tags:
            task.tags.append(add_tag)
    if remove_tag is not None:
        task.tags = [t for t in task.tags if t != remove_tag]
    if cos is not None:
        task.cos = cos
    if due is not None:
        task.due = due
    if body is not None:
        task.body = body

    task.updated = __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat()
    board.save_task(task)
    board._log_activity("edit", task_id, agent or "", "fields updated")
    board._update_master()

    if as_json:
        console.print(_json.dumps({"success": True, "task_id": task_id}, indent=2))
    else:
        console.print(f"[green]✓ Task {task_id} updated[/green]")


# ─── Log ───────────────────────────────────────────────────────────────────

@main.command()
@click.option("--limit", "-n", default=20, help="Max entries to show")
@click.option("--action", default="", help="Filter by action type")
@click.option("--task", "task_id", default="", help="Filter by task_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def log(limit: int, action: str, task_id: str, as_json: bool):
    """Show the activity log."""
    board = get_board()
    if not board.exists():
        if as_json:
            console.print(_json.dumps({"error": "No DevBoard found"}))
        else:
            console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    entries = board.get_activity(limit=limit, action=action, task_id=task_id)

    if as_json:
        console.print(_json.dumps({"entries": entries, "count": len(entries)}, indent=2, default=str))
        return

    if not entries:
        console.print("[dim]No activity yet.[/dim]")
        return

    for entry in entries:
        ts = entry.get("timestamp", "")[:19]
        act = entry.get("action", "")
        tid = entry.get("task_id", "")
        agent = entry.get("agent", "")
        detail = entry.get("detail", "")
        console.print(f"[dim]{ts}[/dim] [bold]{act:10}[/bold] {tid:8} {agent:12} {detail}")


# ─── Agent Name ────────────────────────────────────────────────────────────

@main.command("agent-name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def agent_name(as_json: bool):
    """Generate a random agent name for claim operations."""
    board = get_board()
    name = board.generate_agent_name()
    if as_json:
        console.print(_json.dumps({"name": name}))
    else:
        console.print(name)


# ─── Board (summary) ───────────────────────────────────────────────────────

@main.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def board_summary(as_json: bool):
    """Show a board summary with per-status counts and WIP utilization."""
    board = get_board()
    if not board.exists():
        if as_json:
            console.print(_json.dumps({"error": "No DevBoard found"}))
        else:
            console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    stats = board.get_stats()

    if as_json:
        config = board.load_config()
        wip_limits = config.get("wip_limits", {})
        console.print(_json.dumps({
            "total": stats.total,
            "backlog": stats.backlog,
            "in_progress": stats.in_progress,
            "review": stats.review,
            "done": stats.done,
            "blocked": stats.blocked,
            "wip_limits": wip_limits,
            "by_project": stats.by_project,
            "by_priority": stats.by_priority,
            "by_agent": stats.by_agent,
            "by_cos": stats.by_cos,
        }, indent=2))
        return

    table = Table(box=box.ROUNDED)
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("WIP Limit", justify="right")

    config = board.load_config()
    wip_limits = config.get("wip_limits", {})

    for status_name, count in [
        ("backlog", stats.backlog),
        ("in-progress", stats.in_progress),
        ("review", stats.review),
        ("done", stats.done),
        ("blocked", stats.blocked),
    ]:
        limit = wip_limits.get(status_name, 0)
        limit_str = str(limit) if limit > 0 else "∞"
        style = "yellow" if limit > 0 and count >= limit else "default"
        table.add_row(status_name, str(count), limit_str, style=style)

    console.print(Panel(table, title="Board Summary", border_style="blue"))


# ─── Flow ──────────────────────────────────────────────────────────────────

@main.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def flow(as_json: bool):
    """Show flow metrics (throughput, lead time, cycle time, SLA compliance)."""
    board = get_board()
    if not board.exists():
        if as_json:
            console.print(_json.dumps({"error": "No DevBoard found"}))
        else:
            console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    metrics = board.get_flow_metrics()

    if as_json:
        console.print(_json.dumps({
            "throughput_7d": metrics.throughput_7d,
            "throughput_30d": metrics.throughput_30d,
            "avg_lead_time_hours": metrics.avg_lead_time_hours,
            "avg_cycle_time_hours": metrics.avg_cycle_time_hours,
            "median_lead_time_hours": metrics.median_lead_time_hours,
            "median_cycle_time_hours": metrics.median_cycle_time_hours,
            "current_wip": metrics.current_wip,
            "littles_law_wip": metrics.littles_law_wip,
            "sla_breaches": metrics.sla_breaches,
            "sla_compliance_pct": metrics.sla_compliance_pct,
        }, indent=2))
        return

    table = Table(box=box.ROUNDED)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Throughput (7d)", f"{metrics.throughput_7d} tasks/day")
    table.add_row("Throughput (30d)", f"{metrics.throughput_30d} tasks/day")
    table.add_row("Avg Lead Time", f"{metrics.avg_lead_time_hours}h")
    table.add_row("Avg Cycle Time", f"{metrics.avg_cycle_time_hours}h")
    table.add_row("Median Lead Time", f"{metrics.median_lead_time_hours}h")
    table.add_row("Median Cycle Time", f"{metrics.median_cycle_time_hours}h")
    table.add_row("Current WIP", str(metrics.current_wip))
    table.add_row("Little's Law WIP", str(metrics.littles_law_wip))
    table.add_row("SLA Breaches", str(metrics.sla_breaches))
    table.add_row("SLA Compliance", f"{metrics.sla_compliance_pct}%")

    console.print(Panel(table, title="Flow Metrics", border_style="blue"))


# ─── Validate ──────────────────────────────────────────────────────────────

@main.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def validate(as_json: bool):
    """Validate the board configuration and check for issues."""
    board = get_board()
    if not board.exists():
        if as_json:
            console.print(_json.dumps({"error": "No DevBoard found"}))
        else:
            console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    issues = board.validate_config()
    cycles = board.check_dependency_cycles()

    if cycles:
        issues.append(f"Dependency cycles detected in tasks: {', '.join(cycles)}")

    if as_json:
        console.print(_json.dumps({
            "valid": len(issues) == 0,
            "issues": issues,
            "cycles": cycles,
        }, indent=2))
        return

    if not issues:
        console.print("[green]✓ Board is valid — no issues found[/green]")
    else:
        console.print("[yellow]⚠ Board validation found issues:[/yellow]")
        for issue in issues:
            console.print(f"  • {issue}")


if __name__ == "__main__":
    main()

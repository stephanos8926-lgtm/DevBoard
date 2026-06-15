"""DevBoard CLI — command-line interface for the multi-agent task board.

Reference: kanban-md cmd/ directory structure
Commands: init, add, list, show, pick, claim, complete, move, edit, log, board, agent-name
"""

from __future__ import annotations

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
def init(path: str, name: str):
    """Initialize a new DevBoard directory."""
    board = DevBoard(path)
    if board.exists():
        console.print(f"[yellow]DevBoard already exists at {board.root}[/yellow]")
        return
    board.init(name=name)
    console.print(f"[green]✓ DevBoard initialized at {board.root}[/green]")
    console.print(f"  Run [bold]devboard status[/bold] to see the board")


# ─── Status ────────────────────────────────────────────────────────────────

@main.command("status")
@click.option("--compact", is_flag=True, help="Compact output (token-efficient)")
def cmd_status(compact: bool):
    """Show the current board status."""
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found. Run 'devboard init' first.[/red]")
        sys.exit(1)

    stats = board.get_stats()

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
def add(title: str, priority: str, project: str, description: str, agent: str, tags: str):
    """Add a new task to the board."""
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found. Run 'devboard init' first.[/red]")
        sys.exit(1)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    task = board.add_task(
        name=title,
        priority=priority,
        description=description,
        project=project,
        agent=agent,
        tags=tag_list,
    )
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
def list_tasks(status: str, priority: str, agent: str, project: str, tag: str,
               blocked: bool, sort: str, reverse: bool, limit: int, compact: bool):
    """List tasks with filtering and sorting."""
    board = get_board()
    if not board.exists():
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
def show(task_id: str):
    """Show full details of a task."""
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    task = board.find_task(task_id)
    if not task:
        console.print(f"[red]Task {task_id} not found[/red]")
        sys.exit(1)

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
    if task.body:
        content += f"\n[bold]Description:[/bold]\n{task.body}\n"

    console.print(Panel(content, title=f"Task {task_id}", border_style="blue"))


# ─── Pick ──────────────────────────────────────────────────────────────────

@main.command()
@click.option("--claim", required=True, help="Agent name (required)")
@click.option("--status", default="backlog", help="Source status to pick from")
@click.option("--tags", default="", help="Filter by tags (comma-separated)")
@click.option("--no-body", is_flag=True, help="Suppress task details after pick")
def pick(claim: str, status: str, tags: str, no_body: bool):
    """Atomically pick and claim the next available task.

    Reference: kanban-md cmd/pick.go
    """
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    task = board.pick_task(agent=claim, status=status, tags=tag_list)

    if task:
        console.print(f"[yellow]✓ Picked task {task.task_id}: {task.name} (claimed by {claim})[/yellow]")
        if not no_body:
            console.print(f"  Priority: {task.priority} | Status: {task.status}")
            if task.body:
                console.print(f"  {task.body[:200]}")
    else:
        console.print("[dim]No unblocked, unclaimed tasks found[/dim]")
        sys.exit(1)


# ─── Claim ─────────────────────────────────────────────────────────────────

@main.command()
@click.argument("task_id")
@click.option("--claim", "agent", required=True, help="Agent name (required)")
def claim(task_id: str, agent: str):
    """Claim a task for an agent."""
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    result = board.claim_task(task_id, agent)
    if result:
        console.print(f"[yellow]✓ Task {task_id} claimed by {agent}[/yellow]")
    else:
        console.print(f"[red]✗ Task {task_id} not already claimed or not found[/red]")
        sys.exit(1)


# ─── Complete ──────────────────────────────────────────────────────────────

@main.command()
@click.argument("task_id")
@click.option("--claim", "agent", required=True, help="Your agent name (must be the claimant)")
def complete(task_id: str, agent: str):
    """Mark a task as completed. Only the claiming agent can complete."""
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    result = board.complete_task(task_id, agent)
    if result:
        console.print(f"[green]✓ Task {task_id} completed[/green]")
    else:
        console.print(f"[red]✗ Task {task_id} not found or not claimed by {agent}[/red]")
        sys.exit(1)


# ─── Move ──────────────────────────────────────────────────────────────────

@main.command()
@click.argument("task_id")
@click.argument("new_status")
@click.option("--claim", "agent", default="", help="Agent name")
def move(task_id: str, new_status: str, agent: str):
    """Move a task to a new status."""
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    if board.move_task(task_id, new_status, agent):
        console.print(f"[green]✓ Task {task_id} moved to {new_status}[/green]")
    else:
        console.print(f"[red]✗ Task {task_id} not found[/red]")
        sys.exit(1)


# ─── Log ───────────────────────────────────────────────────────────────────

@main.command()
@click.option("--limit", "-n", default=20, help="Max entries to show")
@click.option("--action", default="", help="Filter by action type")
@click.option("--task", "task_id", default="", help="Filter by task_id")
def log(limit: int, action: str, task_id: str):
    """Show the activity log."""
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    entries = board.get_activity(limit=limit, action=action, task_id=task_id)
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
def agent_name():
    """Generate a random agent name for claim operations.

    Reference: kanban-md cmd/agent_name.go
    """
    board = get_board()
    name = board.generate_agent_name()
    console.print(name)


# ─── Board (summary) ───────────────────────────────────────────────────────

@main.command()
def board_summary():
    """Show a board summary with per-status counts and WIP utilization."""
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    stats = board.get_stats()

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


if __name__ == "__main__":
    main()

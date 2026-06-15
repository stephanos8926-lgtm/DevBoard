"""DevBoard CLI — command-line interface for the multi-agent task board."""

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
    # Fall back to creating in current directory
    return DevBoard(cwd)


@click.group()
@click.version_option(version=__version__)
def main():
    """DevBoard — Multi-agent shared task board."""
    pass


@main.command()
@click.argument("path", default=".", required=False)
def init(path: str):
    """Initialize a new DevBoard directory."""
    board = DevBoard(path)
    if board.exists():
        console.print(f"[yellow]DevBoard already exists at {board.root}[/yellow]")
        return
    board.init()
    console.print(f"[green]✓ DevBoard initialized at {board.root}[/green]")
    console.print(f"  Edit [bold]__TASKS.md[/bold] to add tasks")
    console.print(f"  Run [bold]devboard status[/bold] to see the board")


@main.command()
def status():
    """Show the current board status."""
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found. Run 'devboard init' first.[/red]")
        sys.exit(1)

    stats = board.get_stats()

    # Summary panel
    summary = (
        f"Total: [bold]{stats.total}[/bold] | "
        f"[dim]Not started: {stats.not_started}[/dim] | "
        f"[yellow]In progress: {stats.in_progress}[/yellow] | "
        f"[green]Done: {stats.done}[/green] | "
        f"[red]Blocked: {stats.blocked}[/red]"
    )
    console.print(Panel(summary, title="DevBoard Status", border_style="blue"))

    # Tasks table
    tasks = board.load_tasks()
    if not tasks:
        console.print("\n[dim]No tasks yet. Use 'devboard add' to create one.[/dim]")
        return

    table = Table(box=box.ROUNDED, show_lines=False)
    table.add_column("Status", style="bold", width=8)
    table.add_column("ID", width=12)
    table.add_column("Name", min_width=20)
    table.add_column("Phase", min_width=15)
    table.add_column("Agent", min_width=12)
    table.add_column("Project", min_width=12)

    for task in sorted(tasks, key=lambda t: (t.status, t.task_id)):
        status_style = {
            " ": "dim",
            "~": "yellow",
            "x": "green",
            "!": "red",
        }.get(task.status, "white")

        table.add_row(
            f"[{status_style}][{task.status}][/{status_style}]",
            task.task_id,
            task.name,
            task.phase,
            task.agent,
            task.project,
        )

    console.print(table)


@main.command()
@click.option("--id", "task_id", required=True, help="Task ID (e.g., NA-0042)")
@click.option("--name", required=True, help="Task name")
@click.option("--phase", default="General", help="Phase or milestone")
@click.option("--priority", default="MEDIUM", type=click.Choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"]))
@click.option("--description", default="", help="Task description")
@click.option("--project", default="", help="Project name")
@click.option("--agent", default="Unassigned", help="Assigned agent")
@click.option("--depends", multiple=True, help="Dependency task IDs")
def add(task_id: str, name: str, phase: str, priority: str, description: str, project: str, agent: str, depends: tuple):
    """Add a new task to the board."""
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found. Run 'devboard init' first.[/red]")
        sys.exit(1)

    task = Task(
        task_id=task_id,
        name=name,
        phase=phase,
        priority=priority,
        description=description,
        agent=agent,
        dependencies=list(depends),
        project=project,
    )

    path = board.add_task(task)
    console.print(f"[green]✓ Task {task_id} added[/green] → {path}")


@main.command()
@click.argument("task_id")
@click.option("--agent", default="Unassigned", help="Agent name")
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
        console.print(f"[red]✗ Task {task_id} not available (already claimed or not found)[/red]")
        sys.exit(1)


@main.command()
@click.argument("task_id")
def complete(task_id: str):
    """Mark a task as completed."""
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    result = board.complete_task(task_id)
    if result:
        console.print(f"[green]✓ Task {task_id} completed[/green]")
    else:
        console.print(f"[red]✗ Task {task_id} not found[/red]")
        sys.exit(1)


@main.command()
@click.argument("task_id")
def show(task_id: str):
    """Show details of a specific task."""
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    tasks = board.load_tasks()
    for task in tasks:
        if task.task_id == task_id:
            console.print(Panel(
                f"[bold]{task.name}[/bold]\n\n"
                f"ID: {task.task_id}\n"
                f"Phase: {task.phase}\n"
                f"Priority: {task.priority}\n"
                f"Agent: {task.agent}\n"
                f"Status: [{task.status}]\n"
                f"Project: {task.project}\n\n"
                f"[bold]Description:[/bold]\n{task.description}\n\n"
                f"[bold]Dependencies:[/bold]\n" + ("\n".join(f"  - {d}" for d in task.dependencies) or "  (none)") + "\n\n"
                f"[bold]Acceptance Criteria:[/bold]\n" + ("\n".join(f"  - [ ] {c}" for c in task.acceptance_criteria) or "  (none)") + "\n\n"
                f"[bold]Notes:[/bold]\n{task.notes or '(none)'}",
                title=f"Task {task_id}",
                border_style="blue",
            ))
            return

    console.print(f"[red]Task {task_id} not found[/red]")
    sys.exit(1)


@main.command()
def agents():
    """Show tasks grouped by agent."""
    board = get_board()
    if not board.exists():
        console.print("[red]No DevBoard found.[/red]")
        sys.exit(1)

    tasks = board.load_tasks()
    by_agent: dict[str, list[Task]] = {}
    for task in tasks:
        by_agent.setdefault(task.agent, []).append(task)

    for agent, agent_tasks in sorted(by_agent.items()):
        console.print(f"\n[bold cyan]{agent}[/bold cyan]")
        for task in sorted(agent_tasks, key=lambda t: t.task_id):
            status_style = {" ": "dim", "~": "yellow", "x": "green", "!": "red"}.get(task.status, "white")
            console.print(f"  [{status_style}][{task.status}][/{status_style}] {task.task_id} — {task.name}")


if __name__ == "__main__":
    main()

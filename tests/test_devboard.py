"""Tests for DevBoard."""

from __future__ import annotations

import pytest
from pathlib import Path

from devboard import DevBoard, Task


@pytest.fixture
def tmp_board(tmp_path):
    """Create a temporary DevBoard."""
    board = DevBoard(tmp_path / "test_board")
    board.init()
    return board


class TestTask:
    def test_create_task(self):
        task = Task(task_id="NA-0001", name="Test Task", phase="Refactoring")
        assert task.task_id == "NA-0001"
        assert task.name == "Test Task"
        assert task.status == " "
        assert task.is_available

    def test_task_to_file(self):
        task = Task(
            task_id="NA-0001",
            name="Test Task",
            phase="Refactoring",
            description="Do the thing",
            agent="Lucien",
            project="NexusAgent",
        )
        content = task.to_file_content()
        assert "NA-0001" in content
        assert "Test Task" in content
        assert "Refactoring" in content
        assert "Lucien" in content

    def test_task_from_file(self, tmp_path):
        task = Task(
            task_id="NA-0001",
            name="Test Task",
            phase="Refactoring",
            description="Do the thing",
            agent="Lucien",
            project="NexusAgent",
        )
        task_file = tmp_path / "task"
        task_file.write_text(task.to_file_content())
        parsed = Task.from_file(task_file)
        assert parsed.task_id == "NA-0001"
        assert parsed.name == "Test Task"
        assert parsed.agent == "Lucien"


class TestDevBoard:
    def test_init(self, tmp_board):
        assert tmp_board.exists()
        assert tmp_board.tasks_file.exists()
        assert tmp_board.master_file.exists()

    def test_add_task(self, tmp_board):
        task = Task(task_id="NA-0001", name="Test Task", phase="Refactoring", project="NexusAgent")
        path = tmp_board.add_task(task)
        assert path.exists()

    def test_claim_task(self, tmp_board):
        task = Task(task_id="NA-0001", name="Test Task", phase="Refactoring")
        tmp_board.add_task(task)

        result = tmp_board.claim_task("NA-0001", "Lucien")
        assert result is not None

        # Can't claim again
        result2 = tmp_board.claim_task("NA-0001", "OtherAgent")
        assert result2 is None

    def test_complete_task(self, tmp_board):
        task = Task(task_id="NA-0001", name="Test Task", phase="Refactoring")
        tmp_board.add_task(task)
        tmp_board.claim_task("NA-0001", "Lucien")

        result = tmp_board.complete_task("NA-0001")
        assert result is not None
        assert result.parent.name == "JobEnd"

    def test_stats(self, tmp_board):
        for i in range(3):
            task = Task(task_id=f"NA-{i:04d}", name=f"Task {i}", phase="Refactoring")
            tmp_board.add_task(task)

        stats = tmp_board.get_stats()
        assert stats.total == 3
        assert stats.not_started == 3
        assert stats.done == 0

"""Tests for DevBoard v1.1.0 — YAML frontmatter + atomic claims."""

from __future__ import annotations

import pytest
from pathlib import Path

from devboard import DevBoard, Task


@pytest.fixture
def tmp_board(tmp_path):
    """Create a temporary DevBoard."""
    board = DevBoard(tmp_path / "test_board")
    board.init("Test Board")
    return board


class TestTask:
    def test_create_task(self):
        task = Task(task_id="1", name="Test Task", project="NexusAgent")
        assert task.task_id == "1"
        assert task.name == "Test Task"
        assert task.status == "backlog"
        assert task.is_available
        assert not task.is_claimed

    def test_task_to_file(self):
        task = Task(
            task_id="1",
            name="Test Task",
            priority="high",
            agent="Lucien",
            project="NexusAgent",
            body="Do the thing",
        )
        content = task.to_file_content()
        assert "id: '1'" in content or "id: 1" in content or content.startswith("---\nid:")
        assert "title: Test Task" in content
        assert "priority: high" in content
        assert "project: NexusAgent" in content
        assert "Do the thing" in content

    def test_task_from_file(self, tmp_path):
        task = Task(
            task_id="1",
            name="Test Task",
            priority="high",
            agent="Lucien",
            project="NexusAgent",
            body="Do the thing",
        )
        task_file = tmp_path / "task.md"
        task_file.write_text(task.to_file_content())
        parsed = Task.from_file(task_file)
        assert parsed.task_id == "1"
        assert parsed.name == "Test Task"
        assert parsed.agent == "Lucien"
        assert parsed.project == "NexusAgent"

    def test_claim_expiration(self):
        from datetime import UTC, timedelta
        task = Task(task_id="1", name="Old Task")
        # No claim = not expired
        assert not task.claim_expired

        # Claim from 2 hours ago = expired (default 1h timeout)
        old_time = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        task.claimed_by = "agent-1"
        task.claimed_at = old_time
        assert task.claim_expired
        assert task.is_effectively_available  # Expired = available

    def test_task_serialization_roundtrip(self, tmp_path):
        """Test YAML frontmatter roundtrip."""
        task = Task(
            task_id="42",
            name="Complex Task",
            status="in-progress",
            priority="critical",
            agent="Lucien",
            claimed_by="Lucien",
            claimed_at=datetime.now(UTC).isoformat(),
            dependencies=["1", "2"],
            project="NexusAgent",
            tags=["bug", "urgent"],
            body="This is the task body\nwith multiple lines",
        )
        task_file = tmp_path / "roundtrip.md"
        task_file.write_text(task.to_file_content())
        parsed = Task.from_file(task_file)
        assert parsed.task_id == "42"
        assert parsed.name == "Complex Task"
        assert parsed.status == "in-progress"
        assert parsed.priority == "critical"
        assert parsed.dependencies == ["1", "2"]
        assert parsed.tags == ["bug", "urgent"]
        assert "task body" in parsed.body


class TestDevBoard:
    def test_init(self, tmp_board):
        assert tmp_board.exists()
        assert tmp_board.config_file.exists()
        assert tmp_board.tasks_dir.exists()

    def test_add_task(self, tmp_board):
        task = tmp_board.add_task(name="Test Task", project="NexusAgent")
        assert task.task_id == "1"
        assert task.name == "Test Task"
        assert task.status == "backlog"

    def test_claim_task(self, tmp_board):
        tmp_board.add_task(name="Test Task")

        result = tmp_board.claim_task("1", "Lucien")
        assert result is not None

        # Can't claim again
        result2 = tmp_board.claim_task("1", "OtherAgent")
        assert result2 is None

    def test_complete_task(self, tmp_board):
        tmp_board.add_task(name="Test Task")
        tmp_board.claim_task("1", "Lucien")

        result = tmp_board.complete_task("1", "Lucien")
        assert result is not None

        task = tmp_board.find_task("1")
        assert task.status == "done"

    def test_complete_wrong_agent(self, tmp_board):
        """Only the claiming agent can complete."""
        tmp_board.add_task(name="Test Task")
        tmp_board.claim_task("1", "Lucien")

        result = tmp_board.complete_task("1", "OtherAgent")
        assert result is None

    def test_stats(self, tmp_board):
        for i in range(3):
            tmp_board.add_task(name=f"Task {i}")

        stats = tmp_board.get_stats()
        assert stats.total == 3
        assert stats.backlog == 3
        assert stats.done == 0

    def test_dependency_enforcement(self, tmp_board):
        """Can't claim a task with unmet dependencies."""
        tmp_board.add_task(name="Task A")
        tmp_board.add_task(name="Task B", dependencies=["1"])

        # Can't claim B because A is not done
        result = tmp_board.claim_task("2", "Lucien")
        assert result is None

        # Claim and complete A
        tmp_board.claim_task("1", "Lucien")
        tmp_board.complete_task("1", "Lucien")

        # Now B is claimable
        result = tmp_board.claim_task("2", "Lucien")
        assert result is not None

    def test_activity_log(self, tmp_board):
        tmp_board.add_task(name="Test Task")
        tmp_board.claim_task("1", "Lucien")

        log = tmp_board.get_activity()
        assert len(log) >= 2
        assert log[0]["action"] == "create"
        assert log[1]["action"] == "claim"

    def test_agent_name_generation(self, tmp_board):
        name = tmp_board.generate_agent_name()
        assert "-" in name
        assert len(name.split("-")) == 2

    def test_move_task(self, tmp_board):
        tmp_board.add_task(name="Test Task")
        assert tmp_board.move_task("1", "in-progress", "Lucien")

        task = tmp_board.find_task("1")
        assert task.status == "in-progress"
        assert task.started != ""

    def test_pick_task(self, tmp_board):
        tmp_board.add_task(name="Low priority", priority="low")
        tmp_board.add_task(name="High priority", priority="high")
        tmp_board.add_task(name="Critical", priority="critical")

        # Pick should get critical first
        task = tmp_board.pick_task(agent="Lucien")
        assert task is not None
        assert task.priority == "critical"

    def test_wip_limit(self, tmp_board):
        """WIP limit of 3 in-progress tasks per agent."""
        for i in range(5):
            tmp_board.add_task(name=f"Task {i}")

        # Claim 3 (the limit)
        for i in range(1, 4):
            result = tmp_board.claim_task(str(i), "Lucien")
            assert result is not None

        # 4th should fail (WIP limit)
        result = tmp_board.claim_task("4", "Lucien")
        assert result is None

        # But another agent can still claim
        result = tmp_board.claim_task("4", "OtherAgent")
        assert result is not None


from datetime import datetime, timedelta, UTC

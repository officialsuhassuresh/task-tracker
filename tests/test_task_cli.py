import json
import pytest
from click.testing import CliRunner
from pathlib import Path
from task_cli import cli, TASKS_FILE, load_tasks, save_tasks
from datetime import datetime
import time

@pytest.fixture(autouse=True)
def setup_test_file(tmp_path, monkeypatch):
    """Automatically used fixture that sets up a fresh tasks file for each test"""
    test_file = tmp_path / "tasks.json"
    monkeypatch.setattr('task_cli.TASKS_FILE', test_file)
    # Initialize with empty tasks list
    test_file.write_text('[]')
    return test_file

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def sample_task():
    return {
        "id": 1,
        "description": "Test task",
        "status": "todo",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }

class TestTaskCLI:
    def test_add_task(self, runner, setup_test_file):
        # Clear any existing tasks
        save_tasks([])
        
        result = runner.invoke(cli, ['add', 'Buy groceries'])
        assert result.exit_code == 0
        
        tasks = load_tasks()
        assert len(tasks) == 1
        assert tasks[0]['id'] == 1  # Should always be 1 for first task
        assert tasks[0]['description'] == 'Buy groceries'

    def test_update_task(self, runner, setup_test_file, sample_task):
        # Explicitly save the sample task first
        save_tasks([sample_task])
        
        result = runner.invoke(cli, ['update', '1', 'Updated task'])
        assert result.exit_code == 0
        
        tasks = load_tasks()
        assert len(tasks) == 1
        assert tasks[0]['description'] == 'Updated task'

    def test_list_all_tasks(self, runner, setup_test_file):
        # Initialize with known tasks
        tasks = [
            {
                "id": 1,
                "description": "Task 1",
                "status": "todo",
                "createdAt": datetime.now().isoformat(),
                "updatedAt": datetime.now().isoformat()
            },
            {
                "id": 2,
                "description": "Task 2",
                "status": "in-progress",
                "createdAt": datetime.now().isoformat(),
                "updatedAt": datetime.now().isoformat()
            }
        ]
        save_tasks(tasks)

        result = runner.invoke(cli, ['list'])
        assert result.exit_code == 0
        assert '[1] Task 1 (todo)' in result.output
        assert '[2] Task 2 (in-progress)' in result.output 

    def test_concurrent_task_ids(self, runner, setup_test_file):
        """Test that task IDs remain unique when adding multiple tasks"""
        # Add multiple tasks in succession
        results = [
            runner.invoke(cli, ['add', f'Task {i}'])
            for i in range(1, 4)
        ]
        
        tasks = load_tasks()
        ids = [task['id'] for task in tasks]
        assert len(ids) == len(set(ids)), "Task IDs must be unique"
        assert sorted(ids) == [1, 2, 3], "Task IDs should be sequential"

    def test_task_validation(self, runner, setup_test_file):
        """Test input validation"""
        # Test empty description
        result = runner.invoke(cli, ['add', ''])
        assert result.exit_code != 0
        assert "Error" in result.output

        # Test very long description
        long_description = "x" * 1000
        result = runner.invoke(cli, ['add', long_description])
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_status_transitions(self, runner, setup_test_file, sample_task):
        """Test all possible status transitions"""
        save_tasks([sample_task])
        
        # todo -> in-progress -> done
        result1 = runner.invoke(cli, ['mark-in-progress', '1'])
        assert result1.exit_code == 0
        tasks = load_tasks()
        assert tasks[0]['status'] == 'in-progress'
        
        result2 = runner.invoke(cli, ['mark-done', '1'])
        assert result2.exit_code == 0
        tasks = load_tasks()
        assert tasks[0]['status'] == 'done'

    def test_timestamp_updates(self, runner, setup_test_file, sample_task):
        """Test that timestamps are updated correctly"""
        save_tasks([sample_task])
        original_updated_at = sample_task['updatedAt']
        
        # Wait a small amount to ensure timestamp difference
        time.sleep(0.1)
        
        result = runner.invoke(cli, ['update', '1', 'Updated description'])
        tasks = load_tasks()
        assert tasks[0]['updatedAt'] != original_updated_at
        assert tasks[0]['createdAt'] == sample_task['createdAt']

    def test_bulk_operations(self, runner, setup_test_file):
        """Test handling of multiple tasks and operations"""
        # Add multiple tasks
        for i in range(5):
            runner.invoke(cli, ['add', f'Task {i}'])
        
        # Mark some as in-progress
        runner.invoke(cli, ['mark-in-progress', '1'])
        runner.invoke(cli, ['mark-in-progress', '3'])
        
        # Mark some as done
        runner.invoke(cli, ['mark-done', '2'])
        runner.invoke(cli, ['mark-done', '4'])
        
        # Verify different status filters
        todo_result = runner.invoke(cli, ['list', 'todo'])
        assert '[5] Task 4 (todo)' in todo_result.output
        
        in_progress_result = runner.invoke(cli, ['list', 'in-progress'])
        assert '[1]' in in_progress_result.output
        assert '[3]' in in_progress_result.output
        
        done_result = runner.invoke(cli, ['list', 'done'])
        assert '[2]' in done_result.output
        assert '[4]' in done_result.output

    def test_error_handling(self, runner, setup_test_file):
        """Test various error conditions"""
        # Test invalid task ID
        result = runner.invoke(cli, ['update', 'abc', 'Updated task'])
        assert result.exit_code != 0
        assert "Invalid value" in result.output
        
        # Test non-existent task
        result = runner.invoke(cli, ['mark-done', '999'])
        assert "Task 999 not found" in result.output
        
        # Test invalid status
        result = runner.invoke(cli, ['list', 'invalid-status'])
        assert result.exit_code != 0
        assert "Invalid value" in result.output

    def test_task_deletion_integrity(self, runner, setup_test_file):
        """Test that task deletion maintains data integrity"""
        # Add multiple tasks
        for i in range(3):
            runner.invoke(cli, ['add', f'Task {i}'])
        
        # Delete middle task
        runner.invoke(cli, ['delete', '2'])
        
        tasks = load_tasks()
        ids = [task['id'] for task in tasks]
        assert 2 not in ids, "Deleted task ID should not exist"
        assert len(tasks) == 2, "Should have exactly 2 tasks"
        
        # Add new task and verify ID assignment
        runner.invoke(cli, ['add', 'New task'])
        tasks = load_tasks()
        new_task = max(tasks, key=lambda x: x['id'])
        assert new_task['id'] == 4, "New task should get next available ID"

    def test_empty_list_messages(self, runner, setup_test_file):
        """Test messages for empty task lists"""
        # Test empty list with different status filters
        statuses = ['all', 'todo', 'in-progress', 'done']
        for status in statuses:
            result = runner.invoke(cli, ['list', status])
            assert result.exit_code == 0
            assert "No tasks found" in result.output

    def test_description_whitespace(self, runner, setup_test_file):
        """Test handling of whitespace in task descriptions"""
        # Test leading/trailing whitespace
        result = runner.invoke(cli, ['add', '  Task with spaces  '])
        assert result.exit_code == 0
        
        tasks = load_tasks()
        assert tasks[0]['description'] == 'Task with spaces'  # Should be trimmed
        
        # Test multiple spaces between words
        result = runner.invoke(cli, ['add', 'Task    with    spaces'])
        tasks = load_tasks()
        assert tasks[1]['description'] == 'Task with spaces'  # Should be normalized 

    def test_help_option(self, runner):
        """Test help output for all commands"""
        # Test main help
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Commands:' in result.output
        
        # Test help for each command
        commands = ['add', 'update', 'delete', 'list', 'mark-done', 'mark-in-progress']
        for cmd in commands:
            result = runner.invoke(cli, [cmd, '--help'])
            assert result.exit_code == 0
            assert 'Usage:' in result.output

    def test_invalid_commands(self, runner, setup_test_file):
        """Test handling of invalid commands and options"""
        # Test non-existent command
        result = runner.invoke(cli, ['nonexistent'])
        assert result.exit_code != 0
        assert 'No such command' in result.output
        
        # Test invalid option
        result = runner.invoke(cli, ['list', '--invalid-option'])
        assert result.exit_code != 0
        assert 'no such option' in result.output.lower()

    def test_multiple_status_updates(self, runner, setup_test_file, sample_task):
        """Test multiple status updates on the same task"""
        save_tasks([sample_task])
        
        # Test all possible status transitions
        transitions = [
            ('mark-in-progress', 'in-progress'),
            ('mark-done', 'done'),
            ('mark-in-progress', 'in-progress'),  # From done back to in-progress
            ('mark-done', 'done')
        ]
        
        for command, expected_status in transitions:
            result = runner.invoke(cli, [command, '1'])
            assert result.exit_code == 0
            tasks = load_tasks()
            assert tasks[0]['status'] == expected_status

    def test_list_formatting(self, runner, setup_test_file):
        """Test the formatting of list output"""
        # Add tasks with different statuses
        tasks = [
            {"id": 1, "description": "Task 1", "status": "todo", 
             "createdAt": datetime.now().isoformat(), "updatedAt": datetime.now().isoformat()},
            {"id": 2, "description": "Task 2", "status": "in-progress",
             "createdAt": datetime.now().isoformat(), "updatedAt": datetime.now().isoformat()},
            {"id": 3, "description": "Task 3", "status": "done",
             "createdAt": datetime.now().isoformat(), "updatedAt": datetime.now().isoformat()}
        ]
        save_tasks(tasks)
        
        result = runner.invoke(cli, ['list'])
        assert result.exit_code == 0
        
        # Check formatting
        lines = result.output.strip().split('\n')
        assert len(lines) == 3
        assert all(line.startswith('[') for line in lines)
        assert all(']' in line for line in lines)
        assert all('(' in line and ')' in line for line in lines)

    def test_task_id_conflicts(self, runner, setup_test_file):
        """Test handling of potential ID conflicts"""
        # Add task with specific ID
        tasks = [{"id": 999, "description": "High ID task", "status": "todo",
                  "createdAt": datetime.now().isoformat(), "updatedAt": datetime.now().isoformat()}]
        save_tasks(tasks)
        
        # Add new task and verify ID handling
        result = runner.invoke(cli, ['add', 'New task'])
        assert result.exit_code == 0
        
        tasks = load_tasks()
        assert len(tasks) == 2
        new_task = [t for t in tasks if t['description'] == 'New task'][0]
        assert new_task['id'] == 1000  # Should use next available ID

    def test_empty_file_handling(self, runner, setup_test_file):
        """Test handling of empty or corrupted tasks file"""
        # Test with empty file
        setup_test_file.write_text('')
        result = runner.invoke(cli, ['list'])
        assert result.exit_code == 0
        assert "No tasks found" in result.output
        
        # Test with invalid JSON
        setup_test_file.write_text('{invalid json}')
        result = runner.invoke(cli, ['list'])
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_description_special_characters(self, runner, setup_test_file):
        """Test handling of special characters in descriptions"""
        special_chars = [
            "Task with spaces and !@#$%^&*()",
            "Task with Unicode: 你好世界",
            "Task with newlines\nand\ttabs",
            "Task with 'single' and \"double\" quotes"
        ]
        
        for desc in special_chars:
            result = runner.invoke(cli, ['add', desc])
            assert result.exit_code == 0
            
            tasks = load_tasks()
            added_task = tasks[-1]
            assert added_task['description'] == desc.replace('\n', ' ').replace('\t', ' ')

    def test_concurrent_updates(self, runner, setup_test_file, sample_task):
        """Test handling of concurrent updates to the same task"""
        save_tasks([sample_task])
        
        # Simulate concurrent updates
        result1 = runner.invoke(cli, ['update', '1', 'Update 1'])
        result2 = runner.invoke(cli, ['mark-done', '1'])
        result3 = runner.invoke(cli, ['update', '1', 'Update 2'])
        
        assert all(r.exit_code == 0 for r in [result1, result2, result3])
        
        tasks = load_tasks()
        final_task = tasks[0]
        assert final_task['description'] == 'Update 2'
        assert final_task['status'] == 'done' 
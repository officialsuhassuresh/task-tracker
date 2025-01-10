import click
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Optional

TASKS_FILE = Path("tasks.json")

def load_tasks() -> List[Dict]:
    """Load tasks from file, handling empty or corrupted files"""
    try:
        if not TASKS_FILE.exists() or TASKS_FILE.stat().st_size == 0:
            # If file doesn't exist or is empty, return empty list
            return []
            
        with TASKS_FILE.open() as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                # Fail with error when JSON is corrupted
                raise click.ClickException(f"Error: Tasks file is corrupted. {str(e)}")
                
    except Exception as e:
        if isinstance(e, click.ClickException):
            raise
        raise click.ClickException(f"Error accessing tasks file: {str(e)}")

def save_tasks(tasks: List[Dict]) -> None:
    with TASKS_FILE.open('w') as f:
        json.dump(tasks, f, indent=2)

@click.group()
def cli():
    """Task Tracker CLI - Manage your tasks efficiently"""
    pass

@cli.command()
@click.argument('description')
def add(description: str):
    """Add a new task"""
    description = validate_description(description)
    new_task = add_task(description)
    click.echo(f"Task added successfully (ID: {new_task['id']})")

@cli.command()
@click.argument('task_id', type=int)
@click.argument('description')
def update(task_id: int, description: str):
    """Update a task's description"""
    tasks = load_tasks()
    
    for task in tasks:
        if task['id'] == task_id:
            task['description'] = description
            task['updatedAt'] = datetime.now().isoformat()
            save_tasks(tasks)
            click.echo(f"Task {task_id} updated successfully")
            return
            
    click.echo(f"Task {task_id} not found", err=True)

@cli.command()
@click.argument('task_id', type=int)
def delete(task_id: int):
    """Delete a task"""
    tasks = load_tasks()
    tasks = [task for task in tasks if task['id'] != task_id]
    save_tasks(tasks)
    click.echo(f"Task {task_id} deleted successfully")

@cli.command()
@click.argument('status', type=click.Choice(['all', 'done', 'todo', 'in-progress']), default='all')
def list(status: str):
    """List tasks, optionally filtered by status"""
    tasks = load_tasks()
    
    if status != 'all':
        tasks = [task for task in tasks if task['status'] == status]
    
    if not tasks:
        click.echo("No tasks found")
        return
        
    for task in tasks:
        click.echo(f"[{task['id']}] {task['description']} ({task['status']})")

@cli.command('mark-done')
@click.argument('task_id', type=int)
def mark_done(task_id: int):
    """Mark a task as done"""
    _update_task_status(task_id, 'done')

@cli.command('mark-in-progress')
@click.argument('task_id', type=int)
def mark_in_progress(task_id: int):
    """Mark a task as in progress"""
    _update_task_status(task_id, 'in-progress')

def _update_task_status(task_id: int, status: str) -> None:
    tasks = load_tasks()
    
    for task in tasks:
        if task['id'] == task_id:
            task['status'] = status
            task['updatedAt'] = datetime.now().isoformat()
            save_tasks(tasks)
            click.echo(f"Task {task_id} marked as {status}")
            return
            
    click.echo(f"Task {task_id} not found", err=True)

def add_task(description: str) -> Dict:
    tasks = load_tasks()
    # Get the next ID (should be max + 1, even after deletions)
    next_id = max([task['id'] for task in tasks], default=0) + 1
    
    new_task = {
        "id": next_id,
        "description": description,
        "status": "todo",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
    tasks.append(new_task)
    save_tasks(tasks)
    return new_task

def validate_description(description: str) -> str:
    """Validate and normalize task description"""
    normalized = ' '.join(description.split())  # Normalize internal whitespace
    if not normalized:
        raise click.BadParameter("Task description cannot be empty")
    if len(normalized) > 500:
        raise click.BadParameter("Task description is too long")
    return normalized

if __name__ == '__main__':
    cli() 
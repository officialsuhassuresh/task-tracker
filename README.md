# Task Tracker CLI

A simple command-line interface (CLI) application to track and manage your tasks. Built with Python and Click.

## Features

- Add, update, and delete tasks
- Mark tasks as in progress or done
- List all tasks
- Filter tasks by status (todo, in-progress, done)
- Persistent storage using JSON

## Installation

1. Clone the repository:
```bash
git clone https://github.com/officialsuhassuresh/task-tracker.git
```

2. Navigate to the project directory:
```bash
cd task-tracker
```

3. Create and activate a virtual environment:

On Windows:
```bash 
python -m venv venv
.\venv\Scripts\activate
```

On macOS and Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

4. Install the dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

5. Run the application:
```bash
task-cli
```

## Usage

To add a new task, use the `add` command:
```bash
task-cli add "Buy groceries"
```

To update a task, use the `update` command:
```bash
task-cli update 1 "Buy groceries"
```


To delete a task, use the `delete` command:
```bash
task-cli delete 1
```

To list all tasks, use the `list` command:
```bash
task-cli list
```


To filter tasks by status, use the `filter` command:
```bash
task-cli filter todo
```


To mark a task as done, use the `mark-done` command:
```bash
task-cli mark-done 1
```


To mark a task as in progress, use the `mark-in-progress` command:
```bash
task-cli mark-in-progress 1
```


To mark a task as todo, use the `mark-todo` command:
```bash
task-cli mark-todo 1
```


To mark a task as in progress, use the `mark-in-progress` command:
```bash
task-cli mark-in-progress 1
```

## Command Reference

| Command | Description |
| ------- | ----------- |
| `task-cli add "Buy groceries"` | Add a new task |
| `task-cli update 1 "Buy groceries"` | Update a task |
| `task-cli delete 1` | Delete a task |
| `task-cli list` | List all tasks |
| `task-cli filter todo` | Filter tasks by status |
| `task-cli mark-done 1` | Mark a task as done |
| `task-cli mark-in-progress 1` | Mark a task as in progress |
| `task-cli mark-todo 1` | Mark a task as todo |

## Data Storage

The tasks are stored in a JSON file named `tasks.json` in the project directory.

Each task has the following fields:
- `id`: The unique identifier for the task
- `description`: The description of the task
- `status`: The status of the task (todo, in-progress, done)
- `createdAt`: The date and time the task was created
- `updatedAt`: The date and time the task was last updated

## Development

To contribute to this project, please follow these steps:

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Commit your changes
5. Push your changes to your fork
6. Create a pull request

## License

This project is open-sourced under the MIT License - see the LICENSE file for details.

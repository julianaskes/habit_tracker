# Habit Tracker CLI

A simple command-line habit tracking application built with Python and SQLite3. Track your daily and weekly habits, maintain streaks, and view statistics about your progress.

## Features

- Create and manage daily or weekly habits
- Track habit completions with dates
- View current and longest streaks
- Calculate completion rates
- Persistent storage using SQLite3 database
- Simple command-line interface

## Requirements

- Python 3.6 or higher
- SQLite3 (usually comes pre-installed with Python)

## Installation

1. Clone or download this repository to your local machine
2. No additional Python packages are required as the application uses only built-in libraries

## Usage

The application provides several commands through its command-line interface:

### Adding a New Habit

```bash
python cli.py add "Exercise" --period daily
```

Options:
- `--period`: Can be either `daily` or `weekly` (default: `daily`)

### Marking a Habit as Complete

```bash
python cli.py complete "Exercise"
```

Options:
- `--date`: Specify a completion date in YYYY-MM-DD format (default: today)

Example with specific date:
```bash
python cli.py complete "Exercise" --date 2025-10-07
```

### Listing All Habits and Their Statistics

```bash
python cli.py list
```

This command shows for each habit:
- Current streak
- Longest streak
- Total completions
- 30-day completion rate

### Removing a Habit

```bash
python cli.py remove "Exercise"
```

## Data Storage

The application stores all habit data in a SQLite database file named `habits.db` in the same directory as the application. This file is created automatically when you add your first habit.

## Project Structure

- `cli.py`: Command-line interface and argument parsing
- `habit.py`: Core Habit class implementation
- `storage.py`: Database operations and persistence
- `analytics.py`: Statistics and analysis functions

## Example Session

```bash
# Add a new daily habit
python cli.py add "Morning Meditation" --period daily

# Add a weekly habit
python cli.py add "Weekly Review" --period weekly

# Mark habits as complete
python cli.py complete "Morning Meditation"
python cli.py complete "Weekly Review"

# View all habits and their progress
python cli.py list

# Remove a habit
python cli.py remove "Morning Meditation"
```
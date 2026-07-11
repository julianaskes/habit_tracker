import argparse
import sys
from datetime import datetime, date
from storage import Storage
from habit import Habit
from analytics import get_habit_stats, get_completion_rate


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def _error(message):
    print(f"Error: {message}", file=sys.stderr)


class HabitTrackerCLI:
    def __init__(self):
        self.storage = Storage()

    def add_habit(self, name, period="daily"):
        if not name or not name.strip():
            _error("Habit name cannot be empty")
            return False

        if period not in ["daily", "weekly"]:
            _error("Period must be 'daily' or 'weekly'")
            return False

        if self.storage.get_habit(name):
            _error(f"Habit '{name}' already exists")
            return False

        habit = Habit(name, period)
        self.storage.add_habit(habit)
        print(f"Habit '{name}' added successfully!")
        return True

    def complete_habit(self, name, date_str=None):
        habit = self.storage.get_habit(name)
        if not habit:
            _error(f"Habit '{name}' not found")
            return False

        completion_date = parse_date(date_str) if date_str else date.today()
        if not completion_date:
            _error("Invalid date format. Use YYYY-MM-DD")
            return False

        if completion_date > date.today():
            _error("Completion date cannot be in the future")
            return False

        habit.complete(completion_date)
        self.storage.add_habit(habit)
        print(f"Habit '{name}' marked as completed for {completion_date}")
        return True

    def uncomplete_habit(self, name, date_str=None):
        habit = self.storage.get_habit(name)
        if not habit:
            _error(f"Habit '{name}' not found")
            return False

        completion_date = parse_date(date_str) if date_str else date.today()
        if not completion_date:
            _error("Invalid date format. Use YYYY-MM-DD")
            return False

        if not habit.uncomplete(completion_date):
            _error(f"'{name}' has no completion recorded for {completion_date}")
            return False

        self.storage.add_habit(habit)
        print(f"Completion for '{name}' on {completion_date} removed")
        return True

    def remove_habit(self, name):
        if self.storage.remove_habit(name):
            print(f"Habit '{name}' removed successfully!")
            return True
        _error(f"Habit '{name}' not found")
        return False

    def show_habit(self, name):
        habit = self.storage.get_habit(name)
        if not habit:
            _error(f"Habit '{name}' not found")
            return False

        stats = get_habit_stats(habit)
        print(f"\nName: {stats['name']}")
        print(f"Period: {stats['period']}")
        print(f"Created: {habit.created_at.date()}")
        print(f"Current Streak: {stats['current_streak']}")
        print(f"Longest Streak: {stats['longest_streak']}")
        print(f"Total Completions: {stats['total_completions']}")
        print(f"30-day Completion Rate: {get_completion_rate(habit):.1f}%")
        if habit.completed_dates:
            print("Completion History:")
            for d in sorted(habit.completed_dates):
                print(f"  - {d.isoformat()}")
        else:
            print("No completions yet")
        return True

    def list_habits(self):
        habits = self.storage.get_all_habits()
        if not habits:
            print("No habits found")
            return True

        print("\nYour Habits:")
        print("-" * 50)
        for habit in habits:
            stats = get_habit_stats(habit)
            completion_rate = get_completion_rate(habit)
            print(f"Name: {stats['name']}")
            print(f"Period: {stats['period']}")
            print(f"Current Streak: {stats['current_streak']}")
            print(f"Longest Streak: {stats['longest_streak']}")
            print(f"Total Completions: {stats['total_completions']}")
            print(f"30-day Completion Rate: {completion_rate:.1f}%")
            print("-" * 50)
        return True


def main():
    parser = argparse.ArgumentParser(description="Habit Tracker CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Add habit
    add_parser = subparsers.add_parser("add", help="Add a new habit")
    add_parser.add_argument("name", help="Name of the habit")
    add_parser.add_argument("--period", choices=["daily", "weekly"], default="daily",
                            help="Period of the habit (daily or weekly)")

    # Complete habit
    complete_parser = subparsers.add_parser(
        "complete", help="Mark a habit as completed")
    complete_parser.add_argument("name", help="Name of the habit")
    complete_parser.add_argument("--date", help="Completion date (YYYY-MM-DD)")

    # Uncomplete habit
    uncomplete_parser = subparsers.add_parser(
        "uncomplete", help="Remove a logged completion")
    uncomplete_parser.add_argument("name", help="Name of the habit")
    uncomplete_parser.add_argument("--date", help="Completion date to remove (YYYY-MM-DD)")

    # Remove habit
    remove_parser = subparsers.add_parser("remove", help="Remove a habit")
    remove_parser.add_argument("name", help="Name of the habit")

    # Show a single habit
    show_parser = subparsers.add_parser(
        "show", help="Show one habit's stats and completion history")
    show_parser.add_argument("name", help="Name of the habit")

    # List habits
    subparsers.add_parser("list", help="List all habits and their stats")

    args = parser.parse_args()
    cli = HabitTrackerCLI()

    if args.command == "add":
        ok = cli.add_habit(args.name, args.period)
    elif args.command == "complete":
        ok = cli.complete_habit(args.name, args.date)
    elif args.command == "uncomplete":
        ok = cli.uncomplete_habit(args.name, args.date)
    elif args.command == "remove":
        ok = cli.remove_habit(args.name)
    elif args.command == "show":
        ok = cli.show_habit(args.name)
    elif args.command == "list":
        ok = cli.list_habits()
    else:
        parser.print_help()
        ok = False

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

import argparse
from datetime import datetime, date
from storage import Storage
from habit import Habit
from analytics import get_habit_stats, get_all_habits_stats, get_completion_rate


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


class HabitTrackerCLI:
    def __init__(self):
        self.storage = Storage()

    def add_habit(self, name, period="daily"):
        if not name or not name.strip():
            print("Error: Habit name cannot be empty")
            return

        if period not in ["daily", "weekly"]:
            print("Error: Period must be 'daily' or 'weekly'")
            return

        if self.storage.get_habit(name):
            print(f"Error: Habit '{name}' already exists")
            return

        habit = Habit(name, period)
        self.storage.add_habit(habit)
        print(f"Habit '{name}' added successfully!")

    def complete_habit(self, name, date_str=None):
        habit = self.storage.get_habit(name)
        if not habit:
            print(f"Error: Habit '{name}' not found")
            return

        completion_date = parse_date(date_str) if date_str else date.today()
        if not completion_date:
            print("Error: Invalid date format. Use YYYY-MM-DD")
            return

        if completion_date > date.today():
            print("Error: Completion date cannot be in the future")
            return

        habit.complete(completion_date)
        self.storage.add_habit(habit)
        print(f"Habit '{name}' marked as completed for {completion_date}")

    def remove_habit(self, name):
        if self.storage.remove_habit(name):
            print(f"Habit '{name}' removed successfully!")
        else:
            print(f"Error: Habit '{name}' not found")

    def list_habits(self):
        habits = self.storage.get_all_habits()
        if not habits:
            print("No habits found")
            return

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

    # Remove habit
    remove_parser = subparsers.add_parser("remove", help="Remove a habit")
    remove_parser.add_argument("name", help="Name of the habit")

    # List habits
    subparsers.add_parser("list", help="List all habits and their stats")

    args = parser.parse_args()
    cli = HabitTrackerCLI()

    if args.command == "add":
        cli.add_habit(args.name, args.period)
    elif args.command == "complete":
        cli.complete_habit(args.name, args.date)
    elif args.command == "remove":
        cli.remove_habit(args.name)
    elif args.command == "list":
        cli.list_habits()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

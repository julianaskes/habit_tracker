"""Command-line interface for the habit tracker."""

import argparse
import sys
from datetime import datetime, date
from storage import Storage
from habit import Habit
from analytics import (
    get_habit_stats,
    get_completion_rate,
    list_all_habits,
    habits_by_periodicity,
    longest_streak_overall,
    longest_streak_for_habit,
)
from seed_data import generate_seed_habits


def parse_date(date_str):
    """Parse a date or date+time string typed on the command line.

    Args:
        date_str: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM".

    Returns:
        date | datetime | None: a `date` for a bare date string, a
        `datetime` for a date+time string, or None if neither format matches.
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        pass
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def _error(message):
    """Print an error message to stderr, prefixed with "Error: "."""
    print(f"Error: {message}", file=sys.stderr)


class HabitTrackerCLI:
    """Adapts argparse subcommands to Storage/Habit/analytics calls.

    Each command method returns True on success or False on failure (after
    printing an error to stderr); `main()` maps that to the process exit code.
    """

    def __init__(self):
        """Open the default habits.db in the current working directory."""
        self.storage = Storage()

    def add_habit(self, name, period="daily"):
        """Create a new habit.

        Args:
            name: Habit name; must be non-empty and not already exist.
            period: "daily" or "weekly". Defaults to "daily".

        Returns:
            bool: True on success, False (with an stderr message) on failure.
        """
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
        """Mark a habit as completed.

        Args:
            name: Habit name.
            date_str: Optional "YYYY-MM-DD" or "YYYY-MM-DD HH:MM" string; a
                bare date is combined with the current time. Defaults to
                right now.

        Returns:
            bool: True on success, False (with an stderr message) on failure.
        """
        habit = self.storage.get_habit(name)
        if not habit:
            _error(f"Habit '{name}' not found")
            return False

        completion_moment = None
        if date_str:
            completion_moment = parse_date(date_str)
            if completion_moment is None:
                _error("Invalid date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM")
                return False

            completion_day = (completion_moment.date()
                               if isinstance(completion_moment, datetime)
                               else completion_moment)
            if completion_day > date.today():
                _error("Completion date cannot be in the future")
                return False

        recorded = habit.complete(completion_moment)
        self.storage.add_habit(habit)
        print(f"Habit '{name}' marked as completed for {recorded.strftime('%Y-%m-%d %H:%M')}")
        return True

    def uncomplete_habit(self, name, date_str=None):
        """Remove a logged completion.

        Args:
            name: Habit name.
            date_str: Optional "YYYY-MM-DD" or "YYYY-MM-DD HH:MM" string
                identifying which completion to remove. A bare date removes
                the most recent completion logged that day. Defaults to
                today.

        Returns:
            bool: True on success, False (with an stderr message) on failure.
        """
        habit = self.storage.get_habit(name)
        if not habit:
            _error(f"Habit '{name}' not found")
            return False

        completion_target = date.today()
        if date_str:
            completion_target = parse_date(date_str)
            if completion_target is None:
                _error("Invalid date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM")
                return False

        if not habit.uncomplete(completion_target):
            _error(f"'{name}' has no completion recorded for {completion_target}")
            return False

        self.storage.add_habit(habit)
        print(f"Completion for '{name}' on {completion_target} removed")
        return True

    def remove_habit(self, name):
        """Delete a habit entirely.

        Args:
            name: Habit name.

        Returns:
            bool: True on success, False (with an stderr message) on failure.
        """
        if self.storage.remove_habit(name):
            print(f"Habit '{name}' removed successfully!")
            return True
        _error(f"Habit '{name}' not found")
        return False

    def show_habit(self, name):
        """Print one habit's stats and full completion history.

        Args:
            name: Habit name.

        Returns:
            bool: True on success, False (with an stderr message) on failure.
        """
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
                print(f"  - {d.strftime('%Y-%m-%d %H:%M')}")
        else:
            print("No completions yet")
        return True

    def list_habits(self):
        """Print every habit's stats.

        Returns:
            bool: Always True (an empty habit list is not an error).
        """
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

    def list_names(self):
        """Print the names of all tracked habits (analytics.list_all_habits).

        Returns:
            bool: Always True (an empty habit list is not an error).
        """
        names = list_all_habits(self.storage.get_all_habits())
        if not names:
            print("No habits found")
            return True
        print("\n".join(names))
        return True

    def list_by_period(self, period):
        """Print habit names matching a period (analytics.habits_by_periodicity).

        Args:
            period: "daily" or "weekly".

        Returns:
            bool: True on success, False (with an stderr message) on failure.
        """
        if period not in ("daily", "weekly"):
            _error("Period must be 'daily' or 'weekly'")
            return False

        names = habits_by_periodicity(self.storage.get_all_habits(), period)
        if not names:
            print(f"No {period} habits found")
            return True
        print("\n".join(names))
        return True

    def top_streak(self):
        """Print the habit with the longest streak overall.

        Returns:
            bool: True on success, False (with an stderr message) on failure.
        """
        habits = self.storage.get_all_habits()
        if not habits:
            print("No habits found")
            return True

        name, streak = longest_streak_overall(habits)
        print(f"{name}: {streak}")
        return True

    def habit_streak(self, name):
        """Print one habit's longest streak (analytics.longest_streak_for_habit).

        Args:
            name: Habit name.

        Returns:
            bool: True on success, False (with an stderr message) on failure.
        """
        habit = self.storage.get_habit(name)
        if not habit:
            _error(f"Habit '{name}' not found")
            return False

        print(f"{name}: {longest_streak_for_habit(habit)}")
        return True

    def load_demo(self):
        """Load the 5 predefined demo habits (seed_data.py) into storage.

        Habits whose name already exists are left untouched -- add_habit's
        duplicate protection applies here too, so this is safe to re-run.

        Returns:
            bool: Always True (nothing left to add is not an error).
        """
        loaded = []
        skipped = []
        for habit in generate_seed_habits():
            if self.storage.get_habit(habit.name):
                skipped.append(habit.name)
                continue
            self.storage.add_habit(habit)
            loaded.append(habit.name)

        if loaded:
            print(f"Loaded {len(loaded)} demo habit(s): {', '.join(loaded)}")
        if skipped:
            print(f"Skipped {len(skipped)} already-existing habit(s): {', '.join(skipped)}")
        return True


def main():
    """Parse command-line arguments and dispatch to a CLI method."""
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
    complete_parser.add_argument(
        "--date", help="Completion date/time (YYYY-MM-DD or YYYY-MM-DD HH:MM)")

    # Uncomplete habit
    uncomplete_parser = subparsers.add_parser(
        "uncomplete", help="Remove a logged completion")
    uncomplete_parser.add_argument("name", help="Name of the habit")
    uncomplete_parser.add_argument(
        "--date", help="Completion date/time to remove (YYYY-MM-DD or YYYY-MM-DD HH:MM)")

    # Remove habit
    remove_parser = subparsers.add_parser("remove", help="Remove a habit")
    remove_parser.add_argument("name", help="Name of the habit")

    # Show a single habit
    show_parser = subparsers.add_parser(
        "show", help="Show one habit's stats and completion history")
    show_parser.add_argument("name", help="Name of the habit")

    # List habits
    subparsers.add_parser("list", help="List all habits and their stats")

    # List habit names only
    subparsers.add_parser("names", help="List the names of all tracked habits")

    # Habits filtered by periodicity
    by_period_parser = subparsers.add_parser(
        "by-period", help="List habit names matching a period")
    by_period_parser.add_argument(
        "period", choices=["daily", "weekly"], help="daily or weekly")

    # Habit with the longest streak overall
    subparsers.add_parser(
        "top-streak", help="Show the habit with the longest streak overall")

    # Longest streak for one habit
    streak_parser = subparsers.add_parser(
        "streak", help="Show one habit's longest streak")
    streak_parser.add_argument("name", help="Name of the habit")

    # Load predefined demo habits
    subparsers.add_parser(
        "load-demo", help="Load 5 predefined demo habits with sample history")

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
    elif args.command == "names":
        ok = cli.list_names()
    elif args.command == "by-period":
        ok = cli.list_by_period(args.period)
    elif args.command == "top-streak":
        ok = cli.top_streak()
    elif args.command == "streak":
        ok = cli.habit_streak(args.name)
    elif args.command == "load-demo":
        ok = cli.load_demo()
    else:
        parser.print_help()
        ok = False

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

"""Standalone script: generate the predefined demo habits into a throwaway
test_habits.db (via seed_data.generate_seed_habits) for manual inspection,
without touching the user's real habits.db. See cli.py's `load-demo`
command for loading the same predefined habits into the real database.
"""

import os
import sys

# Allow running this script directly (`python tests/generate_test_data.py`)
# by putting the repo root -- where storage.py/habit.py/seed_data.py live --
# on sys.path, since Python only auto-adds the script's own directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage import Storage
from seed_data import generate_seed_habits


def generate_test_data():
    """Generate 4 weeks of predefined habit data into test_habits.db.

    Returns:
        Storage: the Storage instance the habits were written to.
    """
    storage = Storage("test_habits.db")
    for habit in generate_seed_habits():
        storage.add_habit(habit)
    return storage


def print_test_data_summary(storage):
    """Print a summary of the generated test data.

    Args:
        storage: Storage instance to read habits from.
    """
    print("\nTest Data Summary:")
    print("-" * 50)

    for habit in storage.get_all_habits():
        stats = {
            "name": habit.name,
            "period": habit.period,
            "total_completions": len(habit.completed_dates),
            "current_streak": habit.streak,
            "longest_streak": habit.longest_streak
        }

        print(f"\nHabit: {stats['name']}")
        print(f"Period: {stats['period']}")
        print(f"Total Completions: {stats['total_completions']}")
        print(f"Current Streak: {stats['current_streak']}")
        print(f"Longest Streak: {stats['longest_streak']}")
        print(
            f"Completion Dates: {[d.strftime('%Y-%m-%d %H:%M') for d in sorted(habit.completed_dates)]}")
        print("-" * 30)


if __name__ == "__main__":
    storage = generate_test_data()
    print_test_data_summary(storage)

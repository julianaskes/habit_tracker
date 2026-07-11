"""Shared generation of the predefined demo habit data set.

Extracted so both `tests/generate_test_data.py` (writes to an isolated
test_habits.db) and `cli.py load-demo` (writes into the user's real
habits.db) generate the same 5 predefined habits from a single source of
truth.
"""

from datetime import datetime, timedelta
import random

from habit import Habit

PREDEFINED_HABITS = [
    ("Morning Meditation", "daily", 0.9),    # 90% completion rate
    ("Exercise", "daily", 0.7),              # 70% completion rate
    ("Read Book", "daily", 0.8),             # 80% completion rate
    ("Weekly Review", "weekly", 0.75),       # 75% completion rate
    ("Deep House Cleaning", "weekly", 1.0),  # 100% completion rate
]


def generate_seed_habits(weeks=4, seed=42):
    """Build the 5 predefined demo habits with synthetic completion history.

    Uses a private random.Random instance (rather than the `random` module's
    global state) so calling this doesn't affect unrelated code that also
    uses randomness.

    Args:
        weeks: How many weeks of completion history to generate.
        seed: Random seed, for reproducible output.

    Returns:
        list[Habit]: Fully populated Habit objects, not yet persisted.
    """
    rng = random.Random(seed)
    today = datetime.now().date()
    start_date = today - timedelta(days=weeks * 7)

    habits = []
    for name, period, completion_rate in PREDEFINED_HABITS:
        habit = Habit(name, period)
        current_date = start_date
        while current_date <= today:
            if period == "weekly" and current_date.weekday() != 0:
                current_date += timedelta(days=1)
                continue

            if rng.random() < completion_rate:
                habit.complete(current_date)

            current_date += timedelta(days=1)

        habits.append(habit)

    return habits

from datetime import datetime, timedelta
from storage import Storage
from habit import Habit
import random


def generate_test_data():
    """Generate 4 weeks of test data for various habits"""
    storage = Storage("test_habits.db")

    # Create habits
    habits = [
        ("Morning Meditation", "daily", 0.9),  # 90% completion rate
        ("Exercise", "daily", 0.7),            # 70% completion rate
        ("Read Book", "daily", 0.8),           # 80% completion rate
        ("Weekly Review", "weekly", 0.75),      # 75% completion rate
        ("Deep House Cleaning", "weekly", 1.0)  # 100% completion rate
    ]

    today = datetime.now().date()
    four_weeks_ago = today - timedelta(days=28)

    for habit_name, period, completion_rate in habits:
        habit = Habit(habit_name, period)

        # Generate completion dates
        current_date = four_weeks_ago
        while current_date <= today:
            # For weekly habits, only consider once per week
            if period == "weekly" and current_date.weekday() != 0:
                current_date += timedelta(days=1)
                continue

            # Randomly complete based on completion rate
            if random.random() < completion_rate:
                habit.complete(current_date)

            current_date += timedelta(days=1)

        storage.add_habit(habit)

    return storage


def print_test_data_summary(storage):
    """Print a summary of the generated test data"""
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
            f"Completion Dates: {[d.strftime('%Y-%m-%d') for d in sorted(habit.completed_dates)]}")
        print("-" * 30)


if __name__ == "__main__":
    # Set random seed for reproducible results
    random.seed(42)

    # Generate test data
    storage = generate_test_data()

    # Print summary
    print_test_data_summary(storage)

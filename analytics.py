from datetime import date, timedelta


def get_habit_stats(habit):
    return {
        "name": habit.name,
        "period": habit.period,
        "current_streak": habit.streak,
        "longest_streak": habit.longest_streak,
        "total_completions": len(habit.completed_dates)
    }


def get_all_habits_stats(habits):
    return [get_habit_stats(habit) for habit in habits]


def get_completion_rate(habit, days=30):
    if not habit.completed_dates:
        return 0.0

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    completed_in_period = sum(
        1 for d in habit.completed_dates
        if start_date <= d <= end_date
    )

    expected_completions = days if habit.period == "daily" else (days // 7)
    return (completed_in_period / expected_completions) * 100 if expected_completions > 0 else 0

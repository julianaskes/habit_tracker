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

    in_window = [d for d in habit.completed_dates if start_date <= d <= end_date]

    if habit.period == "weekly":
        # Count distinct Monday-aligned weeks so multiple completions in the
        # same week don't inflate the rate (mirrors the streak logic).
        completed_units = len({d - timedelta(days=d.weekday()) for d in in_window})
        expected_completions = days // 7
    else:
        completed_units = len(in_window)  # daily completions are unique per day
        expected_completions = days

    if expected_completions <= 0:
        return 0.0

    # The window spans days+1 inclusive calendar days, so a fully-completed
    # period can exceed the nominal expectation; clamp to a sane 100%.
    rate = (completed_units / expected_completions) * 100
    return min(rate, 100.0)

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
    window_start = end_date - timedelta(days=days)

    # Don't count time before the habit was being tracked: its creation date,
    # or its first logged completion if that is earlier (e.g. backdated). This
    # keeps a brand-new habit from being judged against days it didn't exist.
    tracking_start = min(habit.created_at.date(), min(habit.completed_dates))
    observed_start = max(window_start, tracking_start)

    in_window = [d for d in habit.completed_dates if observed_start <= d <= end_date]

    if habit.period == "weekly":
        # Count distinct Monday-aligned weeks so multiple completions in the
        # same week don't inflate the rate (mirrors the streak logic).
        completed_units = len({d - timedelta(days=d.weekday()) for d in in_window})
        obs_monday = observed_start - timedelta(days=observed_start.weekday())
        end_monday = end_date - timedelta(days=end_date.weekday())
        expected_completions = (end_monday - obs_monday).days // 7 + 1
    else:
        completed_units = len(in_window)  # daily completions are unique per day
        expected_completions = (end_date - observed_start).days + 1

    if expected_completions <= 0:
        return 0.0

    # A fully-completed period can still edge over the nominal expectation;
    # clamp to a sane 100%.
    rate = (completed_units / expected_completions) * 100
    return min(rate, 100.0)

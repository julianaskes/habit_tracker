"""Pure functions for deriving habit statistics from Habit objects.

Every function here is read-only: none of them mutate the Habit(s) passed
in. `list_all_habits`, `habits_by_periodicity`, `longest_streak_for_habit`,
and `longest_streak_overall` are written in a functional style (map, filter,
functools.reduce, itertools.groupby) rather than explicit loops.
"""

from datetime import date, timedelta
from functools import reduce
from itertools import groupby


def get_habit_stats(habit):
    """Summarize one habit's cached stats into a plain dict.

    Args:
        habit: A Habit object.

    Returns:
        dict: name, period, current_streak, longest_streak, total_completions.
    """
    return {
        "name": habit.name,
        "period": habit.period,
        "current_streak": habit.streak,
        "longest_streak": habit.longest_streak,
        "total_completions": len(habit.completed_dates)
    }


def get_all_habits_stats(habits):
    """Summarize a list of habits via get_habit_stats.

    Args:
        habits: Iterable of Habit objects.

    Returns:
        list[dict]: One stats dict per habit, in the given order.
    """
    return [get_habit_stats(habit) for habit in habits]


def get_completion_rate(habit, days=30):
    """Compute a habit's completion rate over its tracked span.

    The measured window is the intersection of the last `days` calendar
    days and the habit's actual tracked span (from its creation date, or
    its earliest completion if that's earlier), so a new habit is not
    penalized for days before it existed. Weekly habits are scored by
    distinct Monday-aligned weeks completed, not raw completion count.

    Args:
        habit: A Habit object.
        days: Size of the lookback window in days. Defaults to 30.

    Returns:
        float: Completion rate as a percentage, clamped to [0, 100].
    """
    if not habit.completed_dates:
        return 0.0

    # completed_dates holds full timestamps; completion rate only cares
    # about which calendar day each one falls on.
    completion_days = [c.date() for c in habit.completed_dates]

    end_date = date.today()
    window_start = end_date - timedelta(days=days)

    # Don't count time before the habit was being tracked: its creation date,
    # or its first logged completion if that is earlier (e.g. backdated). This
    # keeps a brand-new habit from being judged against days it didn't exist.
    tracking_start = min(habit.created_at.date(), min(completion_days))
    observed_start = max(window_start, tracking_start)

    in_window = [d for d in completion_days if observed_start <= d <= end_date]

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


def list_all_habits(habits):
    """List the names of all currently tracked habits.

    Args:
        habits: Iterable of Habit objects.

    Returns:
        list[str]: Habit names, in the given order.
    """
    return list(map(lambda h: h.name, habits))


def habits_by_periodicity(habits, period):
    """List the names of habits matching a given period.

    Args:
        habits: Iterable of Habit objects.
        period: "daily" or "weekly".

    Returns:
        list[str]: Names of habits whose `period` matches.
    """
    return list(map(lambda h: h.name, filter(lambda h: h.period == period, habits)))


def longest_streak_for_habit(habit):
    """Compute a habit's longest streak directly from its completion history.

    Derived independently of the cached `habit.longest_streak` attribute:
    groups `habit.completed_dates` into calendar days (daily habits) or
    Monday-aligned calendar weeks (weekly habits), then finds the size of
    the largest run of consecutive units. Unlike `Habit._calculate_streak`,
    this has no notion of a "current" streak lapsing -- it is purely
    historical.

    Args:
        habit: A Habit object.

    Returns:
        int: The longest run of consecutive periods, or 0 if the habit has
        no completions.
    """
    if not habit.completed_dates:
        return 0

    weekly = habit.period == "weekly"
    bucket = (lambda d: d.date() - timedelta(days=d.date().weekday())) if weekly \
        else (lambda d: d.date())
    step = 7 if weekly else 1

    units = sorted(set(map(bucket, habit.completed_dates)))

    # Whether each unit (after the first) is consecutive with its predecessor.
    is_consecutive = map(lambda pair: (pair[1] - pair[0]).days == step,
                          zip(units, units[1:]))

    # Assign each unit a run id: the same id as the previous unit when
    # consecutive with it, otherwise a new (incremented) id. groupby then
    # clusters consecutive units sharing an id, and the longest streak is
    # the size of the largest such cluster.
    run_ids = reduce(
        lambda ids, consecutive: ids + [ids[-1] if consecutive else ids[-1] + 1],
        is_consecutive, [0]
    )
    run_lengths = map(lambda group: len(list(group[1])), groupby(run_ids))
    return max(run_lengths, default=0)


def longest_streak_overall(habits):
    """Identify the habit with the longest streak among all given habits.

    Args:
        habits: Iterable of Habit objects.

    Returns:
        tuple[str, int]: (habit_name, streak_length) for the habit whose
        longest_streak_for_habit() is greatest. Ties go to whichever habit
        is encountered first. Returns ("", 0) if `habits` is empty.
    """
    streaks = map(lambda h: (h.name, longest_streak_for_habit(h)), habits)
    return reduce(lambda best, current: current if current[1] > best[1] else best,
                  streaks, ("", 0))

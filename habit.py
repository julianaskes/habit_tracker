"""Core Habit domain model: completion logging and streak calculation."""

from datetime import datetime, date, timedelta


class Habit:
    """A single tracked habit and its completion history.

    Attributes:
        name: The habit's unique name.
        period: "daily" or "weekly".
        created_at: When the habit was created (datetime).
        completed_dates: list[datetime] of every logged completion, each
            carrying both the calendar day and time of day it happened.
        streak: The current streak as of today (0 if it has lapsed).
        longest_streak: The longest streak ever achieved.
    """

    def __init__(self, name, period="daily", created_at=None):
        """Create a new (not-yet-persisted) habit.

        Args:
            name: Habit name.
            period: "daily" or "weekly". Defaults to "daily".
            created_at: Optional datetime of creation; defaults to now.
        """
        self.name = name
        self.period = period  # "daily" or "weekly"
        self.created_at = created_at or datetime.now()
        self.completed_dates = []
        self.streak = 0
        self.longest_streak = 0

    @staticmethod
    def _normalize_moment(moment):
        """Resolve a completion argument into a concrete datetime.

        Args:
            moment: None (-> right now), a `date` (-> that calendar day
                combined with the current time), or a `datetime` (returned
                unchanged, preserving its explicit time).

        Returns:
            datetime: The resolved completion timestamp.
        """
        if moment is None:
            return datetime.now()
        if isinstance(moment, datetime):
            return moment
        return datetime.combine(moment, datetime.now().time())

    def complete(self, completion_date=None):
        """Log a completion.

        Args:
            completion_date: None (defaults to right now), a `date`
                (combined with the current time of day), or an explicit
                `datetime`.

        Returns:
            datetime: The completion timestamp that was recorded (or that
            already existed, if this call was a no-op duplicate).
        """
        moment = self._normalize_moment(completion_date)
        if moment not in self.completed_dates:
            self.completed_dates.append(moment)
            self._calculate_streak()
        return moment

    def uncomplete(self, completion_date=None):
        """Remove a logged completion. Returns True if one was removed.

        Args:
            completion_date: None (removes today's most recent completion),
                a `date` (removes the most recent completion logged on that
                calendar day), or an explicit `datetime` (removes that exact
                completion only).

        Returns:
            bool: True if a completion was removed, False if none matched.
        """
        if completion_date is None:
            completion_date = date.today()

        if isinstance(completion_date, datetime):
            matches = [d for d in self.completed_dates if d == completion_date]
        else:
            matches = [d for d in self.completed_dates if d.date() == completion_date]

        if not matches:
            return False

        self.completed_dates.remove(max(matches))
        self._calculate_streak()
        return True

    def recalculate_streaks(self):
        """Recompute current/longest streak from completed_dates as of today.

        The current streak lapses over time, so a value persisted while a
        habit was active can be stale when re-read on a later day. Callers
        that load a habit from storage should invoke this to refresh it.
        """
        self._calculate_streak()

    def _calculate_streak(self):
        """Recompute self.streak and self.longest_streak from history.

        Groups completions into calendar days (daily habits) or
        Monday-aligned calendar weeks (weekly habits), then finds the
        longest run of consecutive units and whether that run is still
        "current" (its most recent unit is today/this week, or one step
        back as a grace period before an as-yet-undone period reads as
        broken).
        """
        if not self.completed_dates:
            self.streak = 0
            self.longest_streak = 0
            return

        today = date.today()
        if self.period == "weekly":
            # Collapse completions to one entry per calendar week (Monday-aligned)
            # so multiple completions in the same week don't inflate the streak.
            dates = sorted({d.date() - timedelta(days=d.date().weekday()) for d in self.completed_dates})
            step = 7
            reference = today - timedelta(days=today.weekday())
        else:
            dates = sorted({d.date() for d in self.completed_dates})
            step = 1
            reference = today

        current_streak = 1
        longest_in_history = 1
        for i in range(len(dates) - 1):
            date_diff = (dates[i + 1] - dates[i]).days
            if date_diff == step:
                current_streak += 1
            else:
                current_streak = 1
            longest_in_history = max(longest_in_history, current_streak)

        # The run above ends at the most recent completion. It only counts as
        # the *current* streak if that completion is still alive: today/this
        # week (gap 0) or one step ago (grace period so an as-yet-undone today
        # doesn't read as broken). If the last completion is older, the streak
        # has lapsed and the current streak is zero.
        gap = (reference - dates[-1]).days
        self.streak = current_streak if gap <= step else 0
        # Derived purely from the full completion history, so it stays accurate
        # even when a completion is removed via uncomplete().
        self.longest_streak = longest_in_history

    def __repr__(self):
        return f"Habit(name='{self.name}', period='{self.period}', streak={self.streak})"

from datetime import datetime, timedelta
from queue import Queue
from typing import Optional

from src.utils.datetime import strfdelta


class TimedTaskLimiter:
    def __init__(self, time_interval: timedelta) -> None:
        super().__init__()

        self._time_interval = time_interval
        self._last_time_that_did_task = datetime.min

    @property
    def time_interval(self) -> timedelta:
        return self._time_interval

    @property
    def last_time_that_did_task(self) -> datetime:
        return self._last_time_that_did_task

    def can_do_task(self, start_time: datetime = datetime.now()) -> bool:
        return (start_time - self._last_time_that_did_task) \
               > self._time_interval

    def did_task(self) -> None:
        self._last_time_that_did_task = datetime.now()

    def reset(self) -> None:
        self._last_time_that_did_task = datetime.min

    def set_last_time_that_did_task(self, time: datetime) -> None:
        self._last_time_that_did_task = time


class TimedOccurrenceTracker:
    def __init__(self, max_occurrences: int, time_interval: timedelta) -> None:
        super().__init__()

        self._max_occurrences = max_occurrences
        self._time_interval = time_interval

        self._last_occurrences = Queue(maxsize=max_occurrences)
        self.reset()

    @property
    def max_occurrences(self) -> int:
        return self._max_occurrences

    @property
    def time_interval(self) -> timedelta:
        return self._time_interval

    @property
    def time_interval_pretty(self) -> str:
        return strfdelta(self.time_interval, "{hours}h, {minutes}m, {seconds}s")

    def action_happened(self, at_time: Optional[datetime] = None) -> None:
        # Default: get current time
        if at_time is None:
            at_time = datetime.now()

        self._last_occurrences.get()
        self._last_occurrences.put(at_time)

    def too_many_occurrences(self, from_time: Optional[datetime] = None) \
            -> bool:
        # Default: get current time
        if from_time is None:
            from_time = datetime.now()

        # noinspection PyUnresolvedReferences
        oldest_occurrence = self._last_occurrences.queue[0]
        return (from_time - oldest_occurrence) < self._time_interval

    def reset(self) -> None:
        while not self._last_occurrences.empty():
            self._last_occurrences.get()
        for i in range(self._max_occurrences):
            self._last_occurrences.put(datetime.min)

from datetime import datetime, timedelta
from queue import Queue
from typing import Optional, Any

from src.utils.datetime import strfdelta


class TimedTaskLimiter:
    def __init__(self, time_interval: timedelta) -> None:
        super().__init__()

        self._time_interval = time_interval
        self._last_time_that_did_task = datetime.min

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    @property
    def time_interval(self) -> timedelta:
        return self._time_interval

    @property
    def last_time_that_did_task(self) -> datetime:
        return self._last_time_that_did_task

    def can_do_task(self, start_time: datetime = None) -> bool:
        if start_time is None:
            start_time = datetime.now()

        return \
            (start_time - self._last_time_that_did_task) >= self._time_interval

    def did_task(self) -> None:
        self._last_time_that_did_task = datetime.now()

    def reset(self) -> None:
        self._last_time_that_did_task = datetime.min

    def set_last_time_that_did_task(self, time: datetime) -> None:
        self._last_time_that_did_task = time


class TimedTaskTracker:
    def __init__(self, time_interval: timedelta) -> None:
        super().__init__()

        self._time_interval = time_interval
        self._start_time = datetime.min
        self._timer_started = False
        self._did_task = False

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    @property
    def time_interval(self) -> timedelta:
        return self._time_interval

    @property
    def did_task(self) -> bool:
        return self._did_task

    @property
    def timer_started(self) -> bool:
        return self._timer_started

    @property
    def start_time(self) -> datetime:
        return self._start_time

    def start_timer(self, start_time: datetime = None) -> None:
        if start_time is None:
            self._start_time = datetime.now()
        else:
            self._start_time = start_time

        self._timer_started = True
        self._did_task = False

    def can_do_task(self, time: datetime = None) -> bool:
        if not self.timer_started or self.did_task:
            return False
        else:
            if time is None:
                time = datetime.now()

            return (time - self.start_time) >= self.time_interval

    def do_task(self) -> None:
        if self.timer_started:
            self._did_task = True

    def reset(self) -> None:
        self._timer_started = False
        self._did_task = False
        self._start_time = datetime.min


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


class OccurrencesInTimePeriodTracker:
    """
    This class keeps track of how many occurrences happened in a time period.
    Each element represents the time of an occurrence and thus the length of the
    queue is the number of occurrences. When adding a new occurrence the class
    attempts to keep the occurrences happened within a time period.
    """

    def __init__(self, time_period: timedelta) -> None:
        super().__init__()

        self._time_period = time_period
        self._occurrences_queue = Queue()

    def __eq__(self, other: Any) -> bool:
        """
        This function checks that all keys and values are the same for both
        objects except for the `self._occurrences_queue` variable. This is
        omitted because __eq__ was not implemented for the Queue object.
        :param other: Other objects
        :return: True if conditions described above are matched
               : False otherwise
        """

        if self.__dict__.keys() != other.__dict__.keys():
            return False

        for key, val in self.__dict__.items():
            if not key == '_occurrences_queue' \
                    and not val == other.__dict__[key]:
                return False

        return True

    @property
    def time_period(self) -> timedelta:
        return self._time_period

    def add_occurrence(self, time: datetime = None) -> None:
        if time is None:
            time = datetime.now()

        self.remove_old_occurrences(time)

        self._occurrences_queue.put(time)

    def remove_old_occurrences(self, time: datetime = None) -> None:
        if time is None:
            time = datetime.now()

        while not self._occurrences_queue.empty():
            oldest_occurrence = self._occurrences_queue.queue[0]
            if (time - oldest_occurrence) > self.time_period:
                self._occurrences_queue.get()
            else:
                break

    def no_of_occurrences(self) -> int:
        return self._occurrences_queue.qsize()

    def reset(self) -> None:
        self._occurrences_queue.queue.clear()

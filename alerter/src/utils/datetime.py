import datetime

import dateutil.parser


def strfdelta(delta: datetime.timedelta, fmt: str) -> str:
    # Get hours, minutes, seconds
    d = {}
    d['hours'], rem = divmod(delta.seconds, 3600)
    d['minutes'], d['seconds'] = divmod(rem, 60)

    # In the case of days, if not in fmt, add to hours
    if 'days' in fmt:
        d['days'] = delta.days
    else:
        d['hours'] += delta.days * 24

    return fmt.format(**d)


def json_to_unix_time(time: str) -> float:
    datetime_object = dateutil.parser.parse(time)
    return datetime.datetime.timestamp(datetime_object)


def iso_to_epoch(time):
    """
    This function takes a ISO time in the format: YYYY-MM-DDTHH:MM:SS.FFFFFFFFFZ
    The final 4 values of the input string are removed, and strptime is used
    to convert the ISO string into a UNIX timestamp.

    This function is currently generalized and may be modified to accomodate for
    other time formats in the future.
    """
    time = str(time)[:-4]
    time = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%f')
    return time.timestamp()

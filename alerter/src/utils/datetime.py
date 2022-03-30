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

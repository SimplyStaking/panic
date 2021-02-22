from time import sleep
from unittest.mock import Mock


def infinite_fn() -> None:
    while True:
        sleep(10)


def assert_not_called_with(mocked_function: Mock, *args, **kwargs):
    try:
        mocked_function.assert_has_calls(*args, **kwargs)
    except AssertionError:
        return
    raise AssertionError(
        'Expected %s to not have been called.' %
        mocked_function._format_mock_call_signature(args, kwargs))

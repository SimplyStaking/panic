from typing import Any

REATTEMPTING_MESSAGE = "Re-attempting the initialisation procedure"


def get_initialisation_error_message(name: str, exception: Exception) -> str:
    return "'!!! Error when initialising {}: {} !!!".format(name, exception)


def get_reattempting_message(reattempting_what: str) -> str:
    return "Re-attempting initialisation procedure of {}".format(
        reattempting_what)


def get_stopped_message(what_stopped: Any) -> str:
    return "{} stopped.".format(what_stopped)

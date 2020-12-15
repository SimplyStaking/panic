from typing import FrozenSet, Iterable


class EmailChannelConfig:
    def __init__(self, id_: str, config_name: str, smtp: str, email_from: str,
                 emails_to: Iterable[str], username: str, password: str):
        self._id_ = id_
        self._config_name = config_name
        self._smtp = smtp
        self._email_from = "PANIC <{}>".format(email_from)
        self._emails_to = frozenset(emails_to)
        self._username = username
        self._password = password

    @property
    def id_(self) -> str:
        return self._id_

    @property
    def config_name(self) -> str:
        return self._config_name

    @property
    def smtp(self) -> str:
        return self._smtp

    @property
    def email_from(self) -> str:
        return self._email_from

    # We use frozen sets to make it immutable
    @property
    def emails_to(self) -> FrozenSet[str]:
        return self._emails_to

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

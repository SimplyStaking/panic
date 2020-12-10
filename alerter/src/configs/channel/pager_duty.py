class PagerDutyChannelConfig:
    def __init__(self, id_: str, config_name: str, api_token: str,
                 integration_key: str):
        self._id_ = id_
        self._config_name = config_name
        self._api_token = api_token
        self._integration_key = integration_key

    @property
    def id_(self) -> str:
        return self._id_

    @property
    def config_name(self) -> str:
        return self._config_name

    @property
    def api_token(self) -> str:
        return self._api_token

    @property
    def integration_key(self) -> str:
        return self._integration_key

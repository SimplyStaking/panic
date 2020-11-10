import opsgenie_sdk


class OpsgenieApi:
    def __init__(self, opsgenie_api_key: str, eu_host: bool):
        api_configuration = opsgenie_sdk.configuration.Configuration()
        api_configuration.api_key['Authorization'] = opsgenie_api_key
        api_configuration.host = 'https://api.eu.opsgenie.com' if eu_host \
            else 'https://api.opsgenie.com'

        self._client = opsgenie_sdk.api_client.ApiClient(
            configuration=api_configuration)
        self._alert_api = opsgenie_sdk.AlertApi(api_client=self._client)
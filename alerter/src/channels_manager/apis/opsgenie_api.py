from datetime import datetime
from typing import Optional

import opsgenie_sdk
from opsgenie_sdk import SuccessResponse

from src.utils.types import OpsgenieSeverities


# Calls to Opsgenie can be both synchronous and synchronous. In this case the
# calls are being made in a synchronous fashion. Note that internally Opsgenie
# still processes alerts asynchronously.

class OpsgenieApi:
    def __init__(self, opsgenie_api_key: str, eu_host: bool):
        api_configuration = opsgenie_sdk.configuration.Configuration()
        api_configuration.api_key['Authorization'] = opsgenie_api_key
        api_configuration.host = 'https://api.eu.opsgenie.com' if eu_host \
            else 'https://api.opsgenie.com'

        self._client = opsgenie_sdk.api_client.ApiClient(
            configuration=api_configuration)
        self._alert_api = opsgenie_sdk.AlertApi(api_client=self._client)

    def create_alert(self, alert_name: str, alert_message: str,
                     severity: OpsgenieSeverities, origin: str,
                     timestamp: float, alias: str = None) \
            -> Optional[SuccessResponse]:
        payload = opsgenie_sdk.CreateAlertPayload(
            message=alert_name,
            description='Message: {} \n Triggered at: {}'.format(
                alert_message, datetime.fromtimestamp(timestamp)),
            priority=severity.value,
            source=origin,
            alias=alias
        )
        return self._alert_api.create_alert(create_alert_payload=payload)

    def close_alert(self, alert_id: str) -> Optional[SuccessResponse]:
        payload = opsgenie_sdk.CloseAlertPayload()
        return self._alert_api.close_alert(identifier=alert_id,
                                           close_alert_payload=payload)

    def update_severity(self, severity: OpsgenieSeverities, alert_id: str) \
            -> Optional[SuccessResponse]:
        payload = opsgenie_sdk.UpdateAlertPriorityPayload(
            priority=severity.value)
        return self._alert_api.update_alert_priority(
            identifier=alert_id, update_alert_priority_payload=payload)

    def update_message(self, message: str, alert_id: str) \
            -> Optional[SuccessResponse]:
        payload = opsgenie_sdk.UpdateAlertMessagePayload(message=message)
        return self._alert_api.update_alert_message(
            identifier=alert_id, update_alert_message_payload=payload)

    def update_description(self, description: str, alert_id: str) \
            -> Optional[SuccessResponse]:
        payload = opsgenie_sdk.UpdateAlertDescriptionPayload(
            description=description)
        return self._alert_api.update_alert_description(
            identifier=alert_id, update_alert_description_payload=payload)

    def get_request_status(self, request_id: str) \
            -> Optional[SuccessResponse]:
        return self._alert_api.get_request_status(request_id=request_id)

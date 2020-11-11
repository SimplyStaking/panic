from datetime import datetime

from pdpyras import EventsAPISession


# TODO: Must handle exceptions in the caller just in case request fails.

class PagerDutyApi:
    def __init__(self, integration_key: str) -> None:
        self._session = EventsAPISession(integration_key)

    # This method returns the dedup key. Exceptions must be handled by the
    # caller
    def trigger(self, alert_message: str, severity: str, origin: str,
                timestamp: float, dedup_key: str = None) -> str:
        return self._session.trigger(
            summary=alert_message, source=origin, dedup_key=dedup_key,
            severity=severity, payload={
                'timestamp': datetime.fromtimestamp(timestamp).isoformat()})

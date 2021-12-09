from typing import Dict

from src.alerter.alert_data.alert_data import AlertData


class ChainlinkContractAlertData(AlertData):
    """
    ChainlinkContractAlertData will store extra information needed for the
    data store such as the contract_proxy_address.
    """

    def __init__(self):
        super().__init__()

    @property
    def alert_data(self) -> Dict:
        return self._alert_data

    def set_alert_data(self, contract_proxy_address: str) -> None:
        self._alert_data = {
            'contract_proxy_address': contract_proxy_address
        }

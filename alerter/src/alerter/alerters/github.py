from src.alerter.alerters.alerter import Alerter

class GithubAlerter(Alerter):
    def __init__(self, alerter_name: str, logger: logging.Logger) -> None:
        super().__init__(alerter_name, logger)

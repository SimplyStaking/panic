from time import sleep

from src.alerter.alert_code import AlertCode


def infinite_fn() -> None:
    while True:
        sleep(10)


class DummyAlertCode(AlertCode):
    TEST_ALERT_CODE = 'test_alert_code'
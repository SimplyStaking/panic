Change the contents of this file to this:

# Change Log

## Unreleased

- Fixed tests to work with alerter changes. Merged multiple tests into one using parameterization.
- Updated Alerter to fix bugs with regards to metric changes in thresholds.
- Added Internal Alerts on startup originating from the Alerter, which are used to reset all metrics for that chain.
- Added functionality to cater for new Internal Alert in Data Store.
- Added Tests for new Internal Alerts in System/Github Alerter and Alert Store.
- Added the ChainlinkNodeMonitor, NodeMonitorsManager, and their tests.
- Refactored RabbitMQ queues and routing keys.
- The SystemMonitorsManager additionally now parses systems belonging to chains from the `system_config.ini` if Chainlink is the base chain. Same schema as `GENERAL` is expected.

## 0.1.2

Released on 25th March 2021

- Fixed bug in the web-installer where the BLACKLIST wasn't being exported properly

## 0.1.1

Released on 24th March 2021

- Fixed bug where the `metric_not_found` key was missing inside the store keys.
- Fixed tests having issues running in docker and pipenv.

## 0.1.0

Released on 22nd March 2021

This version contains the following:
* A base alerter that can alert about the host system the nodes are running by monitoring system metrics exposed by node exporter
* A base alerter that can alert on new releases for any GitHub repository.
* Multiple alerting channels supported, namely PagerDuty, OpsGenie, Telegram, E-mail and Twilio.
* A web-based installer to easily set-up PANIC
* A dockerized set-up for easy installation and communication between the different components.
Change the contents of this file to this:

# Change Log

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
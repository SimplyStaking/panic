# Change Log

## Unreleased

## 1.3.1

Released on 24th January 2023

 - Added `is_peered_with_sentinel` monitorable for use in nodes that are running `mev-tendermint`
 - Added `node_is_peered_with_sentinel` / `validator_is_peered_with_sentinel` alerts / alerting configs
- Updated CosmosNode `data_store`, `data_transformer`, `monitor`, and `alerter` to accomodate this new monitorable / alert
 - Update API / UI for configuring these alerts

## 1.3.0

Released on 24th October 2022

- Web Installer: Installation procedure merged into PANIC UI.
- Web Installer: Config editing functionality added to PANIC UI.
- Web Installer: Docker service removed.
- Updated PANIC UI to use `@simply-vc/uikit` 1.6.1.
- Removed `@stencil/router` from PANIC UI dependencies.
- API: Added endpoints required to migrate the web installer to PANIC UI
- Updated documentation throughout.
- Updated Polkadot API to 9.6.1.

## 1.2.1
Released on 6th July 2022

- Installer: Fixed blank page bug when adding a Cosmos node.
- Installer: Added functionality for preventing square-brackets in configuration names.

## 1.2.0
Released on 27th June 2022

- Added Substrate Node and Network alerting.
- Added Substrate-API docker service. This is going to be used to get Substrate-related metrics.
- Updated API, UI and Web-Installer to be compatible with Substrate alerting.

## 1.1.1
Released on 17th May 2022

- Updated Chainlink Node Monitor/Alerts to use correct moniker for the balance of node accounts.
- Integrated System Alerter with current factory classes.
- Fixed colored severities in systems-overview page in UI.

## 1.1.0

Released on 28th April 2022

- Added Cosmos Node and Network alerting.
- Updated API, UI and Web-Installer to be compatible with Cosmos alerting.
- Updated alert messages for Chainlink/EVM block height alerts.

## 1.0.0

Released on 30th March 2022

- Added DockerHub repository tags monitoring and alerting.
- Developed a UI dashboard capable of showing problems and alert logs related to the Chainlink/EVM nodes, GitHub/DockerHub repositories and host systems. A System's overview page showing the host system metrics was also developed.
- Replaced Config Store with Monitorable Store within the alerter.
- Integrated Monitorable Store with Monitor Managers.
- Fixed uncaught Telegram connection exceptions.
- Fixed incorrectly raised missing contract observations upon alerter/monitor restart.
- Updated configs manager to ignore weiwatchers configs.
- Fixed alerting logic bug for the `SyncedDataSourcesFound` and `ContractsNowRetrieved` metrics when the node isn't participating in any contract.
- Added alerts for GitHub API call error and resolution.
- Fixed improper RabbitMQ connection handling in ConfigsManager.

## 0.3.4

Released on 16th March 2022

- Updated Chainlink Contracts Monitor/Alerts to use chain names and contract names.

## 0.3.3

Released on 23rd February 2022

- Fixed bug in data transformers for mutable values in previous state.

## 0.3.2

Released on 21st January 2022

- Set `tx_manager_num_gas_bumps_total` and `tx_manager_gas_bump_exceeds_limit_total` as optional metrics, depending on whether they are being exposed by the Prometheus endpoint or not. This fixes the issue with `MetricNotFoundError` alerts being raised repetitively.
- Fixed bug in slack commands when muting multiple severities.
- ChainlinkNodeMonitor is now compatible with multi-chain nodes prometheus data. Note: It is still assumed that each chainlink node is associated to one chain for now.
- Refactored Alert Store together with some error codes, and updated data store with missing chainlink contract alert keys.

## 0.3.1

Released on 6th January 2022

- Fixed bug in web-installer when loading empty configs.
- Fixed bug in web-installer when writing empty configs.
- Fixed bug in alerting logic for `no change in` alerts.
- Fixed bug in alerting for downtime of EVM nodes.

## 0.3.0

Released on 9th December 2021

- Updated the Web-Installer to cater for GETH RPC Monitoring
- Added EVM node store, Chainlink contract store and tests for both.
- Added EVM Node Monitoring along with the monitor tests.
- Added ChainlinkContractsMonitor along with its tests.
- Added ContractMonitorsManager along with its tests.
- Added EVM Node Data Transformer along with its tests.
- Added ChainlinkContractsDataTransformer along with its tests.
- Added EVMNodeAlerterManager and its tests.
- Added the ChainlinkAlertersManager and its tests.
- Added EVMNodeAlerter and its tests.
- Added ChainlinkNodeAlerter and its tests.
- Added ChainlinkContractAlerter and its tests.
- Removed `no_of_active_jobs` as `job_subscriber_subscriptions` is no longer found
- Added QOL improvements: mid-form popup warnings, custom weiwatcher network input, other changes such as descriptions etc.

## 0.2.0 (Part of 0.3.0 tag)

Released on 9th December 2021

- Fixed tests to work with alerter changes. Merged multiple tests into one using parameterization.
- Updated Alerter to fix bugs with regards to metric changes in thresholds.
- Added Internal Alerts on startup originating from the Alerter, which are used to reset all metrics for that chain.
- Added functionality to cater for new Internal Alert in Data Store.
- Added Tests for new Internal Alerts in System/Github Alerter and Alert Store.
- Added the ChainlinkNodeMonitor, ChainlinkNodeDataTransformer, DataTransformersManager chainlink logic, NodeMonitorsManager, and their tests.
- Refactored RabbitMQ queues and routing keys.
- The SystemMonitorsManager additionally now parses systems belonging to chains from the `system_config.ini` if Chainlink is the base chain. Same schema as `GENERAL` is expected.
- Web-Installer visually updated to look better
- Web-Installer Chainlink/DockerHub/Slack have been integrated for the setup process
- Fixed issue with Internal Alerts generation when the Alert Router is not yet up.
- Fixed issue with GitHub alerter raising new release alerts in reverse order for multiple releases.
- The data store components are now compatible with the base Chainlink integration features.
- Added Chainlink Node Alerter Manager and tests.
- Web-Installer bug fixes and removing outdated alerts.
- Added Chainlink Node Alerter logic and tests.
- Integrated Slack as an alerting channel and command handler.
- Added new components heartbeat to Slack.

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

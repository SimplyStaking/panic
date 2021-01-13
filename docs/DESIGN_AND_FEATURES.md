# Design and Features of PANIC

- [**High-Level Design**](#high-level-design)
- [**Alert Types**](#alert-types)
- [**Alerting Channels**](#alerting-channels)
- [**Telegram Commands**](#telegram-commands)
- [**List of Alerts**](#list-of-alerts)

## High-Level Design

The PANIC alerter can alert a node operator on the following sources: 
- The host systems that the Cosmos-SDK/Substrate nodes are running on based on system metrics obtained from the node via [Node Exporter](https://github.com/prometheus/node_exporter)
- Cosmos-SDK/Substrate GitHub repository releases using the [GitHub Releases API](https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#releases). 

Given the above, system monitoring and GitHub repository monitoring were developed as general as possible to give the node operator the option to monitor any system and/or any GitHub repository (Don't have to be Substrate/Cosmos-sdk based nodes/repositories).

The diagram below depicts the different components which constitute PANIC and how they interact with each other and the node operator.

<img src="./images/IMG_PANIC_DESIGN_10X.png" alt="PANIC Design"/>

For both system monitoring/alerting and GitHub repository monitoring/alerting, PANIC starts by loading the configuration (saved during [installation](../README.md)).

For system monitoring and alerting, PANIC operates as follows:
- When the **Monitors** **Manager Process** receives the configurations, it starts as many **System Monitors** as there are systems to be monitored.
- Each **System Monitor** extracts the system data from the node's Node Exporter endpoint and forwards this data to the **System Data Transformer** via **RabbitMQ**.
- The **System Data Transformer** starts by listening for data from the **System Monitors** via **RabbitMQ**. Whenever a system's data is received, the **System Data Transformer** combines the received data with the system's state obtained from **Redis**, and sends the combined data to the **Data Store** and the **System Alerter** via RabbitMQ.
- The **System Alerter** starts by listening for data from the **System Data Transformer** via **RabbitMQ**. Whenever a system's transformed data is received, the **System Alerter** compares the received data with the alert rules set during installation, and raises an alert if any of these rules are triggered. This alert is then sent to the **Alert Router** via **RabbitMQ** .
- The **Data Store** also received data from the **System Data Transformer** via **RabbitMQ** and saves this data to both **Redis** and **MongoDB** as required.
- When the **Alert Router** receives an alert from the **System Alerter** via **RabbitMQ**, it checks the configurations to determine which channels should receive this alert. As a result, this alert is then routed to the appropriate channel and the **Data Store** (so that the alert is stored in a **Mongo** database) via **RabbitMQ**.
- When a **Channel Handler** receives an alert via **RabbitMQ**, it simply forwards it to the channel it handles and the **Node Operator** would be notified via this channel.
- If the user sets-up a **Telegram Channel** with **Commands** enabled, the user would be able to control and query PANIC via Telegram Bot Commands. A list of available commands is given [here](#telegram-commands).

For GitHub repository monitoring and alerting, PANIC operates similarly to the above but the data flows through GitHub repository dedicated processes.

**Notes**: 

- In future releases, the node operator will be able to use PANIC to monitor Substrate and Cosmos-SDK based nodes and get alerts based on blockchain-specific metrics obtained from various data sources.
- Another important component which is not depicted above is the **Health-Checker** component. The **Health-Checker** was not included in the image above as it is not part of the monitoring and alerting process, in fact it runs in its own Docker container. The **Health-Checker** component constitutes of two separate components, the **Ping Publisher** and the **Heartbeat Handler**. The **Ping Publisher** sends ping requests to PANIC's components every 30 seconds via **RabbitMQ**, and the **Heartbeat Handler** listens for heartbeats and saves them to **Redis**. This mechanism makes it possible to deduce whether PANIC's components are running as expected when the node operator enters the `/status` command described [here](#telegram-commands).

## Alert Types

Different events vary in severity. We cannot treat an alert for a new version of the Cosmos-SDK as being on the same level as an alert for 100% Storage usage. PANIC makes use of four alert types:

- **CRITICAL**: Alerts of this type are the most severe. Such alerts are raised to inform the node operator of a situation which requires immediate action. **Example**: System's storage usage reached 100%.
- **WARNING**: A less severe alert type but which still requires attention as it may be a warning of an incoming critical alert. **Example**: System's storage usage reached 85%.
- **INFO**: Alerts of this type have little to zero severity but consists of information which is still important to acknowledge. Info alerts also include positive events. **Example**: System's storage usage is no longer at a critical level.
- **ERROR**: Alerts of this type are triggered by abnormal events and ranges from zero to high severity based on the error that has occurred and how many times it is triggered. **Example**: Cannot access GitHub page alert.

**Note:** The critical and warning values (100% and 85%) mentioned in the examples above are configurable, and these can be configured using the installation procedure mentioned [here](../README.md)

## Alerting Channels

PANIC supports multiple alerting channels. By default, only the console and logging channels are enabled, allowing the node operator to run the alerter without having to set up extra alerting channels. This is not enough for a more serious and longer-term alerting setup, for which the node operator should set up the remaining alerting channels using the installation process described [here](../README.md).

PANIC supports the following alerting channels:

| Channel | Severities Supported | Configurable Severities | Description |
|---|---|---|---|
| `Console` | `INFO`, `CRITICAL`, `WARNING`, `ERROR` | All | Alerts printed to standard output (`stdout`) of the alerter's Docker container. |
| `Log` | `INFO`, `CRITICAL`, `WARNING`, `ERROR` | All | Alerts logged to an alerts log (`alerter/log/alerts.log`). |
| `Telegram` | `INFO`, `CRITICAL`, `WARNING`, `ERROR` | All | Alerts delivered to a Telegram chat via a Telegram bot in the form of a text message. |
| `E-mail` | `INFO`, `CRITICAL`, `WARNING`, `ERROR` | All | Alerts sent as emails using an SMTP server, with option for authentication. |
| `Twilio` | `CRITICAL` | None | Alerts trigger a phone call to grab the node operator's attention. |
| `Opsenie` | `INFO`, `CRITICAL`, `WARNING`, `ERROR` | All | Alerts are sent to the node operator's Opsgenie environment using the following severity mapping: `CRITICAL` → `P1`, `WARNING` → `P3`, `ERROR` → `P3`, `INFO` → `P5`|
| `PagerDuty` | `INFO`, `CRITICAL`, `WARNING`, `ERROR` | All | Alerts are sent to the node operator's PagerDuty environment using the following severity mapping: `CRITICAL` → `critical`, `WARNING` → `warning`, `ERROR` → `error`, `INFO` → `info`|

Using the installation procedure, the user is able to specify the chain a system/GitHub repository belongs to (if the system/GitHub repository is not associated with a chain, it is associated automatically under the GENERAL chain). Due to this, the user is given the capability of associating channels with specific chains, hence obtaining a more organized alerting system. In addition to this, the user can set multiple alerting channels of the same type and enable/disable alert severities on each channel.

For example the node operator may have the following setup:
- A Telegram Channel for Polkadot alerts with only WARNING and CRITICAL alerts enabled.
- A Telegram Channel for Cosmos alerts with all severities enabled.
- A Twilio Channel for all chains added to PANIC.

## Telegram Commands

Telegram bots in PANIC serve two purposes. As mentioned above, they are used to send alerts. However they can also accept commands, allowing the node operator to have some control over the alerter and check its status.

PANIC supports the following commands:

| Command | Parameters | Description |
|---|---|---|
| `/start` | None | A welcome message is returned. |
| `/ping` | None | Pings the Telegram Commands Handler associated with the Telegram Chat and returns `PONG!`. The user can use this command to check that the associated Telegram Commands Handler is running. |
| `/help` | None | Returns a guide of acceptable commands and their description. |
| `/mute` | List of severities, for example: `/mute INFO CRITICAL` | Suppose that the user types `/mute INFO CRITICAL` in a Telegram chat associated with the chain `Polkadot`. The `/mute` command mutes `INFO` and `CRITICAL` alerts on all channels (Including all other channels which are set-up, for example Opsgenie) for the chain `Polkadot`. If no severities are given, all `Polkadot` alerts are muted on all channels. |
| `/unmute` | None | Suppose that the user types `/unmute` in a Telegram chat associated with the chain `Polkadot`. This command will unmute all alert severities on all channels (Including all other channels which are set-up ex. Opsgenie) for the chain `Polkadot`. |
| `/muteall` | List of severities, for example: `/muteall INFO CRITICAL` | Suppose that the user types `/muteall INFO CRITICAL` in a Telegram chat associated with the chain `Polkadot`. The `/muteall` command mutes `INFO` and `CRITICAL` alerts on all channels (Including all other channels which are set-up, for example Opsgenie) for every chain being monitored (including the GENERAL chain). If no severities are given, all alerts for all chains being monitored are muted on all channels. |
| `/unmuteall` | None | Suppose that the user types `/unmuteall` in a Telegram chat associated with the chain `Polkadot`. This command unmutes all alert severities on all channels (Including all other channels which are set-up ex. Opsgenie) for every chain being monitored (including the GENERAL chain). |
| `/status` | None | Returns whether the components that constitute PANIC are running or not. If there are problems, the problems are highlighted in the status message. |

## List of Alerts

A complete list of alerts will now be presented. These are grouped into [System Alerts](#system-alerts) and [GitHub Repository Alerts](#github-repository-alerts) for easier understanding.

Each alert has either severity thresholds associated, or is associated a single severity. A severity threshold is a (`value`, `severity`) pair such that when a metric associated with the alert reaches `value`, an alert with `severity` is raised. For example, the `System CPU Usage Critical` severity threshold can be configured to `95%`, meaning that you will get a `CRITICAL` `SystemCPUUsageIncreasedAboveThresholdAlert` alert if the `CPU Usage` of a system reaches `95%`. On the other hand, if an alert is associated a single severity, that alert will always be raised with the same severity whenever the alert rule is obeyed. For example, when a System is back up again after it was down, a `SystemBackUpAgainAlert` with severity `INFO` is raised. In addition to this, not all alerts have their severities or severity thresholds configurable, also some alerts can be even disabled altogether.

In the lists below we will show which alerts have severity thresholds and which alerts have a single severity associated. In addition to this we will state which alerts are configurable/non-configurable and which can be disabled/enabled.

**Note**: Alerts can be configured and/or enabled/disabled using the installation procedure described [here](../README.md)

## System Alerts

| Alert Class | Severity Thresholds | Severity | Configurable | Enabled/Disabled | Description |
|---|---|---|:-:|:-:|---|
| `SystemWentDownAtAlert` | `WARNING`, `CRITICAL` | | ✓ | ✓ | A `WARNING`/`CRITICAL` alert is raised if `warning_threshold`/`critical_threshold` seconds pass after a system is down respectively. |
| `SystemBackUpAgainAlert` | | `INFO` | ✗ | ✗ | This alert is raised if the the system was down and is back up again. This alert can only be enabled/disabled if the downtime alert is enabled/disabled respectively. |
| `SystemStillDownAlert` | `CRITICAL` | | ✓ | ✓ | This alert is raised periodically every `critical_repeat` seconds if a `SystemWentDownAt` alert has already been raised. |
| `InvalidUrlAlert` | | `ERROR` | ✗ | ✗ | This alert is raised if the System's provided Node Exporter endpoint has an invalid URL schema. |
| `MetricNotFoundErrorAlert` | | `ERROR` | ✗ | ✗ | This alert is raised if a metric that is being monitored cannot be found at the system's Node Exporter endpoint. |
| `OpenFileDescriptorsIncreasedAboveThresholdAlert` | `WARNING`, `CRITICAL` | | ✓ | ✓ | A `WARNING`/`CRITICAL` alert is raised if the percentage number of open file descriptors increases above `warning_threshold`/`critical_threshold` respectively. This alert is raised periodically every `critical_repeat` seconds with `CRITICAL` severity if the percentage number of open file descriptors is still above `critical_threshold`. |
| `OpenFileDescriptorsDecreasedBelowThresholdAlert` | | `INFO` | ✗ | ✗ | This alert is raised if the percentage number of open file descriptors decreases below `warning_threshold`/`critical_threshold`. This alert can only be enabled/disabled if the `OpenFileDescriptorsIncreasedAboveThresholdAlert` is enabled/disabled respectively. |
| `SystemCPUUsageIncreasedAboveThresholdAlert` | `WARNING`, `CRITICAL` | | ✓ | ✓ | A `WARNING`/`CRITICAL` alert is raised if the system's CPU usage percentage increases above `warning_threshold`/`critical_threshold` respectively. This alert is raised periodically every `critical_repeat` seconds with `CRITICAL` severity if the system's CPU usage percentage is still above `critical_threshold`. |
| `SystemCPUUsageDecreasedBelowThresholdAlert` | | `INFO` | ✗ | ✗ | This alert is raised if the system's CPU usage percentage decreases below `warning_threshold`/`critical_threshold`. This alert can only be enabled/disabled if the `SystemCPUUsageIncreasedAboveThresholdAlert` is enabled/disabled respectively. |
| `SystemRAMUsageIncreasedAboveThresholdAlert` | `WARNING`, `CRITICAL` | | ✓ | ✓ | A `WARNING`/`CRITICAL` alert is raised if the system's RAM usage percentage increases above `warning_threshold`/`critical_threshold` respectively. This alert is raised periodically every `critical_repeat` seconds with `CRITICAL` severity if the system's RAM usage percentage is still above `critical_threshold`. |
| `SystemRAMUsageDecreasedBelowThresholdAlert` | | `INFO` | ✗ | ✗ | This alert is raised if the system's RAM usage percentage decreases below `warning_threshold`/`critical_threshold`. This alert can only be enabled/disabled if the `SystemRAMUsageIncreasedAboveThresholdAlert` is enabled/disabled respectively. |
| `SystemStorageUsageIncreasedAboveThresholdAlert` | `WARNING`, `CRITICAL` | | ✓ | ✓ | A `WARNING`/`CRITICAL` alert is raised if the system's storage usage percentage increases above `warning_threshold`/`critical_threshold` respectively. This alert is raised periodically every `critical_repeat` seconds with `CRITICAL` severity if the system's storage usage percentage is still above `critical_threshold`. |
| `SystemStorageUsageDecreasedBelowThresholdAlert` | | `INFO` | ✗ | ✗ | This alert is raised if the system's storage usage percentage decreases below `warning_threshold`/`critical_threshold`. This alert can only be enabled/disabled if the `SystemStorageUsageIncreasedAboveThresholdAlert` is enabled/disabled respectively. |

**Note:** 
- `warning_threshold` and `critical_threshold` represent the `WARNING` and `CRITICAL` configurable thresholds respectively. These are set by the user during installation.
- `critical_repeat` represents the amount of time that needs to pass for a `CRITICAL` alert that has already been raised to be raised again. This can also be set by the user during installation.

## GitHub Repository Alerts

| Alert Class | Severity | Configurable | Enabled/Disabled | Description |
|---|---|:-:|:-:|---|
| `NewGitHubReleaseAlert` | `INFO` | ✗ | ✗ | This alert is raised whenever a new release is published for a GitHub repository. Some release details are also given. Note, this alert cannot be enabled/disabled unless the operator decides to not monitor a repo altogether. |
| `CannotAccessGitHubPageAlert` | `ERROR` | ✗ | ✗ | This alert is raised when the alerter cannot access the GitHub repository's Releases API Page. |

---
[Back to front page](../README.md)
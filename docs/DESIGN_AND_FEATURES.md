# Design and Features of PANIC

- [**High-Level Design**](#high-level-design)
- [**Alert Types**](#alert-types)
- [**Alerting Channels**](#alerting-channels)
- [**Telegram Commands**](#telegram-commands)
- [**List of Alerts**](#list-of-alerts)

## High-Level Design

The PANIC alerter can alert a Cosmos-SDK-based or Substrate-based node operator about the host a Cosmos-SDK/Substrate node is running on based on system metrics obtained from the node via [Node Exporter](https://github.com/prometheus/node_exporter), and new Cosmos-SDK-based or Substrate-based GitHub repository releases using the [GitHub Releases API](https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#releases). Having said that, system monitoring and GitHub repository monitoring where developed as general as possible to give the node operator the option to monitor any system and/or any GitHub repository.

The diagram below depicts the different components which constitute PANIC and how they interact with each other and the node operator.

<img src="./images/IMG_PANIC_DESIGN_10X.png" alt="PANIC Design"/>

For both system monitoring/alerting and GitHub repository monitoring/alerting, PANIC starts by loading the configuration (saved during [installation](../README.md)) into the components that need these configurations. 

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
| `Opsenie` | `INFO`, `CRITICAL`, `WARNING`, `ERROR` | All | Alerts are sent to the node operator's Opsgenie space using the following severity mapping: `CRITICAL` → `P1`, `WARNING` → `P3`, `ERROR` → `P3`, `INFO` → `P5`|
| `PagerDuty` | `INFO`, `CRITICAL`, `WARNING`, `ERROR` | All | Alerts are sent to the node operator's PagerDuty space using the following severity mapping: `CRITICAL` → `critical`, `WARNING` → `warning`, `ERROR` → `error`, `INFO` → `info`|

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
| `/start` | None | A welcome message is returned |
| `/ping` | None | Pings the Telegram Commands Handler associated with the Telegram Chat and returns `PONG!` if it is running. The user can use this command to check that the associated Telegram Commands Handler is running. |
| `/help` | None | Returns a guide of acceptable commands and their description. |
| `/mute` | `Optional( List(<severity>) )` | Mutes List(<severity>) alerts on all channels (Including all other channels which are set-up ex. Opsgenie) for the chains associated with the Telegram Channel. If the list of severities is not given, all alerts for the chains associated with the Telegram Channel are muted on all channels. |
| `/unmute` | None | Unmutes all alert severities on all channels (Including all other channels which are set-up ex. Opsgenie) for chains associated with the Telegram channel. |
| `/mute_all` | `Optional( List(<severity>) )` | Mutes List(<severity>) alerts on all channels (Including all other channels which are set-up ex. Opsgenie) for every chain being monitored (including the GENERAL chain). If the list of severities is not given, all alerts for all chains being monitored are muted on all channels. |
| `/unmute_all` | None | Unmutes all alert severities on all channels (Including all other channels which are set-up ex. Opsgenie) for every chain being monitored (including the GENERAL chain). |
| `/status` | None | Returns whether the components that constitute PANIC are running or not. If there are problems, the problems are highlighted in the status message. |

## List of Alerts

###### TODO: Content

---
[Back to front page](../README.md)
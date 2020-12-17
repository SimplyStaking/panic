# Design and Features of PANIC

- [**High-Level Design**](#high-level-design)
- [**Alerting Channels**](#alerting-channels)
- [**Alert Types**](#alert-types)
- [**Telegram Commands**](#telegram-commands)
- [**List of Alerts**](#list-of-alerts)

## High-Level Design

The PANIC alerter can alert the node operator about the host a node is running on based on system metrics obtained from the node via [Node Exporter](https://github.com/prometheus/node_exporter), and new GitHub repository releases using the [GitHub Releases API](https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#releases). The diagram below depicts the different components which constitute PANIC and how they interact with each other and the node operator.

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

**Note**: In future releases, the node operator will be able to use PANIC to monitor Substrate and Cosmos-SDK based nodes and get alerts based on metrics obtained from various data sources.

###### TODO: Content

## Alerting Channels

###### TODO: Content

## Alert Types

###### TODO: Content

## Telegram Commands

###### TODO: Content

## List of Alerts

###### TODO: Content

---
[Back to front page](../README.md)
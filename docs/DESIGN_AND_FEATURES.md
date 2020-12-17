# Design and Features of PANIC

- [**High-Level Design**](#high-level-design)
- [**Alerting Channels**](#alerting-channels)
- [**Alert Types**](#alert-types)
- [**Telegram Commands**](#telegram-commands)
- [**List of Alerts**](#list-of-alerts)

## High-Level Design

The PANIC alerter can alert the node operator about the host a node is running on based on system metrics obtained from the node via [Node Exporter](https://github.com/prometheus/node_exporter), and new GitHub repository releases using the [GitHub Releases API](https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#releases). The diagram below depicts the different components which constitute PANIC and how they interact with each other and the node operator.

<img src="./images/IMG_PANIC_DESIGN_10X.png" alt="PANIC Design" width="900"/>

**Note**: In future releases, the node operator will be able to use PANIC to monitor Substrate and Cosmos-SDK based nodes and get alerts based on the metrics of these nodes.

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
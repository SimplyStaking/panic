# Exchanges
CONFIG_EXCHANGE = 'config'
RAW_DATA_EXCHANGE = 'raw_data'
STORE_EXCHANGE = 'store'
ALERT_EXCHANGE = 'alert'
HEALTH_CHECK_EXCHANGE = 'health_check'

# Queues that need to be declared in the run_alerter to avoid configs being sent
# while a component has not started yet. Basically these are all config queues.
ALERT_ROUTER_CONFIGS_QUEUE_NAME = 'alert_router_configs_queue'
SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME = \
    'system_alerters_manager_configs_queue'
CHANNELS_MANAGER_CONFIGS_QUEUE_NAME = 'channels_manager_configs_queue'
GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME = \
    'github_monitors_manager_configs_queue'
SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME = \
    'system_monitors_manager_configs_queue'

# Routing keys and queue names
GITHUB_ALERTER_INPUT_QUEUE = 'github_alerter_queue'
GITHUB_ALERTER_INPUT_ROUTING_KEY = 'alerter.github'

GITHUB_MANAGER_INPUT_QUEUE = 'github_alerter_manager_queue'
GITHUB_MANAGER_INPUT_ROUTING_KEY = 'ping'

SYS_ALERTERS_MAN_INPUT_QUEUE = 'system_alerters_manager_ping_queue'
SYS_ALERTERS_MAN_INPUT_ROUTING_KEY = 'ping'
SYS_ALERTERS_MAN_CONF_ROUTING_KEY_CHAIN = 'chains.*.*.alerts_config'
SYS_ALERTERS_MAN_CONF_ROUTING_KEY_GEN = 'general.alerts_config'

DATA_STORE_MAN_INPUT_QUEUE = 'data_stores_manager_queue'
DATA_STORE_MAN_INPUT_ROUTING_KEY = 'ping'

# Sleep periods
RESTART_SLEEPING_PERIOD = 10
RE_INITIALISE_SLEEPING_PERIOD = 10

# Templates
EMAIL_HTML_TEMPLATE = """<style type="text/css">
.email {{font-family: sans-serif}}
.tg  {{border:none; border-spacing:0;border-collapse: collapse;}}
.tg td{{border-style:none;border-width:0px;overflow:hidden; padding:10px 5px;word-break:normal;}}
.tg th{{border-style:none;border-width:0px;overflow:hidden;padding:10px 5px;word-break:normal;text-align:left;background-color:lightgray;}}
@media screen and (max-width: 767px) {{.tg {{width: auto !important;}}.tg col {{width: auto !important;}}.tg-wrap {{overflow-x: auto;-webkit-overflow-scrolling: touch;}} }}</style>
<div class="email">
<h2>PANIC Alert</h2>
<p>An alert was generated with the following details:</p>
<div class="tg-wrap"><table class="tg">
<tbody>
  <tr>
    <th>Alert Code:</th>
    <td>{alert_code}</td>
  </tr>
  <tr>
    <th>Severity:</th>
    <td>{severity}</td>
  </tr>
  <tr>
    <th>Message:</th>
    <td>{message}</td>
  </tr>
  <tr>
    <th>Timestamp:</th>
    <td>{timestamp}</td>
  </tr>
  <tr>
    <th>Parent ID:</th>
    <td>{parent_id}</td>
  </tr>
  <tr>
    <th>Origin ID:</th>
    <td>{origin_id}</td>
  </tr>
</tbody>
</table></div>
</div>"""

EMAIL_TEXT_TEMPLATE = """
PANIC Alert!
======================
An alert was generated with the following details:

Alert Code: {alert_code}
Severity: {severity}
Message: {message}
Timestamp: {timestamp}
Parent ID: {parent_id}
Origin ID: {origin_id}
"""

# Component names/name templates/ids
GITHUB_ALERTER_NAME = 'GitHub Alerter'
SYSTEM_STORE_NAME = 'System Store'
GITHUB_STORE_NAME = 'GitHub Store'
ALERT_STORE_NAME = 'Alert Store'
SYSTEM_DATA_TRANSFORMER_NAME = 'System Data Transformer'
GITHUB_DATA_TRANSFORMER_NAME = 'GitHub Data Transformer'
SYSTEM_MONITORS_MANAGER_NAME = 'System Monitors Manager'
GITHUB_MONITORS_MANAGER_NAME = 'GitHub Monitors Manager'
DATA_TRANSFORMERS_MANAGER_NAME = 'Data Transformers Manager'
SYSTEM_ALERTERS_MANAGER_NAME = 'System Alerters Manager'
GITHUB_ALERTER_MANAGER_NAME = 'GitHub Alerter Manager'
DATA_STORE_MANAGER_NAME = 'Data Store Manager'
ALERT_ROUTER_NAME = 'Alert Router'
CONFIGS_MANAGER_NAME = 'Configs Manager'
CHANNELS_MANAGER_NAME = 'Channels Manager'
HEARTBEAT_HANDLER_NAME = 'Heartbeat Handler'
PING_PUBLISHER_NAME = 'Ping Publisher'
HEALTH_CHECKER_MANAGER_NAME = 'Health Checker Manager'
CONSOLE_CHANNEL_NAME = 'CONSOLE'
CONSOLE_CHANNEL_ID = 'CONSOLE'
LOG_CHANNEL_NAME = 'LOG'
LOG_CHANNEL_ID = 'LOG'
SYSTEM_ALERTER_NAME_TEMPLATE = 'System alerter ({})'
GITHUB_MONITOR_NAME_TEMPLATE = 'GitHub monitor ({})'
SYSTEM_MONITOR_NAME_TEMPLATE = 'System monitor ({})'
TELEGRAM_ALERTS_HANDLER_NAME_TEMPLATE = 'Telegram Alerts Handler ({})'
TELEGRAM_COMMANDS_HANDLER_NAME_TEMPLATE = 'Telegram Commands Handler ({})'
TWILIO_ALERTS_HANDLER_NAME_TEMPLATE = 'Twilio Alerts Handler ({})'
PAGERDUTY_ALERTS_HANDLER_NAME_TEMPLATE = 'PagerDuty Alerts Handler ({})'
EMAIL_ALERTS_HANDLER_NAME_TEMPLATE = 'Email Alerts Handler ({})'
OPSGENIE_ALERTS_HANDLER_NAME_TEMPLATE = 'Opsgenie Alerts Handler ({})'
CONSOLE_ALERTS_HANDLER_NAME_TEMPLATE = 'Console Alerts Handler ({})'
LOG_ALERTS_HANDLER_NAME_TEMPLATE = 'Log Alerts Handler ({})'

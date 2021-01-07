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

# Sleep periods
RESTART_SLEEPING_PERIOD = 10
RE_INITIALIZE_SLEEPING_PERIOD = 10

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

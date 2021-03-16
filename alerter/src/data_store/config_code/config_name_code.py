from src.data_store.config_code.config_code import ConfigCode


class ConfigNameCode(ConfigCode):
    GeneralConfig = 'general'
    ChannelsConfig = 'channels'
    SystemsConfig = 'systems_config'
    AlertsConfig = 'alerts_config'
    ReposConfig = 'repos_config'
    OpsGenieConfig = 'opsgenie_config'
    PagerDutyConfig = 'pagerduty_config'
    TelegramConfig = 'telegram_config'
    EmailConfig = 'email_config'
    TwilioConfig = 'twilio_config'
    NodesConfig = 'nodes_config'

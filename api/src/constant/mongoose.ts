export const enum GenericDocument {
    CONFIG_TYPE_SUB_CHAIN = "6265758cfdb17d641746dce4",
    CONFIG_TYPE_EMAIL_CHANNEL = "626574fffdb17d641746dce0",
    CONFIG_TYPE_OPSGENIE_CHANNEL = "62f0f9822bff1d0ead2d2df7",
    CONFIG_TYPE_PAGERDUTY_CHANNEL = "62f0f9a52bff1d0ead2d2df8",
    CONFIG_TYPE_SLACK_CHANNEL = "62f0f9b52bff1d0ead2d2df9",
    CONFIG_TYPE_TELEGRAM_CHANNEL = "62f0f9c52bff1d0ead2d2dfa",
    CONFIG_TYPE_TWILIO_CHANNEL = "62f0f9d52bff1d0ead2d2dfb"
}

export const enum Collection {
    BASE_CHAIN = 'base_chains',
    CONFIG = 'configs',
    CONFIG_OLD = 'configs_old',
    GENERIC = 'generics'
}

export const enum ModelName {
    TELEGRAM = 'telegram',
    TELEGRAM_OLD = 'telegram_old',
    SLACK = 'slack',
    SLACK_OLD = 'slack_old',
    PAGER_DUTY = 'pager_duty',
    PAGER_DUTY_OLD = 'pager_duty_old',
    OPSGENIE = 'opsgenie',
    OPSGENIE_OLD = 'opsgenie_old',
    EMAIL = 'email',
    EMAIL_OLD = 'email_old',
    TWILIO = 'twilio',
    TWILIO_OLD = 'twilio_old',
    CONFIG = 'config',
    CONFIG_OLD = 'config_old',
    GENERIC = 'generic',
    BASE_CHAIN = 'base_chain',
    SEVERITY_ALERT_SUBCONFIG = 'severity_alert_subconfig',
    TIME_WINDOW_ALERT_SUBCONFIG = 'time_window_alert_subconfig',
    THRESHOLD_ALERT_SUBCONFIG = 'threshold_alert_subconfig'
}

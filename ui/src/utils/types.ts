/**
 * The available service names covered by this component.
 */
import {PingStatus} from "./constants";

export type ServiceNames = (
    'node-exporter' | 'prometheus' | 'cosmos-rest' |'tendermint-rpc' | 'substrate-websocket' |
    'ethereum-rpc'| 'opsgenie' | 'telegram'| 'slack' | 'pagerduty' | 'twilio' | 'email' | 'github' | 'dockerhub'
    );

export type ServiceNamesMultipleSources = 'prometheus' | 'twilio' | 'email';

/**
 * The type to be used in {@link ServiceFullNames}.
 */
export type ServicesFullNameType = {
    [services in ServiceNames]: string;
};

/**
 * The type to be used in {@link Services}.
 */
export type ServicesType = {
    [services in ServiceNames]: {
        'endpoint_url': string;
    };
};

/**
 * The type to be used in the pingProperties prop for base chains.
 */
type BaseChainPingPropertiesType = {
    'url': string,
    'baseChain'?: string
}

/**
 * The type to be used in the pingProperties prop for opsgenie.
 */
type OpsgeniePingPropertiesType = {
    'apiKey': string,
    'eu': boolean
}

/**
 * The type to be used in the pingProperties prop for telegram.
 */
type TelegramPingPropertiesType = {
    'botToken': string,
    'botChatId': string
}

/**
 * The type to be used in the pingProperties prop for slack.
 */
type SlackPingPropertiesType = {
    'botToken': string,
    'botChannelId': string
}

/**
 * The type to be used in the pingProperties prop for pagerduty.
 */
type PagerDutyPingPropertiesType = {
    'integrationKey': string
}

/**
 * The type to be used in the pingProperties prop for twilio.
 */
type TwilioPingPropertiesType = {
    'accountSid': string,
    'authToken': string,
    'twilioPhoneNumber': string,
    'phoneNumberToDial': string
}

/**
 * The type to be used in the pingProperties prop for email.
 */
type EmailPingPropertiesType = {
    'smtp': string,
    'port': number,
    'from': string,
    'to': string,
    'username': string,
    'password': string
}

/**
 * The type to be used in the pingProperties prop for channels.
 */
type ChannelsPingPropertiesType = (
    OpsgeniePingPropertiesType | TelegramPingPropertiesType | SlackPingPropertiesType |
    PagerDutyPingPropertiesType | TwilioPingPropertiesType | EmailPingPropertiesType
    );

type RepositoryPingPropertiesType = {
    'name': string;
}

/**
 * The accepted type for the pingProperties prop in `panic-installer-test-button`.
 */
export type PingPropertiesType = (
    BaseChainPingPropertiesType | ChannelsPingPropertiesType | RepositoryPingPropertiesType
    );

/**
 * The accepted type for the pingProperties prop in `panic-installer-test-button-multiple-sources`.
 */
export type PingPropertiesTypeMultipleSources = (
    BaseChainPingPropertiesType | TwilioPingPropertiesType | EmailPingPropertiesType
    );

/**
 * The type of the object to be returned by ping endpoints.
 */
export type PingResult = {
    'result'?: PingStatus,
    'error'?: string
}

/**
 * An extension of {@link PingResult} which also contains a {@link PingPropertiesTypeMultipleSources} property.
 */
export interface PingResultWithProperties extends PingResult {
    'pingProperties': PingPropertiesTypeMultipleSources
}

/**
 * Defines a specific set of attributes received by the alert forms.
 */
export type AlertKeyAttributes = {
    identifier: string,
    severity?: string,
    field: string,
}
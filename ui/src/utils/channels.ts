import {SlackChannel} from "../../../entities/ts/channels/SlackChannel";
import {TwilioChannel} from "../../../entities/ts/channels/TwilioChannel";
import {TelegramChannel} from "../../../entities/ts/channels/TelegramChannel";
import {PagerDutyChannel} from "../../../entities/ts/channels/PagerDutyChannel";
import {OpsgenieChannel} from "../../../entities/ts/channels/OpsgenieChannel";
import {EmailChannel} from "../../../entities/ts/channels/EmailChannel";
import {Channel} from "../../../entities/ts/channels/AbstractChannel";

export const ChannelsAPI = {
    createChannelRequestBody: createChannelRequestBody
}

/**
 * Returns the channel's unique property data based on its channel type.
 * @param channel The channel object
 * @returns object
 */
function getChannelPropertyData(channel: Channel): object {
    switch (channel.type.value) {
        case "slack":
            channel = channel as SlackChannel;
            return {
                appToken: channel.appToken,
                botToken: channel.botToken,
                botChannelId: channel.botChannelId,
                commands: channel.commands,
                alerts: channel.alerts,
                info: channel.info,
                warning: channel.warning,
                critical: channel.critical,
                error: channel.error,
            };
        case "twilio":
            channel = channel as TwilioChannel;
            return {
                accountSid: channel.accountSid,
                authToken: channel.authToken,
                twilioPhoneNumber: channel.twilioPhoneNumber,
                twilioPhoneNumbersToDial: channel.twilioPhoneNumbersToDial,
                critical: channel.critical,
            };
        case "telegram":
            channel = channel as TelegramChannel;
            return {
                botToken: channel.botToken,
                chatId: channel.chatId,
                commands: channel.commands,
                alerts: channel.alerts,
                info: channel.info,
                warning: channel.warning,
                critical: channel.critical,
                error: channel.error,
            }
        case "pagerduty":
            channel = channel as PagerDutyChannel;
            return {
                integrationKey: channel.integrationKey,
                info: channel.info,
                warning: channel.warning,
                critical: channel.critical,
                error: channel.error,
            }
        case "opsgenie":
            channel = channel as OpsgenieChannel;
            return {
                apiToken: channel.apiToken,
                eu: channel.eu,
                info: channel.info,
                warning: channel.warning,
                critical: channel.critical,
                error: channel.error,
            }
        case "email":
            channel = channel as EmailChannel;
            return {
                smtp: channel.smtp,
                port: channel.port,
                emailFrom: channel.emailFrom,
                emailsTo: channel.emailsTo,
                username: channel.username,
                password: channel.password,
                info: channel.info,
                warning: channel.warning,
                critical: channel.critical,
                error: channel.error,
            }
    }
}

/**
 * Creates a request body object given the channel object, according to the type
 * of channel provided.
 * @param channel The channel object from which the request body object is being
 * created.
 * @param id the channel identifier
 * @returns Channel object request body
 */
function createChannelRequestBody(channel: Channel, id: string): Channel {
    const requestBody = {
        id: id,
        type: {
            id: channel.type.id,
        },
        name: channel.name,
        ...getChannelPropertyData(channel),
    } as Channel;

    if (!requestBody.id) {
        delete requestBody.id;
    }

    return requestBody;
}
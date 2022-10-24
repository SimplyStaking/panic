import {EmailChannel} from "../../../../entities/ts/channels/EmailChannel";
import {SlackChannel} from "../../../../entities/ts/channels/SlackChannel";
import {TelegramChannel} from "../../../../entities/ts/channels/TelegramChannel";
import {TwilioChannel} from "../../../../entities/ts/channels/TwilioChannel";
import {OpsgenieChannel} from "../../../../entities/ts/channels/OpsgenieChannel";
import {PagerDutyChannel} from "../../../../entities/ts/channels/PagerDutyChannel";
import {BaseSerializer} from "../serializer.interface";
import {Channel} from "../../../../entities/ts/channels/AbstractChannel";

/**
 * Converts "raw data" (JSON response) into {@link Channel} object and vice-versa.
 */
export class ChannelSerializer implements BaseSerializer<Channel> {

    unserialize(data: Channel): Channel {
        switch (data.type.value.toLowerCase()) {
            case 'email':
                const emailChannel = new EmailChannel();
                return EmailChannel.fromJSON(data, emailChannel);
            case 'slack':
                const slackChannel = new SlackChannel();
                return SlackChannel.fromJSON(data, slackChannel);
            case 'pagerduty':
                const pagerDutyChannel = new PagerDutyChannel();
                return PagerDutyChannel.fromJSON(data, pagerDutyChannel);
            case 'opsgenie':
                const opsgenieChannel = new OpsgenieChannel();
                return OpsgenieChannel.fromJSON(data, opsgenieChannel);
            case 'telegram':
                const telegramChannel = new TelegramChannel();
                return TelegramChannel.fromJSON(data, telegramChannel);
            case 'twilio':
                const twilioChannel = new TwilioChannel();
                return TwilioChannel.fromJSON(data, twilioChannel);
        }
    }

    serialize(entity: Channel): string {
        return JSON.stringify(entity);
    }

}
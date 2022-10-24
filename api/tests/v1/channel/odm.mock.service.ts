import {ObjectUtil} from "../../../src/util/ObjectUtil";
import {EmailModel} from "../../../src/v1/entity/model/channels/EmailModel";
import {OpsgenieModel} from "../../../src/v1/entity/model/channels/OpsgenieModel";
import {PagerDutyModel} from "../../../src/v1/entity/model/channels/PagerDutyModel";
import {SlackModel} from "../../../src/v1/entity/model/channels/SlackModel";
import {TelegramModel} from "../../../src/v1/entity/model/channels/TelegramModel";
import {TwilioModel} from "../../../src/v1/entity/model/channels/TwilioModel";
import {GenericModel} from "../../../src/v1/entity/model/GenericModel";

const mockingoose = require('mockingoose');

const emailChannelType = {
    "_id": "626573a7fdb17d641746dcdb",
    "created": "2022-04-01T00:00:00Z",
    "modified": null,
    "status": true,
    "name": "Email",
    "value": 'email',
    "description": null
};

export const emailChannel = ObjectUtil.snakeToCamel({
    "_id": "62f21c26378930217aa1e681",
    "created": "2022-05-02T22:02:46.000Z",
    "modified": "2022-05-02T23:02:46.000Z",
    "name": "Test Email Channel",
    "type": emailChannelType,
    "configs": [],
    "info": true,
    "warning": true,
    "critical": true,
    "error": true,
    "smtp": "test.smtp",
    "port": 123,
    "email_from": "test@test.test",
    "emails_to": ["test@test.test", "test2@test2.test2"],
    "username": "test_username",
    "password": "test_password"
});

const opsGenieChannelType = {
    "_id": "626573d6fdb17d641746dcdc",
    "created": "2022-04-01T00:00:00Z",
    "modified": null,
    "status": true,
    "name": "Opsgenie",
    "value": 'opsgenie',
    "description": null
};

export const opsGenieChannel = ObjectUtil.snakeToCamel({
    "_id": "62f21c27378930217aa1e682",
    "created": "2022-05-02T22:02:46.000Z",
    "modified": "2022-05-02T23:02:46.000Z",
    "name": "Test OpsGenie Channel",
    "type": opsGenieChannelType,
    "configs": [],
    "info": true,
    "warning": true,
    "critical": true,
    "error": true,
    "api_token": "test_api_token",
    "eu": true
});

const pagerDutyChannelType = {
    "_id": "626573fefdb17d641746dcdd",
    "created": "2022-04-01T00:00:00Z",
    "modified": null,
    "status": true,
    "name": "PagerDuty",
    "value": 'pagerduty',
    "description": null
};

export const pagerDutyChannel = ObjectUtil.snakeToCamel({
    "_id": "62f21c27378930217aa1e683",
    "created": "2022-05-02T22:02:46.000Z",
    "modified": "2022-05-02T23:02:46.000Z",
    "name": "Test OpsGenie Channel",
    "type": pagerDutyChannelType,
    "configs": [],
    "info": true,
    "warning": true,
    "critical": true,
    "error": true,
    "integration_key": "test_integration_key"
});

const slackChannelType = {
    "_id": "62657450fdb17d641746dcdf",
    "created": "2022-04-01T00:00:00Z",
    "modified": null,
    "status": true,
    "name": "Slack",
    "value": 'slack',
    "description": null
};

export const slackChannel = ObjectUtil.snakeToCamel({
    "_id": "62f21c27378930217aa1e684",
    "created": "2022-05-02T22:02:46.000Z",
    "modified": "2022-05-02T23:02:46.000Z",
    "name": "Test OpsGenie Channel",
    "type": slackChannelType,
    "configs": [],
    "info": true,
    "warning": true,
    "critical": true,
    "error": true,
    "app_token": "test_app_token",
    "bot_token": "test_bot_token",
    "bot_channel_id": "test_bot_channel_id",
    "commands": true,
    "alerts": true
});

const telegramChannelType = {
    "_id": "62656ebafdb17d641746dcda",
    "created": "2022-04-01T00:00:00Z",
    "modified": null,
    "status": true,
    "name": "Telegram",
    "value": 'telegram',
    "description": null
};

export const telegramChannel = ObjectUtil.snakeToCamel({
    "_id": "62f21c27378930217aa1e685",
    "created": "2022-05-02T22:02:46.000Z",
    "modified": "2022-05-02T23:02:46.000Z",
    "name": "Test OpsGenie Channel",
    "type": telegramChannelType,
    "configs": [],
    "info": true,
    "warning": true,
    "critical": true,
    "error": true,
    "bot_token": "test_bot_token",
    "chat_id": "test_chat_id",
    "commands": true,
    "alerts": true
});

const twilioChannelType = {
    "_id": "62657442fdb17d641746dcde",
    "created": "2022-04-01T00:00:00Z",
    "modified": null,
    "status": true,
    "name": "Twilio",
    "value": 'twilio',
    "description": null
};

export const twilioChannel = ObjectUtil.snakeToCamel({
    "_id": "62f21c27378930217aa1e686",
    "created": "2022-05-02T22:02:46.000Z",
    "modified": "2022-05-02T23:02:46.000Z",
    "name": "Test OpsGenie Channel",
    "type": twilioChannelType,
    "configs": [],
    "info": true,
    "critical": true,
    "account_sid": "test_account_sid",
    "auth_token": "test_auth_token",
    "twilio_phone_number": "12345678",
    "twilio_phone_numbers_to_dial": ["12345678", "87654321"]
});

export const channels = [
    emailChannel, opsGenieChannel, pagerDutyChannel,
    slackChannel, telegramChannel, twilioChannel
];

/**
 * Service to mock Channel Document
 */
export class ChannelMockService {
    public static mock(): void {
        //mock findone
        mockingoose(EmailModel).toReturn(emailChannel, 'findOne');
        mockingoose(EmailModel).toReturn(emailChannel);
        mockingoose(EmailModel).toReturn([emailChannel], 'find');

        mockingoose(OpsgenieModel).toReturn(opsGenieChannel, 'findOne');
        mockingoose(OpsgenieModel).toReturn(opsGenieChannel);
        mockingoose(OpsgenieModel).toReturn([opsGenieChannel], 'find');

        mockingoose(PagerDutyModel).toReturn(pagerDutyChannel, 'findOne');
        mockingoose(PagerDutyModel).toReturn(pagerDutyChannel);
        mockingoose(PagerDutyModel).toReturn([pagerDutyChannel], 'find');

        mockingoose(SlackModel).toReturn(slackChannel, 'findOne');
        mockingoose(SlackModel).toReturn(slackChannel);
        mockingoose(SlackModel).toReturn([slackChannel], 'find');

        mockingoose(TelegramModel).toReturn(telegramChannel, 'findOne');
        mockingoose(TelegramModel).toReturn(telegramChannel);
        mockingoose(TelegramModel).toReturn([telegramChannel], 'find');

        mockingoose(TwilioModel).toReturn(twilioChannel, 'findOne');
        mockingoose(TwilioModel).toReturn(twilioChannel);
        mockingoose(TwilioModel).toReturn([twilioChannel], 'find');

        //to mock populate of mongoose
        EmailModel.schema.path('type', emailChannelType);
        OpsgenieModel.schema.path('type', opsGenieChannelType);
        PagerDutyModel.schema.path('type', pagerDutyChannelType);
        SlackModel.schema.path('type', slackChannelType);
        TelegramModel.schema.path('type', telegramChannelType);
        TwilioModel.schema.path('type', twilioChannelType);
    }

    public static mockError(): void {
        mockingoose(EmailModel).toReturn(new Error('erro'), 'findOne');
        mockingoose(EmailModel).toReturn(new Error('erro'), 'find');

        mockingoose(OpsgenieModel).toReturn(new Error('erro'), 'findOne');
        mockingoose(OpsgenieModel).toReturn(new Error('erro'), 'find');

        mockingoose(PagerDutyModel).toReturn(new Error('erro'), 'findOne');
        mockingoose(PagerDutyModel).toReturn(new Error('erro'), 'find');

        mockingoose(SlackModel).toReturn(new Error('erro'), 'findOne');
        mockingoose(SlackModel).toReturn(new Error('erro'), 'find');

        mockingoose(TelegramModel).toReturn(new Error('erro'), 'findOne');
        mockingoose(TelegramModel).toReturn(new Error('erro'), 'find');

        mockingoose(TwilioModel).toReturn(new Error('erro'), 'findOne');
        mockingoose(TwilioModel).toReturn(new Error('erro'), 'find');
    }

    public static findOneNotFound(): void {
        mockingoose(EmailModel).toReturn(null, 'findOne');
        mockingoose(OpsgenieModel).toReturn(null, 'findOne');
        mockingoose(PagerDutyModel).toReturn(null, 'findOne');
        mockingoose(SlackModel).toReturn(null, 'findOne');
        mockingoose(TelegramModel).toReturn(null, 'findOne');
        mockingoose(TwilioModel).toReturn(null, 'findOne');
    }

    public static deleteOneMock(): void {
        mockingoose(EmailModel).toReturn({deletedCount: 1}, 'deleteOne');
        mockingoose(OpsgenieModel).toReturn({deletedCount: 1}, 'deleteOne');
        mockingoose(PagerDutyModel).toReturn({deletedCount: 1}, 'deleteOne');
        mockingoose(SlackModel).toReturn({deletedCount: 1}, 'deleteOne');
        mockingoose(TelegramModel).toReturn({deletedCount: 1}, 'deleteOne');
        mockingoose(TwilioModel).toReturn({deletedCount: 1}, 'deleteOne');
    }

    public static deleteOneError(): void {
        mockingoose(EmailModel).toReturn(new Error('erro'), 'deleteOne');
        mockingoose(OpsgenieModel).toReturn(new Error('erro'), 'deleteOne');
        mockingoose(PagerDutyModel).toReturn(new Error('erro'), 'deleteOne');
        mockingoose(SlackModel).toReturn(new Error('erro'), 'deleteOne');
        mockingoose(TelegramModel).toReturn(new Error('erro'), 'deleteOne');
        mockingoose(TwilioModel).toReturn(new Error('erro'), 'deleteOne');
    }

    public static deleteOneNotFound(): void {
        mockingoose(EmailModel).toReturn({deletedCount: 0}, 'deleteOne');
        mockingoose(OpsgenieModel).toReturn({deletedCount: 0}, 'deleteOne');
        mockingoose(PagerDutyModel).toReturn({deletedCount: 0}, 'deleteOne');
        mockingoose(SlackModel).toReturn({deletedCount: 0}, 'deleteOne');
        mockingoose(TelegramModel).toReturn({deletedCount: 0}, 'deleteOne');
        mockingoose(TwilioModel).toReturn({deletedCount: 0}, 'deleteOne');
    }

    public static save(): void {
        //to avoid change mock reference
        mockingoose(EmailModel).toReturn(JSON.parse(JSON.stringify(emailChannel)), 'save');
        mockingoose(OpsgenieModel).toReturn(JSON.parse(JSON.stringify(opsGenieChannel)), 'save');
        mockingoose(PagerDutyModel).toReturn(JSON.parse(JSON.stringify(pagerDutyChannel)), 'save');
        mockingoose(SlackModel).toReturn(JSON.parse(JSON.stringify(slackChannel)), 'save');
        mockingoose(TelegramModel).toReturn(JSON.parse(JSON.stringify(telegramChannel)), 'save');
        mockingoose(TwilioModel).toReturn(JSON.parse(JSON.stringify(twilioChannel)), 'save');

        mockingoose(GenericModel).toReturn(emailChannelType, 'findOne');
    }

    public static saveError(): void {
        mockingoose(EmailModel).toReturn(new Error(), 'save');
        mockingoose(OpsgenieModel).toReturn(new Error(), 'save');
        mockingoose(PagerDutyModel).toReturn(new Error(), 'save');
        mockingoose(SlackModel).toReturn(new Error(), 'save');
        mockingoose(TelegramModel).toReturn(new Error(), 'save');
        mockingoose(TwilioModel).toReturn(new Error(), 'save');

        mockingoose(GenericModel).toReturn([
            emailChannelType, opsGenieChannelType,
            pagerDutyChannelType, slackChannelType,
            telegramChannelType, twilioChannelType], 'findOne');
    }

    public static updateOneMock(): void {
        mockingoose(EmailModel).toReturn({matchedCount: 1}, 'updateOne');
        mockingoose(EmailModel).toReturn(emailChannel, 'findOne');

        mockingoose(OpsgenieModel).toReturn({matchedCount: 1}, 'updateOne');
        mockingoose(OpsgenieModel).toReturn(emailChannel, 'findOne');
        
        mockingoose(PagerDutyModel).toReturn({matchedCount: 1}, 'updateOne');
        mockingoose(PagerDutyModel).toReturn(emailChannel, 'findOne');

        mockingoose(SlackModel).toReturn({matchedCount: 1}, 'updateOne');
        mockingoose(SlackModel).toReturn(emailChannel, 'findOne');

        mockingoose(TelegramModel).toReturn({matchedCount: 1}, 'updateOne');
        mockingoose(TelegramModel).toReturn(emailChannel, 'findOne');

        mockingoose(TwilioModel).toReturn({matchedCount: 1}, 'updateOne');
        mockingoose(TwilioModel).toReturn(emailChannel, 'findOne');
    }

    public static updateOneNotUpdated(): void {
        mockingoose(EmailModel).toReturn({matchedCount: 0}, 'updateOne');
        mockingoose(OpsgenieModel).toReturn({matchedCount: 0}, 'updateOne');
        mockingoose(PagerDutyModel).toReturn({matchedCount: 0}, 'updateOne');
        mockingoose(SlackModel).toReturn({matchedCount: 0}, 'updateOne');
        mockingoose(TelegramModel).toReturn({matchedCount: 0}, 'updateOne');
        mockingoose(TwilioModel).toReturn({matchedCount: 0}, 'updateOne');
    }
}

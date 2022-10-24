process.env.UI_ACCESS_IP = '0.0.0.0';

import {ConfigMockService} from "../config/odm.mock.service";
import {EmailModel} from "../../../src/v1/entity/model/channels/EmailModel";
import {EmailChannel} from "../../../../entities/ts/channels/EmailChannel";
import {OpsgenieModel} from "../../../src/v1/entity/model/channels/OpsgenieModel";
import {OpsgenieChannel} from "../../../../entities/ts/channels/OpsgenieChannel";
import {PagerDutyModel} from "../../../src/v1/entity/model/channels/PagerDutyModel";
import {PagerDutyChannel} from "../../../../entities/ts/channels/PagerDutyChannel";
import {SlackModel} from "../../../src/v1/entity/model/channels/SlackModel";
import {SlackChannel} from "../../../../entities/ts/channels/SlackChannel";
import {TelegramModel} from "../../../src/v1/entity/model/channels/TelegramModel";
import {TelegramChannel} from "../../../../entities/ts/channels/TelegramChannel";
import {TwilioModel} from "../../../src/v1/entity/model/channels/TwilioModel";
import {TwilioChannel} from "../../../../entities/ts/channels/TwilioChannel";
import request from 'supertest'
import {app} from '../../../src/server';
import {Status} from '../../../src/constant/server';
import {
    ChannelMockService,
    emailChannel,
    opsGenieChannel,
    pagerDutyChannel,
    slackChannel,
    telegramChannel,
    twilioChannel
} from "./odm.mock.service";

const mockingoose = require('mockingoose');

beforeEach(() => {
    mockingoose.resetAll();
});

describe('ODM channel data structure', () => {
    test("should check Email channel", async () => {
        ChannelMockService.mock();

        const id = '62f21c26378930217aa1e681';
        const emailChannel = await EmailModel.findOne<EmailChannel>({id: id}) as EmailChannel;
        expect(emailChannel.id.toString()).toEqual(id);

        expect(typeof emailChannel.info).toEqual('boolean');
        expect(typeof emailChannel.warning).toEqual('boolean');
        expect(typeof emailChannel.critical).toEqual('boolean');
        expect(typeof emailChannel.error).toEqual('boolean');

        expect(typeof emailChannel.name).toEqual('string');
        expect(typeof emailChannel.smtp).toEqual('string');
        expect(typeof emailChannel.port).toEqual('number');
        expect(typeof emailChannel.emailFrom).toEqual('string');
        expect(typeof emailChannel.emailsTo).toEqual('object');
        expect(typeof emailChannel.username).toEqual('string');
        expect(typeof emailChannel.password).toEqual('string');

        expect(typeof emailChannel.configs).toEqual('object');
    });

    test("should check Opsgenie channel", async () => {
        ChannelMockService.mock();

        const id = '62f21c27378930217aa1e682';
        const opsgenieChannel = await OpsgenieModel.findOne<OpsgenieChannel>({id: id}) as OpsgenieChannel;
        expect(opsgenieChannel.id).toEqual(id);

        expect(typeof opsgenieChannel.info).toEqual('boolean');
        expect(typeof opsgenieChannel.warning).toEqual('boolean');
        expect(typeof opsgenieChannel.critical).toEqual('boolean');
        expect(typeof opsgenieChannel.error).toEqual('boolean');

        expect(typeof opsgenieChannel.name).toEqual('string');
        expect(typeof opsgenieChannel.apiToken).toEqual('string');
        expect(typeof opsgenieChannel.eu).toEqual('boolean');

        expect(typeof opsgenieChannel.configs).toEqual('object');
    });

    test("should check PagerDuty channel", async () => {
        ChannelMockService.mock();

        const id = '62f21c27378930217aa1e683';
        const pagerDutyChannel = await PagerDutyModel.findOne<PagerDutyChannel>({id: id}) as PagerDutyChannel;
        expect(pagerDutyChannel.id).toEqual(id);

        expect(typeof pagerDutyChannel.info).toEqual('boolean');
        expect(typeof pagerDutyChannel.warning).toEqual('boolean');
        expect(typeof pagerDutyChannel.critical).toEqual('boolean');
        expect(typeof pagerDutyChannel.error).toEqual('boolean');

        expect(typeof pagerDutyChannel.name).toEqual('string');
        expect(typeof pagerDutyChannel.integrationKey).toEqual('string');

        expect(typeof pagerDutyChannel.configs).toEqual('object');
    });

    test("should check Slack channel", async () => {
        ChannelMockService.mock();

        const id = '62f21c27378930217aa1e684';
        const slackChannel = await SlackModel.findOne<SlackChannel>({id: id}) as SlackChannel;
        expect(slackChannel.id).toEqual(id);

        expect(typeof slackChannel.info).toEqual('boolean');
        expect(typeof slackChannel.warning).toEqual('boolean');
        expect(typeof slackChannel.critical).toEqual('boolean');
        expect(typeof slackChannel.error).toEqual('boolean');

        expect(typeof slackChannel.name).toEqual('string');
        expect(typeof slackChannel.appToken).toEqual('string');
        expect(typeof slackChannel.botToken).toEqual('string');
        expect(typeof slackChannel.botChannelId).toEqual('string');

        expect(typeof slackChannel.configs).toEqual('object');
    });

    test("should check Telegram channel", async () => {
        ChannelMockService.mock();

        const id = '62f21c27378930217aa1e685';
        const telegramChannel = await TelegramModel.findOne<TelegramChannel>({id: id}) as TelegramChannel;
        expect(telegramChannel.id).toEqual(id);

        expect(typeof telegramChannel.info).toEqual('boolean');
        expect(typeof telegramChannel.warning).toEqual('boolean');
        expect(typeof telegramChannel.critical).toEqual('boolean');
        expect(typeof telegramChannel.error).toEqual('boolean');

        expect(typeof telegramChannel.name).toEqual('string');
        expect(typeof telegramChannel.botToken).toEqual('string');
        expect(typeof telegramChannel.chatId).toEqual('string');

        expect(typeof telegramChannel.configs).toEqual('object');
    });

    test("should check Twilio channel", async () => {
        ChannelMockService.mock();

        const id = '62f21c27378930217aa1e686';
        const twilioChannel = await TwilioModel.findOne<TwilioChannel>({id: id}) as TwilioChannel;
        expect(twilioChannel.id).toEqual(id);

        expect(typeof twilioChannel.critical).toEqual('boolean');

        expect(typeof twilioChannel.name).toEqual('string');
        expect(typeof twilioChannel.accountSid).toEqual('string');
        expect(typeof twilioChannel.authToken).toEqual('string');
        expect(typeof twilioChannel.twilioPhoneNumber).toEqual('string');
        expect(typeof twilioChannel.twilioPhoneNumbersToDial).toEqual('object');

        expect(typeof twilioChannel.configs).toEqual('object');
    });
});

describe('channel endpoints family', () => {
    test("should check success when getting channel list", async () => {
        ChannelMockService.mock();

        const endpoint = '/v1/channels';
        const res = await request(app).get(endpoint);

        const channels = res.body.result;

        expect(res.statusCode).toEqual(Status.SUCCESS);
        expect(res.body.status).toEqual(Status.SUCCESS);
        expect(channels.length).toEqual(6);
    });

    test("should check getting channel list and Server Error", async () => {
        ChannelMockService.mockError();

        const endpoint = '/v1/channels';
        const res = await request(app).get(endpoint);

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    test("should check success when getting a single channel using findOne", async () => {
        ChannelMockService.mock();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681';
        const res = await request(app).get(endpoint);

        expect(res.statusCode).toEqual(Status.SUCCESS);
        expect(res.body.status).toEqual(Status.SUCCESS);
    });

    test("should check getting a single channel using findOne and Server Error", async () => {
        ChannelMockService.mockError();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681';
        const res = await request(app).get(endpoint);

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    test("should check getting a single channel using findOne and Not Found", async () => {
        ChannelMockService.findOneNotFound();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681';
        const res = await request(app).get(endpoint);

        expect(res.statusCode).toEqual(Status.NOT_FOUND);
        expect(res.body.status).toEqual(Status.NOT_FOUND);
    });

    test("should check no content when remove channel", async () => {
        ChannelMockService.deleteOneMock();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681';
        const res = await request(app).delete(endpoint);

        expect(res.statusCode).toEqual(Status.NO_CONTENT);
        expect(res.body).toEqual({});
    });

    test("should check remove channel and Server Error", async () => {
        ChannelMockService.deleteOneError();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681';
        const res = await request(app).delete(endpoint);

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    test("should check not found when remove channel", async () => {
        ChannelMockService.deleteOneNotFound();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681';
        const res = await request(app).delete(endpoint);

        expect(res.statusCode).toEqual(Status.NOT_FOUND);
        expect(res.body.status).toEqual(Status.NOT_FOUND);
    });

    it.each([
        ['email', emailChannel], ['opsgenie', opsGenieChannel], ['pager duty', pagerDutyChannel],
        ['slack', slackChannel], ['telegram', telegramChannel], ['twilio', twilioChannel]
    ])("should check success when adding %s channel", async (_, channel) => {
        ChannelMockService.save();

        const newChannel = {...channel, type: {...channel.type, id: channel.type._id}};
        delete newChannel.type._id;

        const endpoint = '/v1/channels';
        const res = await request(app).post(endpoint).send(newChannel);

        expect(res.statusCode).toEqual(Status.SUCCESS);
        expect(res.body.status).toEqual(Status.SUCCESS);
    });

    it.each([
        ['email', emailChannel], ['opsgenie', opsGenieChannel], ['pager duty', pagerDutyChannel],
        ['slack', slackChannel], ['telegram', telegramChannel], ['twilio', twilioChannel]
    ])("should check could_not_save_data error when adding %s channel", async (_, channel) => {
        ChannelMockService.saveError();

        const newChannel = {...channel, type: {...channel.type, id: channel.type._id}};
        delete newChannel.type._id;

        const endpoint = '/v1/channels';
        const res = await request(app).post(endpoint).send(newChannel);

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    it.each([
        ['email', emailChannel], ['opsgenie', opsGenieChannel], ['pager duty', pagerDutyChannel],
        ['slack', slackChannel], ['telegram', telegramChannel], ['twilio', twilioChannel]
    ])("should check success when updating %s channel", async (_, channel) => {
        ChannelMockService.mock();
        ChannelMockService.save();

        const newChannel = {...channel};
        delete newChannel.name;
        const endpoint = '/v1/channels/62675e2d8331c477b85f5b15';
        const res = await request(app).put(endpoint).send(newChannel);

        expect(res.statusCode).toEqual(Status.SUCCESS);
        expect(res.body.status).toEqual(Status.SUCCESS);
    });

    it.each([
        ['email', emailChannel], ['opsgenie', opsGenieChannel], ['pager duty', pagerDutyChannel],
        ['slack', slackChannel], ['telegram', telegramChannel], ['twilio', twilioChannel]
    ])("should check not found when updating %s channel", async (_, channel) => {
        ChannelMockService.save();

        const endpoint = '/v1/channels/62675e2d8331c477b85f5b15';
        const res = await request(app).put(endpoint).send(channel);

        expect(res.statusCode).toEqual(Status.NOT_FOUND);
        expect(res.body.status).toEqual(Status.NOT_FOUND);
    });

    it.each([
        ['email', emailChannel], ['opsgenie', opsGenieChannel], ['pager duty', pagerDutyChannel],
        ['slack', slackChannel], ['telegram', telegramChannel], ['twilio', twilioChannel]
    ])("should check could_not_save_data error when updating %s channel", async (_, channel) => {
        ChannelMockService.mock();
        ChannelMockService.saveError();

        const newChannel = {...channel};
        delete newChannel.name;
        const endpoint = '/v1/channels/62675e2d8331c477b85f5b15';
        const res = await request(app).put(endpoint).send(newChannel);

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    test("should check no content when linking channel and config via POST", async () => {
        ConfigMockService.mock();
        ChannelMockService.updateOneMock();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681/configs/62f21c26378930217aa1e681';
        const res = await request(app).post(endpoint);

        expect(res.statusCode).toEqual(Status.NO_CONTENT);
        expect(res.body).toEqual({});
    });

    test("should check linking channel and config via POST and Server Error", async () => {
        ConfigMockService.mockError();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681/configs/62f21c26378930217aa1e681';
        const res = await request(app).post(endpoint);

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    test("should check channel not found when linking channel and config via POST", async () => {
        ChannelMockService.updateOneNotUpdated();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681/configs/62f21c26378930217aa1e681';
        const res = await request(app).post(endpoint);

        expect(res.statusCode).toEqual(Status.NOT_FOUND);
        expect(res.body.status).toEqual(Status.NOT_FOUND);
    });

    test("should check config not found when linking channel and config via POST", async () => {
        ConfigMockService.notFound();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681/configs/62f21c26378930217aa1e681';
        const res = await request(app).post(endpoint);

        expect(res.statusCode).toEqual(Status.NOT_FOUND);
        expect(res.body.status).toEqual(Status.NOT_FOUND);
    });

    test("should check no content when unlinking channel and config via DELETE", async () => {
        ConfigMockService.mock();
        ChannelMockService.updateOneMock();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681/configs/62f21c26378930217aa1e681';
        const res = await request(app).delete(endpoint);

        expect(res.statusCode).toEqual(Status.NO_CONTENT);
        expect(res.body).toEqual({});
    });

    test("should check unlinking channel and config via DELETE and Server Error", async () => {
        ConfigMockService.mockError();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681/configs/62f21c26378930217aa1e681';
        const res = await request(app).delete(endpoint);

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    test("should check channel not found when unlinking channel and config via DELETE", async () => {
        ChannelMockService.updateOneNotUpdated();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681/configs/62f21c26378930217aa1e681';
        const res = await request(app).delete(endpoint);

        expect(res.statusCode).toEqual(Status.NOT_FOUND);
        expect(res.body.status).toEqual(Status.NOT_FOUND);
    });

    test("should check config not found when unlinking channel and config via DELETE", async () => {
        ConfigMockService.notFound();

        const endpoint = '/v1/channels/62f21c26378930217aa1e681/configs/62f21c26378930217aa1e681';
        const res = await request(app).delete(endpoint);

        expect(res.statusCode).toEqual(Status.NOT_FOUND);
        expect(res.body.status).toEqual(Status.NOT_FOUND);
    });
});

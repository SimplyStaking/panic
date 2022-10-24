import {PanicInstallerChannel} from "../panic-installer-channel";
import {Channel} from "../../../../../../entities/ts/channels/AbstractChannel";

const testChannel1: Channel = {
    id: "62674c51fcf822cb9c653246",
    // @ts-ignore
    created: "2022-05-02T22:02:46.000Z",
    modified: null,
    name: "Test Channel",
    type: {
        "id": "62657450fdb17d641746dcdf",
        "modified": null,
        "status": true,
        "name": "Telegram",
        "value": "telegram",
        "description": null,
        "group": "channel_type",
        // @ts-ignore
        "created": "2022-05-02T22:02:46.000Z"
    },
    configs: [
        {
            id: "a679nz7u4kb8y77rnutwjqjbj",
            // @ts-ignore
            sub_chain_name: "sub chain 1",
            enabled: true
        },
        {
            id: "4227hzwq8y2lsi2kzk2du1bv8",
            // @ts-ignore
            sub_chain_name: "sub chain 2",
            enabled: false
        }
    ],
    bot_token: "BOT_TOKEN",
    chat_id: "BOT_CHAT_ID",
    commands: false,
    alerts: false,
    info: false,
    warning: false,
    critical: false,
    error: false
}

describe('isAnyChannelEnabledForThisConfig()', () => {

    it('should return true if at least one channel is enabled within the config', () => {
        const panicInstallerChannel = new PanicInstallerChannel();
        panicInstallerChannel.channels = [testChannel1];
        panicInstallerChannel.configId = "a679nz7u4kb8y77rnutwjqjbj";
        const isChannelEnabledForThisConfig = panicInstallerChannel.isAnyChannelEnabledForThisConfig();
        expect(isChannelEnabledForThisConfig).toBeTruthy()
    });

    it('should return false if no channel is enabled within the config', () => {
        const panicInstallerChannel = new PanicInstallerChannel();
        panicInstallerChannel.channels = [testChannel1];
        panicInstallerChannel.configId = "some-random-id";
        const isChannelEnabledForThisConfig = panicInstallerChannel.isAnyChannelEnabledForThisConfig();
        expect(isChannelEnabledForThisConfig).toBeFalsy()
    });
});
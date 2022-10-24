import { newSpecPage } from '@stencil/core/testing';
import { PanicSettingsChains } from '../panic-settings-chains';
import {ConfigService} from "../../../services/config/config.service";

const dummyConfigs = [{
    subChain: {name: "test_sub_chain"},
    baseChain: {name: "test_base_chain"},
    channels: [
        {
            "channel_id": 1651233337426,
            "enabled_sub_chains": [
                "test_sub_chain"
            ],
            "channel_data": {
                "channel_type": "telegram",
                "info": "true",
                "warning": "",
                "critical": "true",
                "error": "true",
                "channel_name": "telegram_bot_1",
                "bot_token": "token_123",
                "chat_id": "123",
                "telegram_commands": "true",
                "telegram_alerts": "true"
            }
        },
        {
            "channel_id": 1651233435456,
            "enabled_sub_chains": [],
            "channel_data": {
                "channel_type": "slack",
                "info": "true",
                "warning": "",
                "critical": "",
                "error": "",
                "channel_name": "slack_bot_1",
                "app_token": "app123",
                "bot_token": "123",
                "bot_channel_id": "123123",
                "commands": "",
                "alerts": "true"
            }
        },
    ],
    repos: [],
}]
ConfigService.getInstance().getAll = jest.fn().mockReturnValue(dummyConfigs);

describe('panic-settings-chains', () => {
    it('renders', async () => {
        const page = await newSpecPage({
            components: [PanicSettingsChains],
            html: '<panic-settings-chains></panic-settings-chains>',
        });

        const panicRoot = page.body.querySelector('panic-settings-chains');

        expect(panicRoot).toMatchSnapshot();
    });
});

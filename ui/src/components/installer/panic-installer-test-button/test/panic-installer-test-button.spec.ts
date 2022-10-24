import {PanicInstallerTestButton} from "../panic-installer-test-button";
import {ServiceNames} from "../../../../utils/types";

describe('isChannelService()', () => {
    const panicInstallerTestButton = new PanicInstallerTestButton();

    it.each(['opsgenie', 'telegram', 'slack', 'pagerduty', 'twilio', 'email'])('%s should return true',
        async (channel: ServiceNames) => {
        panicInstallerTestButton.service = channel;
        const isCommon: boolean = panicInstallerTestButton.isChannelService();
        expect(isCommon).toBeTruthy();
    });
})



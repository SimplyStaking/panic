import {PanicSettingsChannels} from "../panic-settings-channels";

describe('isEnableEvent()', () => {
    const panicSettingsChannels = new PanicSettingsChannels();

    it('%s should return true', () => {
        const isEnableEvent: boolean = panicSettingsChannels.isEnableEvent(
          {'testId': 'true'});
        expect(isEnableEvent).toBeTruthy();
    });

    it('%s should return false', () => {
        const isEnableEvent: boolean = panicSettingsChannels.isEnableEvent(
          {'testId': 'false'});
        expect(isEnableEvent).toBeFalsy();
    });
});

describe('getConfigAndChannelId()', () => {
    const panicSettingsChannels = new PanicSettingsChannels();

    it('%s should return config channel id', () => {
        const configAndChannelId: string[] =
          panicSettingsChannels.getConfigAndChannelId(
            {'testConfig testID': 'true'});
        expect(configAndChannelId).toEqual(['testConfig', 'testID']);
    });
})



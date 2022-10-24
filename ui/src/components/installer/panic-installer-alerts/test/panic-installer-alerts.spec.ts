import {PanicInstallerAlerts} from "../panic-installer-alerts";
const thresholdAlert = 'test_identifier1 test_severity test_field';
const thresholdAlertKey = thresholdAlert.split(' ');

const severityAlert = 'test_identifier2 test_field';
const severityAlertKey = severityAlert.split(' ');

describe('getIdentifierFromAlertKey()', () => {
    const panicInstallerAlerts = new PanicInstallerAlerts();

    it('should return \'test_identifier\' as key', () => {
        const identifierFromKey1 = panicInstallerAlerts.getIdentifierFromAlertKey(thresholdAlertKey);
        const identifierFromKey2 = panicInstallerAlerts.getIdentifierFromAlertKey(severityAlertKey);
        expect(identifierFromKey1).toEqual('test_identifier1');
        expect(identifierFromKey2).toEqual('test_identifier2');
    });

});

describe('getSeverityFromThresholdAlertKey()', () => {
    const panicInstallerAlerts = new PanicInstallerAlerts();

    it('should return \'test_severity\' as key', () => {
        const severityFromKey = panicInstallerAlerts.getSeverityFromThresholdAlertKey(thresholdAlertKey);
        expect(severityFromKey).toEqual('test_severity');
    });

});

describe('getFieldFromThresholdAlertKey()', () => {
    const panicInstallerAlerts = new PanicInstallerAlerts();

    it('should return \'test_field\' as key', () => {
        const fieldFromKey = panicInstallerAlerts.getFieldFromThresholdAlertKey(thresholdAlertKey);
        expect(fieldFromKey).toEqual('test_field');
    });

});

describe('getFieldFromSeverityAlertKey()', () => {
    const panicInstallerAlerts = new PanicInstallerAlerts();

    it('should return \'test_field\' as key', () => {
        const fieldFromKey = panicInstallerAlerts.getFieldFromSeverityAlertKey(severityAlertKey);
        expect(fieldFromKey).toEqual('test_field');
    });

});



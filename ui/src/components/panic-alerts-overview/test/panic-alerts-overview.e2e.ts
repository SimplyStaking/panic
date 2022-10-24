import {newSpecPage} from '@stencil/core/testing';
import {
    fetchMock,
    mockAlertsData,
    mockIsFirstInstall,
    mockMonitorablesInfoData
} from '../../../utils/mock';
import {PanicAlertsOverview} from '../panic-alerts-overview';

fetchMock.mockResponses([JSON.stringify(mockIsFirstInstall())]
                        [JSON.stringify(mockMonitorablesInfoData())],
                        [JSON.stringify(mockAlertsData())]);

describe('panic-alerts-overview', () => {
    it('renders', async () => {
        const page = await newSpecPage({
            components: [PanicAlertsOverview],
            html: '<panic-alerts-overview></panic-alerts-overview>',
        });

        const panicAlertsOverview = page.body.querySelector('panic-alerts-overview');
        expect(panicAlertsOverview).toMatchSnapshot();
    });
});

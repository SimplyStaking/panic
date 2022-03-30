import {newSpecPage} from '@stencil/core/testing';
import {
    fetchMock,
    mockAlertsOverviewWithAlerts,
    mockMonitorablesInfoData
} from '../../../utils/mock';
import {PanicDashboardOverview} from '../panic-dashboard-overview';

fetchMock.mockResponses([JSON.stringify(mockMonitorablesInfoData())], [JSON.stringify(mockAlertsOverviewWithAlerts())]);

describe('panic-dashboard-overview', () => {
    it('renders', async () => {
        const page = await newSpecPage({
            components: [PanicDashboardOverview],
            html: '<panic-dashboard-overview></panic-dashboard-overview>',
        });

        const panicDashboardOverview = page.body.querySelector('panic-dashboard-overview');
        expect(panicDashboardOverview).toMatchSnapshot();
    });
});

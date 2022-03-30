import {newSpecPage} from '@stencil/core/testing';
import {PanicSystemsOverview} from '../panic-systems-overview';
import {h} from '@stencil/core';
import {
    fetchMock,
    mockMetricsData,
    mockMonitorablesInfoData
} from '../../../utils/mock';

fetchMock.mockResponses([JSON.stringify(mockMonitorablesInfoData())], [JSON.stringify(mockMetricsData())]);

describe('panic-systems-overview', () => {
    it('renders', async () => {
        const page = await newSpecPage({
            components: [PanicSystemsOverview],
            template: () => (<panic-systems-overview
                                baseChainName={'general'}/>),
        });

        const panicSystemsOverview = page.body.querySelector('panic-systems-overview');
        expect(panicSystemsOverview).toMatchSnapshot();
    });
});

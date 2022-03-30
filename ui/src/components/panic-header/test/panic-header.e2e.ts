import {newSpecPage} from '@stencil/core/testing';
import {fetchMock, mockMonitorablesInfoData} from '../../../utils/mock';
import {PanicHeader} from "../panic-header";

fetchMock.mockResponseOnce(JSON.stringify(mockMonitorablesInfoData()));

describe('panic-header', () => {
    it('renders', async () => {
        const page = await newSpecPage({
            components: [PanicHeader],
            html: '<panic-header></panic-header>',
        });

        const panicHeader = page.body.querySelector('panic-header');

        expect(panicHeader).toMatchSnapshot();
    });
});

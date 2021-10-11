import { newE2EPage } from '@stencil/core/testing';

describe('panic-alerts-overview', () => {
    it('renders', async () => {
        const page = await newE2EPage();
        await page.setContent('<panic-alerts-overview></panic-alerts-overview>');

        const element = await page.find('panic-alerts-overview');
        expect(element).toMatchSnapshot();
    });
});

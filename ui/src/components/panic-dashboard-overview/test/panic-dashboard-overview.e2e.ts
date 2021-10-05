import { newE2EPage } from '@stencil/core/testing';

describe('panic-dashboard-overview', () => {
  it('renders', async () => {
    const page = await newE2EPage();
    await page.setContent('<panic-dashboard-overview></panic-dashboard-overview>');

    const element = await page.find('panic-dashboard-overview');
    expect(element).toMatchSnapshot();
  });
});

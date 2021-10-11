import { newE2EPage } from '@stencil/core/testing';

describe('panic-systems-overview', () => {
  it('renders', async () => {
    const page = await newE2EPage();
    await page.setContent('<panic-systems-overview></panic-systems-overview>');

    const element = await page.find('panic-systems-overview');
    expect(element).toHaveClass('hydrated');
  });
});

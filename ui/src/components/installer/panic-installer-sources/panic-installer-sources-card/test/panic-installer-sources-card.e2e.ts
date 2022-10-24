import { newE2EPage } from '@stencil/core/testing';

describe('panic-installer-sources-card', () => {
  it('renders', async () => {
    const page = await newE2EPage();
    await page.setContent('<panic-installer-sources-card></panic-installer-sources-card>');

    const element = await page.find('panic-installer-sources-card');
    expect(element).toMatchSnapshot();
  });
});

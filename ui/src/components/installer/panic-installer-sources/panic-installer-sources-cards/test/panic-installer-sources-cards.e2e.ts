import { newE2EPage } from '@stencil/core/testing';

describe('panic-installer-sources-cards', () => {
  it('renders', async () => {
    const page = await newE2EPage();
    await page.setContent('<panic-installer-sources-cards></panic-installer-sources-cards>');

    const element = await page.find('panic-installer-sources-cards');
    expect(element).toMatchSnapshot();
  });
});

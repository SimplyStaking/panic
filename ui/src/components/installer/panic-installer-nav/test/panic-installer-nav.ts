import { newE2EPage } from '@stencil/core/testing';

describe('panic-installer-nav', () => {
  it('renders', async () => {
    const page = await newE2EPage();
    await page.setContent('<panic-installer-nav></panic-installer-nav>');

    const element = await page.find('panic-installer-nav');
    expect(element).toMatchSnapshot();
  });
});

import { newE2EPage } from '@stencil/core/testing';

describe('panic-footer', () => {
  it('renders', async () => {
    const page = await newE2EPage();
    await page.setContent('<panic-footer></panic-footer>');

    const element = await page.find('panic-footer');
    expect(element).toMatchSnapshot();
  });
});

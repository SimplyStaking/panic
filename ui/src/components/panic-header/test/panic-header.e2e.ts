import { newE2EPage } from '@stencil/core/testing';

describe('panic-header', () => {
  it('renders', async () => {
    const page = await newE2EPage();
    await page.setContent('<panic-header></panic-header>');

    const element = await page.find('panic-header');
    expect(element).toMatchSnapshot();
  });
});

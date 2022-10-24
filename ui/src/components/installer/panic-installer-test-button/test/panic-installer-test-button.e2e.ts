 import { newE2EPage } from '@stencil/core/testing';

describe('panic-installer-test-button', () => {
  it('renders', async () => {
    const page = await newE2EPage();
    await page.setContent('<panic-installer-setup-test-button></panic-installer-setup-test-button>');

    const element = await page.find('panic-installer-setup-test-button');
    expect(element).toMatchSnapshot();
  });
});

import { newE2EPage } from '@stencil/core/testing';

describe('panic-installer-more-info-modal', () => {
  it('renders', async () => {
    const page = await newE2EPage();
    await page.setContent('<panic-installer-more-info-modal></panic-installer-more-info-modal>');

    const element = await page.find('panic-installer-more-info-modal');
    expect(element).toMatchSnapshot();
  });
});

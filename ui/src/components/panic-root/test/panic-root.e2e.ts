import { newE2EPage } from '@stencil/core/testing';

describe('panic-root', () => {
  it('renders', async () => {
    const page = await newE2EPage();
    await page.setContent('<panic-root></panic-root>');

    const element = await page.find('panic-root');
    expect(element).toHaveClass('hydrated');
  });
});

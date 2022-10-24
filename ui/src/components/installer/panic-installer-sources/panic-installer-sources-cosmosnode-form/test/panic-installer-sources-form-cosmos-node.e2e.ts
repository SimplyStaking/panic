import { newE2EPage } from '@stencil/core/testing';

describe('panic-installer-sources-form-cosmos-node', () => {
  it('renders', async () => {
    const page = await newE2EPage();
    await page.setContent('<panic-installer-sources-form-cosmos-node></panic-installer-sources-form-cosmos-node>');

    const element = await page.find('panic-installer-sources-form-cosmos-node');
    expect(element).not.toBeNull();
  });
});

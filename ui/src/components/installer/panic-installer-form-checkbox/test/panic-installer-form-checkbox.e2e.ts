import { newE2EPage } from '@stencil/core/testing';

describe('panic-installer-form-checkbox', () => {
  it('render the inputs in the correct order', async () => {
    const page = await newE2EPage();
    await page.setContent('<panic-installer-form-checkbox></panic-installer-form-checkbox>');

    const element = await page.find('panic-installer-form-checkbox');
    expect(element).toMatchSnapshot();
  });
});
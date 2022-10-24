import {newSpecPage} from '@stencil/core/testing';
import {
  PanicInstallerSourcesFormSystem
} from "../panic-installer-sources-form-system";

describe('panic-installer-sources-form-system', () => {
  it('renders', async () => {
    const page = await newSpecPage(
        {
          components: [PanicInstallerSourcesFormSystem],
          html: '<panic-installer-sources-form-system></panic-installer-sources-form-system>',
        }
    );

    const element = page.body.querySelector('panic-installer-sources-form-system');
    expect(element).toMatchSnapshot();
  });
});

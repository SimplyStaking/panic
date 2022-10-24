import {newSpecPage} from '@stencil/core/testing';
import {
  PanicInstallerSourcesChainlinkNodeForm
} from "../panic-installer-sources-chainlinknode-form";

describe('panic-installer-sources-chainlinknode-form', () => {
  it('renders', async () => {
    const page = await newSpecPage(
        {
          components: [PanicInstallerSourcesChainlinkNodeForm],
          html: '<panic-installer-sources-chainlinknode-form></panic-installer-sources-chainlinknode-form>',
        }
    );

    const element = page.body.querySelector('panic-installer-sources-chainlinknode-form');
    expect(element).toMatchSnapshot();
  });
});

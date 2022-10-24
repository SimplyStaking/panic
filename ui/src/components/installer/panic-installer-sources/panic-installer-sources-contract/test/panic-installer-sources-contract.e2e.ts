import {newSpecPage} from '@stencil/core/testing';
import {
  PanicInstallerSourcesContract
} from "../panic-installer-sources-contract";
import {
  PanicInstallerSourcesContractForm
} from "../panic-installer-sources-contract-form";
import {
    PanicInstallerSourcesContractWeiWatcher
} from "../panic-installer-sources-contract-wei-watcher";

describe('panic-installer-sources-contract', () => {
  it('renders', async () => {
    const page = await newSpecPage(
        {
          components: [PanicInstallerSourcesContract],
          html: '<panic-installer-sources-contract></panic-installer-sources-contract>',
        }
    );

    const element = page.body.querySelector('panic-installer-sources-contract');
    expect(element).toMatchSnapshot();
  });
});

describe('panic-installer-sources-contract-wei-watcher', () => {
  it('renders', async () => {
    const page = await newSpecPage(
        {
            components: [PanicInstallerSourcesContractWeiWatcher],
            html: '<panic-installer-sources-contract-wei-watcher></panic-installer-sources-contract-wei-watcher>',
        }
    );

    const element = page.body.querySelector('panic-installer-sources-contract-wei-watcher');
    expect(element).toMatchSnapshot();
  });
});

describe('panic-installer-sources-contract-form', () => {
  it('renders', async () => {
    const page = await newSpecPage(
        {
          components: [PanicInstallerSourcesContractForm],
          html: '<panic-installer-sources-contract-form></panic-installer-sources-contract-form>',
        }
    );

    const element = page.body.querySelector('panic-installer-sources-contract-form');
    expect(element).toMatchSnapshot();
  });
});

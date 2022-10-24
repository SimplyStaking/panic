import { newSpecPage } from '@stencil/core/testing';
import { PanicInstallerWelcome } from '../panic-installer-welcome';

describe('panic-installer-welcome', () => {
  it('renders', async () => {
      const page = await newSpecPage({
          components: [PanicInstallerWelcome],
          html: '<panic-installer-welcome></panic-installer-welcome>',
      });

      const panicInstallerWelcome = page.body.querySelector('panic-installer-welcome');
      expect(panicInstallerWelcome).toMatchSnapshot();
  });
});
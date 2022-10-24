import { newSpecPage } from '@stencil/core/testing';
import {PanicInstallerAlertsMessageCell} from "../panic-installer-alerts-message-cell";

describe('panic-installer-alerts-message-cell', () => {
  it('renders', async () => {
    const page = await newSpecPage({
      components: [PanicInstallerAlertsMessageCell],
      html: '<panic-installer-alerts-message-cell label="test" message="test">' +
        '</panic-installer-alerts-message-cell>',
    });

    const panicInstallerAlertsMessageCell = page.body.querySelector('panic-installer-alerts-message-cell');
    expect(panicInstallerAlertsMessageCell).toMatchSnapshot();
  });
});
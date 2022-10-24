import { newSpecPage } from '@stencil/core/testing';
import {PanicInstallerAlertsAlertCell} from "../panic-installer-alerts-alert-cell";

describe('panic-installer-alerts-alert-cell', () => {
  it('renders', async () => {
    const page = await newSpecPage({
      components: [PanicInstallerAlertsAlertCell],
      html: '<panic-installer-alerts-alert-cell alertIdentifier="test" severity="Warning" severityEnabled="true" primaryInputLabel="test" primaryInputValue="100"></panic-installer-alerts-alert-cell>',
    });

    const panicInstallerAlertsAlertCell = page.body.querySelector('panic-installer-alerts-alert-cell');
    expect(panicInstallerAlertsAlertCell).toMatchSnapshot();
  });
});
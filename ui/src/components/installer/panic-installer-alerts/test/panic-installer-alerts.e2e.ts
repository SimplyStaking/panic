import { newSpecPage } from '@stencil/core/testing';
import {PanicInstallerAlerts} from "../panic-installer-alerts";
import {ConfigService} from "../../../../services/config/config.service";
import {mockGetConfigData} from "../../../../utils/mock";

beforeAll(() => {
  jest.spyOn(ConfigService.prototype, 'getByID').mockImplementation(
    (_: string) => mockGetConfigData()
  );
});

afterAll(() => {
  jest.restoreAllMocks();
});

describe('panic-installer-alerts', () => {
  it('renders', async () => {
    const page = await newSpecPage({
      components: [PanicInstallerAlerts],
      html:
        '<panic-installer-alerts baseChain="cosmos"></panic-installer-alerts>',
    });

    const selector = page.body.querySelector('panic-installer-alerts');

    expect(selector).toMatchSnapshot();
  });
});

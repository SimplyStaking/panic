import { newSpecPage } from '@stencil/core/testing';
import { PanicInstallerSubChain } from '../panic-installer-sub-chain';
import {ConfigService} from "../../../../services/config/config.service";
import {mockGetAllConfigs} from "../../../../utils/mock";

beforeAll(() => {
  jest.spyOn(ConfigService.prototype, 'getAll').mockImplementation(
    (_: string) => mockGetAllConfigs()
  );
});

afterAll(() => {
  jest.restoreAllMocks();
});

describe('panic-installer-sub-chain', () => {
  it('renders', async () => {
      const page = await newSpecPage({
          components: [PanicInstallerSubChain],
          html: '<panic-installer-sub-chain></panic-installer-sub-chain>',
      });

      const panicInstallerSubChain = page.body.querySelector('panic-installer-sub-chain');
      expect(panicInstallerSubChain).toMatchSnapshot();
  });
});
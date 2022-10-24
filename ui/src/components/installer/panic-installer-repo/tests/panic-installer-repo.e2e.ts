import {newSpecPage} from "@stencil/core/testing";
import {PanicInstallerRepo} from "../panic-installer-repo";
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

describe('panic-installer-repo', () => {
  it('renders', async () => {
    const page = await newSpecPage({
      components: [PanicInstallerRepo],
      html: '<panic-installer-repo></panic-installer-repo>',
    });

    const PanicInstallerRepos = page.body.querySelector('panic-installer-repo');

    expect(PanicInstallerRepos).toMatchSnapshot();
  });
})
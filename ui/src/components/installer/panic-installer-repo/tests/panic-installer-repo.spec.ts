import {PanicInstallerRepo} from "../panic-installer-repo";
import {RepositorySubconfig} from "../../../../../../entities/ts/RepositorySubconfig";
import {Config} from "../../../../../../entities/ts/Config";

const repository1 = {
    id: 'test_repo1',
    name: 'test_name1',
    namespace: 'test_namespace1',
    monitor: false,
    type: {
        id: 'test1',
    },
} as RepositorySubconfig;

const repository2 = {
    id: 'test_repo2',
    name: 'test_name2',
    namespace: 'test_namespace2',
    monitor: false,
    type: {
        id: 'test2',
    },
} as RepositorySubconfig;

const config = {
    id: 'test_config_id',
    repositories: [repository1, repository2],
} as Config;

describe('getRepositoryById()', () => {
    const panicInstallerRepo = new PanicInstallerRepo();
    panicInstallerRepo.config = config;

    it('should return the correct RepositorySubconfig matching the id', () => {
        const repository: RepositorySubconfig = panicInstallerRepo.getRepositoryById(repository1.id);
        expect(repository).toEqual(repository1);
    });

    it('should return the correct RepositorySubconfig matching the id', () => {
        const repository: RepositorySubconfig = panicInstallerRepo.getRepositoryById(repository2.id);
        expect(repository).toEqual(repository2);
    });

});

describe('deleteRepositoryFromConfig()', () => {
    const panicInstallerRepo = new PanicInstallerRepo();
    panicInstallerRepo.config = config;

    it('should delete the RepositorySubconfig matching the id', () => {
        const newRepositoryList: RepositorySubconfig[] = panicInstallerRepo.deleteRepositoryFromConfig(
          repository1.id);
        const expectedRepositoryList: RepositorySubconfig[] = [repository2];
        expect(newRepositoryList).toEqual(expectedRepositoryList);
    });

    it('should delete the RepositorySubconfig matching the id', () => {
        const newRepositoryList: RepositorySubconfig[] = panicInstallerRepo.deleteRepositoryFromConfig(
          repository2.id);
        const expectedRepositoryList: RepositorySubconfig[] = [repository1];
        expect(newRepositoryList).toEqual(expectedRepositoryList);
    });

});

describe('createRepoRequestBody()', () => {
    const panicInstallerRepo = new PanicInstallerRepo();
    panicInstallerRepo.config = config;

    it('should create the correct request body', () => {
        const requestBody: object = panicInstallerRepo.createRepoRequestBody();
        const expectedRequestBody: object = {
            id: config.id,
            repositories: [
                {
                    id: repository1.id,
                    name: repository1.name,
                    namespace: repository1.namespace,
                    type: repository1.type.id,
                    monitor: repository1.monitor,
                },
                {
                    id: repository2.id,
                    name: repository2.name,
                    namespace: repository2.namespace,
                    type: repository2.type.id,
                    monitor: repository2.monitor,
                },
            ]
        }

        expect(requestBody).toEqual(expectedRequestBody);
    });

});


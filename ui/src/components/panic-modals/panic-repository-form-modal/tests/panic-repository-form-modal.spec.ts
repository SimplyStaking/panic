import {PanicRepoFormModal} from "../panic-repo-form-modal";
import {RepositoryType} from "../../../../../../entities/ts/RepositoryType";

const testRepositoryType1 = {
    id: 'test_id_1',
    value: 'github',
    name: 'GitHub',
} as RepositoryType;

const testRepositoryType2 = {
    id: 'test_id1',
    value: 'dockerhub',
    name: 'Dockerhub',
} as RepositoryType;

const testRepositoryTypes: RepositoryType[] = [testRepositoryType1, testRepositoryType2];

describe('getDockerhubNamespaceAndName()', () => {
    const panicRepoFormModal = new PanicRepoFormModal();

    it('splits the dockerhub name (without /) by namespace (library) and name', () => {
        let nameAndNamespace: Array<string> = panicRepoFormModal.getDockerhubNamespaceAndName('test1');
        expect(nameAndNamespace).toEqual(['library', 'test1']);
    });

    it('splits the dockerhub name (with /) by namespace and name', () => {
        let nameAndNamespace: Array<string> = panicRepoFormModal.getDockerhubNamespaceAndName('test1/test2');
        expect(nameAndNamespace).toEqual(['test1', 'test2']);
    });

});

describe('getRepositoryTypeById()', () => {
    const panicRepoFormModal = new PanicRepoFormModal();
    panicRepoFormModal.repositoryTypes = testRepositoryTypes;

    it('should return the correct RepositorySubconfig matching the id', () => {
        const repository: RepositoryType = panicRepoFormModal.getRepositoryTypeById(testRepositoryType1.id);
        expect(repository).toEqual(testRepositoryType1);
    });

});
import { PanicInstallerSources } from '../panic-installer-sources'

describe('findSourceByID()', () => {
    const panicInstallerSources = new PanicInstallerSources();
    const sources: any[] = [
        {
            id: 1,
            name: 'cosmos_node_1'
        },
        {
            id: 2,
            name: 'cosmos_node_2'
        },
        {
            id: 3,
            name: 'cosmos_node_3'
        }
    ];

    it('should return the object equivalent to ID 1', () => {
        const source: any = panicInstallerSources.findSourceByID(sources, 1);
        expect(source).toEqual(expect.objectContaining({ id: 1, name: 'cosmos_node_1' }));
    });

    it('should return the object equivalent to ID 2', () => {
        const source: any = panicInstallerSources.findSourceByID(sources, 2);
        expect(source).toEqual(expect.objectContaining({ id: 2, name: 'cosmos_node_2' }));
    });

    it('should return the object equivalent to ID 3', () => {
        const source: any = panicInstallerSources.findSourceByID(sources, 3);
        expect(source).toEqual(expect.objectContaining({ id: 3, name: 'cosmos_node_3' }));
    });

    it('should return undefined for an ID thats not present in the sources', () => {
        const source: any = panicInstallerSources.findSourceByID(sources, 4);
        expect(source).toBeUndefined();
    });

});

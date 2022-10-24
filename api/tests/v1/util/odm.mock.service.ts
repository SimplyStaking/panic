export interface SimpleObject {
    id?: string,
    value1?: any,
    value2?: any,
    value3?: any,
    value4?: any,
    value5?: any,
    value6?: any
}

export interface ComplexObject {
    simpleObject: SimpleObject,
    scalarList: Array<number>,
    mixedScalarList: Array<number | null | undefined | string | boolean>,
    simpleList: Array<SimpleObject>,
    customList: Array<SimpleObject>
}

export interface FullData {
    id?: string,
    name?: string,
    simpleObject?: SimpleObject,
    complexObject?: ComplexObject
}

export const simpleObject: SimpleObject = {
    id: "1",
    value1: 1,
    value2: true,
    value3: undefined,
    value4: null,
    value5: false,
    value6: "value6 is cool!"
};

export const simpleList: Array<SimpleObject> = [
    simpleObject, { ...simpleObject, id: '2' }, { ...simpleObject, id: '3' }
];

export const fullData: FullData = {
    id: '123456',
    name: 'fulldata',
    simpleObject: simpleObject,
    complexObject: {
        simpleObject: simpleObject,
        scalarList: [1, 3, 4, 5],
        mixedScalarList: [1, 3, 4, null, undefined, 'hi', false, true],
        simpleList: simpleList,
        customList: simpleList
    }
}
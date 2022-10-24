import { ObjectID } from "mongodb";
import { MongooseUtil } from "../../../src/util/MongooseUtil";
import { FullData, fullData, simpleObject } from "./odm.mock.service";

describe('Test MongooseUtil Class', () => {
    test("Should check merge function", async () => {

        const oldData = JSON.parse(JSON.stringify(fullData));

        const id = new ObjectID();

        const newData: FullData = {
            id: id.toString(),
            name: 'new name',
            simpleObject: {
                value6: true
            },
            complexObject: {
                simpleObject: {
                    value4: 8
                },
                scalarList: [1, 4, 6, 9, 10],
                mixedScalarList: [1, false, 1],
                simpleList: [{
                    id: "1",
                    value4: 5
                }, {
                    value4: 6
                }],
                customList: []
            }
        };

        const result: FullData = MongooseUtil.merge(oldData, newData);


        const simpleItem1 = {
            ...simpleObject,
            value4: 5
        };

        delete simpleItem1.id;

        const expectedResult = {
            ...oldData,
            _id: id.toString(),
            name: 'new name',
            simpleObject: {
                ...simpleObject,
                value6: true
            },
            complexObject: {
                ...oldData.complexObject,
                simpleObject: { ...simpleObject, value4: 8 },
                scalarList: [1, 4, 6, 9, 10],
                mixedScalarList: [1, false, 1],
                simpleList: [simpleItem1, { value4: 6 }],
                customList: []
            }
        }

        expect(result.id).toEqual(expectedResult.id);
        expect(result.name).toEqual(expectedResult.name);
        expect(result.simpleObject).toEqual(expectedResult.simpleObject);

        expect(result.complexObject.simpleObject).toEqual(
            expectedResult.complexObject.simpleObject
        );
        expect(result.complexObject.scalarList).toEqual(
            expectedResult.complexObject.scalarList
        );
        expect(result.complexObject.mixedScalarList).toEqual(
            expectedResult.complexObject.mixedScalarList
        );
        
        expectedResult.complexObject.simpleList[0]._id = result.complexObject.simpleList[0]['_id'];
        expect(result.complexObject.simpleList).toEqual(
            expectedResult.complexObject.simpleList
        );

        expect(JSON.stringify(result)).toEqual(JSON.stringify(expectedResult));

    });
});
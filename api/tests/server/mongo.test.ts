import {MongoClientNotInitialised} from "../../src/server/errors";
import {MongoInterface} from "../../src/server/mongo";

describe('MongoInterface', () => {
    const mongoInterface: MongoInterface = new MongoInterface({});
    it('client should return undefined if client is not initialised',
        () => {
            const ret = mongoInterface.client;
            expect(ret).toBeUndefined();
        })

    it('disconnect should throw error if client is not initialised',
        async () => {
            await expect(
                async () => {
                    await mongoInterface.disconnect();
                }
            ).rejects.toThrow(MongoClientNotInitialised);
        })
});

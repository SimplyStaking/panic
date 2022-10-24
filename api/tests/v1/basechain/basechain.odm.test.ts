process.env.UI_ACCESS_IP = '0.0.0.0';

import {BaseChainMockService} from "./odm.mock.service";
import {BaseChain} from "../../../../entities/ts/BaseChain";
import request from 'supertest'
import {app} from '../../../src/server';
import {Status} from '../../../src/constant/server';
import {BaseChainModel} from "../../../src/v1/entity/model/BaseChainModel";

const mockingoose = require('mockingoose');

beforeEach(() => {
    mockingoose.resetAll();
});

describe('ODM basechain data structure', () => {
    test("should check Base Chain", async () => {
        BaseChainMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const baseChain = await BaseChainModel.findOne<BaseChain>({_id: id}) as BaseChain;
        expect(baseChain.id.toString()).toEqual(id);

        expect(typeof baseChain.status).toEqual('boolean');

        expect(typeof baseChain.name).toEqual('string');
        expect(typeof baseChain.value).toEqual('string');

        expect(typeof baseChain.sources).toEqual('object');
        expect(typeof baseChain['severity_alerts']).toEqual('object');
        expect(typeof baseChain['threshold_alerts']).toEqual('object');
        expect(typeof baseChain['time_window_alerts']).toEqual('object');

        expect(baseChain.sources.length).toEqual(1);
        expect(baseChain['severity_alerts'].length).toEqual(1);
        expect(baseChain['threshold_alerts'].length).toEqual(1);
        expect(baseChain['time_window_alerts'].length).toEqual(1);
    });
});

describe('base chain endpoints family', () => {
    test("should check getting base chain list", async () => {
        BaseChainMockService.mock();

        const endpoint = '/v1/basechains';
        const res = await request(app).get(endpoint);

        const channels = res.body.result;

        expect(res.statusCode).toEqual(Status.SUCCESS);
        expect(res.body.status).toEqual(Status.SUCCESS);
        expect(channels.length).toEqual(1);
    });

    test("should check getting base chain list and Server Error", async () => {
        BaseChainMockService.mockError();

        const endpoint = '/v1/basechains';
        const res = await request(app).get(endpoint);

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    test("should check success when getting a single base chain using findOne", async () => {
        BaseChainMockService.mock();

        const endpoint = '/v1/basechains/62675e2d8891cd77b87f5b16';
        const res = await request(app).get(endpoint);

        expect(res.statusCode).toEqual(Status.SUCCESS);
        expect(res.body.status).toEqual(Status.SUCCESS);
    });

    test("should check getting a single channel using findOne and Server Error", async () => {
        BaseChainMockService.mockError();

        const endpoint = '/v1/basechains/62675e2d8891cd77b87f5b16';
        const res = await request(app).get(endpoint);

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    test("should check getting a single base chain using findOne and Not Found", async () => {
        BaseChainMockService.findOneNotFound();

        const endpoint = '/v1/basechains/62675e2d8891cd77b87f5b16';
        const res = await request(app).get(endpoint);

        expect(res.statusCode).toEqual(Status.NOT_FOUND);
        expect(res.body.status).toEqual(Status.NOT_FOUND);
    });
});

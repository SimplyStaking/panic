process.env.UI_ACCESS_IP = '0.0.0.0';

import {Status} from '../../../src/constant/server';
import {app, mongoInterval, redisInterval, server} from '../../../src/server';
import request from 'supertest';
import {ConfigMockService} from './odm.mock.service';

// Used to stop redis and mongo interval processes after all tests finish
afterAll(() => {
    mongoInterval.unref();
    redisInterval.unref();

    server.close();
});

describe('Mongo Installation Checker GET Route', () => {
    const endpoint = '/v1/installation/is-first';

    it("Check if it's the first installation of PANIC.", async () => {
        ConfigMockService.count(0);

        const res = await request(app).get(endpoint);
        expect(res.statusCode).toEqual(Status.SUCCESS);
        expect(res.body.status).toEqual(Status.SUCCESS);
        expect(res.body.result).toEqual(true);
    });

    it("Check if it's an old installation of PANIC.", async () => {
        ConfigMockService.count(1);

        const res = await request(app).get(endpoint);
        expect(res.statusCode).toEqual(Status.SUCCESS);
        expect(res.body.status).toEqual(Status.SUCCESS);
        expect(res.body.result).toEqual(false);
    });
});

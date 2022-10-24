process.env.UI_ACCESS_IP = '0.0.0.0';

import {app, mongoInterval, redisInterval, server} from '../../../src/server';
import request from 'supertest'
import {TestUtil} from '../util/TestUtil';
import {Status} from '../../../src/constant/server';
import {GenericErrorMockService, GenericMockService} from '../config/odm.mock.service';
import {ResponseError} from '../../../src/v1/entity/io/ResponseData';
import {CouldNotRetrieveDataFromDB} from '../../../src/constant/server.feedback';

// Used to stop redis and mongo interval processes after all tests finish
afterAll(() => {
    mongoInterval.unref();
    redisInterval.unref();

    server.close();
});

describe('Generic Domain Endpoints', () => {
    test("Should return a Channel Type list when consumes /v1/channel-types endpoint", async () => {
        GenericMockService.mockChannelType();

        const endpoint = '/v1/channel-types';
        const res = await request(app).get(endpoint);

        const channels = res.body.result;
        expect(res.statusCode).toEqual(Status.SUCCESS);
        expect(res.body.status).toEqual(Status.SUCCESS);

        expect(channels.length).toEqual(1);
        TestUtil.channel(channels[0]);
    });

    test("Should return a Threshold Alert list when consumes /v1/threshold-alerts endpoint",
        async () => {
            GenericMockService.mockThresholdAlert();

            const endpoint = '/v1/threshold-alerts';
            const res = await request(app).get(endpoint);

            const thresholds = res.body.result;
            expect(Status.SUCCESS).toEqual(res.statusCode);
            expect(res.body.status).toEqual(Status.SUCCESS);

            expect(thresholds.length).toEqual(1);
        });

    test("Should return a Severity Alert list when consumes /v1/severity-alerts endpoint",
        async () => {
            GenericMockService.mockSeverityAlert();

            const endpoint = '/v1/severity-alerts';
            const res = await request(app).get(endpoint);

            const severities = res.body.result;
            expect(Status.SUCCESS).toEqual(res.statusCode);
            expect(res.body.status).toEqual(Status.SUCCESS);

            expect(severities.length).toEqual(1);
        });

    test("Should return a Time Window Alert list when consumes /v1/time-window-alerts endpoint",
        async () => {
            GenericMockService.mockTimeWindowAlert();

            const endpoint = '/v1/time-window-alerts';
            const res = await request(app).get(endpoint);

            const thresholds = res.body.result;
            expect(Status.SUCCESS).toEqual(res.statusCode);
            expect(res.body.status).toEqual(Status.SUCCESS);

            expect(thresholds.length).toEqual(1);
        });

    test("Should return a Severity Type list when consumes /v1/severity-types endpoint",
        async () => {
            GenericMockService.mockSeverityType();

            const endpoint = '/v1/severity-types';
            const res = await request(app).get(endpoint);

            const severities = res.body.result;
            expect(Status.SUCCESS).toEqual(res.statusCode);
            expect(res.body.status).toEqual(Status.SUCCESS);

            expect(severities.length).toEqual(1);
            TestUtil.severityType(severities[0]);
        });

    test("Should return a Repository Type list when consumes /v1/repository-types endpoint",
        async () => {
            GenericMockService.mockRepositoryType();

            const endpoint = '/v1/repository-types';
            const res = await request(app).get(endpoint);

            const repositories = res.body.result;
            expect(Status.SUCCESS).toEqual(res.statusCode);
            expect(res.body.status).toEqual(Status.SUCCESS);

            expect(repositories.length).toEqual(1);
            TestUtil.repository(repositories[0]);
        });

    test("Should return a Source Type list when consumes /v1/source-types endpoint",
        async () => {
            GenericMockService.mockSourceType();

            const endpoint = '/v1/source-types';
            const res = await request(app).get(endpoint);

            const type = res.body.result;
            expect(Status.SUCCESS).toEqual(res.statusCode);
            expect(res.body.status).toEqual(Status.SUCCESS);

            expect(type.length).toEqual(1);
            TestUtil.source(type[0]);
        });

    test("Should return a Config Type list when consumes /v1/config-types endpoint",
        async () => {
            GenericMockService.mockConfigType();

            const endpoint = '/v1/config-types';
            const res = await request(app).get(endpoint);

            const type = res.body.result;
            expect(Status.SUCCESS).toEqual(res.statusCode);
            expect(res.body.status).toEqual(Status.SUCCESS);

            expect(type.length).toEqual(1);
            TestUtil.config(type[0]);
        });
});

describe('Common errors On Generic Endpoints', () => {
    test.each([
        ['Channel Type endpoint', '/v1/channel-types'],
        ['Config Type endpoint', '/v1/config-types'],
        ['Repository Type endpoint', '/v1/repository-types'],
        ['Severity Type endpoint', '/v1/severity-types'],
        ['Source Type endpoint', '/v1/source-types'],
        ['Severity Alert endpoint', '/v1/severity-alerts'],
        ['Threshold Alert endpoint', '/v1/threshold-alerts'],
    ])("Should return CouldNotRetrieveDataFromDB Error and status 536",
        async (_: string, endpoint: string) => {
            GenericErrorMockService.mockFind();
            const res = await request(app).get(endpoint);
            const result: ResponseError = res.body;
            expect(res.statusCode).toEqual(Status.E_536);
            expect(result.status).toEqual(Status.E_536);

            const messages = result.messages;
            expect(messages.length).toEqual(1);

            const error = new CouldNotRetrieveDataFromDB();
            expect(messages[0].type).toEqual(error.type);
            expect(messages[0].name).toEqual(error.name);
            expect(messages[0].description).toEqual(error.description);
        });
})

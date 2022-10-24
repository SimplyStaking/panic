process.env.UI_ACCESS_IP = '0.0.0.0';

import {ConfigModel} from "../../../src/v1/entity/model/ConfigModel";
import request from 'supertest'

import {Config} from "../../../../entities/ts/Config";
import {TestUtil} from "../util/TestUtil";
import {config, ConfigMockService} from "./odm.mock.service";
import {app} from '../../../src/server';
import {Status} from '../../../src/constant/server';
import {ObjectID} from 'mongodb';
import { ObjectUtil } from "../../../src/util/ObjectUtil";

const mockingoose = require('mockingoose');

beforeEach(() => {
    mockingoose.resetAll();
});

describe('ODM Config data structure', () => {
    test("should check Config", async () => {
        ConfigMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const config = await ConfigModel.findOne<Config>({_id: id}) as Config;
        expect(config.id.toString()).toEqual(id);
        expect(typeof config.status).toEqual('boolean');

        //1651528966 = 2022-05-02T22:02:46.000Z
        const created: number = new Date(config.created).getTime() / 1000;
        expect(created).toEqual(1651528966);

        //1651525366 = 2022-05-02T23:02:46.000Z
        const modified: number = new Date(config.modified).getTime() / 1000;
        expect(modified).toEqual(1651532566);

        expect(typeof config.baseChain).toEqual('object');
        expect(typeof config.subChain).toEqual('object');
        expect(typeof config.contract).toEqual('object');

        expect(config['threshold_alerts'].length).toEqual(1);
        expect(config['severity_alerts'].length).toEqual(1);
        expect(config['time_window_alerts'].length).toEqual(1);
        expect(config.evm_nodes.length).toEqual(1);
        expect(config.nodes.length).toEqual(2);
        expect(config.repositories.length).toEqual(2);
        expect(config.systems.length).toEqual(1);
    });

    test("should check Basechain configured", async () => {
        ConfigMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const config = await ConfigModel.findOne<Config>({_id: id}) as Config;
        const basechain = config.baseChain;

        expect(basechain.id.toString()).toEqual('6265cefcfdb17d641746dced');
        expect(typeof basechain.status).toEqual('boolean');

        //1651615366 = 2022-05-03T22:02:46.000Z
        const created: number = new Date(basechain.created).getTime() / 1000;
        expect(created).toEqual(1651615366);

        //1651878166 = 2022-05-06T23:02:46.000Z
        const modified: number = new Date(basechain.modified).getTime() / 1000;
        expect(modified).toEqual(1651878166);

        expect(basechain.name).toEqual('Chainlink');
        expect(basechain.sources.length).toEqual(1);
    });

    test("should check Sourcetype inside Basechain configured", async () => {
        ConfigMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const config = await ConfigModel.findOne<Config>({_id: id}) as Config;
        const source = config.baseChain.sources[0];

        TestUtil.source(source);
    });

    test("should check Sub chain configured", async () => {
        ConfigMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const config = await ConfigModel.findOne<Config>({_id: id}) as Config;
        const subChain = config.subChain;

        expect(subChain.id.toString()).toEqual('626aeb43980cf43ee7bbf683');
        expect(typeof subChain.status).toEqual('boolean');

        //1651528966 = 2022-05-02T22:02:46.000Z
        const created: number = new Date(subChain.created).getTime() / 1000;
        expect(created).toEqual(1651528966);

        expect(subChain.modified).toEqual(null);
        expect(subChain.name).toEqual('binance');
    });

    test("should check Contract configured", async () => {

        ConfigMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const config = await ConfigModel.findOne<Config>({_id: id}) as Config;
        const contract = config.contract;

        expect(contract.id.toString()).toEqual('6267661fbe66cae642f57fb7');
        expect(contract.status).toEqual(false);

        //1651528966 = 2022-05-03T22:02:46.000Z
        const created: number = new Date(contract.created).getTime() / 1000;
        expect(created).toEqual(1651528966);

        expect(contract.modified).toEqual(null);

        expect(contract.name).toEqual('Weiwatcher');

        const url = 'https://weiwatchers.com/feeds-bsc-mainnet.json';
        expect(contract.url).toEqual(url);
        expect(contract.monitor).toEqual(true);
    });

    test("should check Threshold alert configured", async () => {
        ConfigMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const config = await ConfigModel.findOne<Config>({_id: id}) as Config;
        const threshold = config['threshold_alerts'][0];

        expect(threshold.id.toString()).toEqual('6269def62b7e18add54e96e9');
        expect(threshold.status).toEqual(true);

        //1651528966 = 2022-05-02T22:02:46.000Z
        const created: number = new Date(threshold.created).getTime() / 1000;
        expect(created).toEqual(1651528966);

        expect(threshold.modified).toEqual(null);

        expect(threshold.warning.enabled).toEqual(true);
        expect(threshold.warning.threshold).toEqual(0);

        expect(threshold.critical.enabled).toEqual(true);
        console.log(threshold.critical);
        expect(threshold.critical['repeat_enabled']).toEqual(true);
        expect(threshold.critical.threshold).toEqual(120);
        expect(threshold.critical.repeat).toEqual(300);
    });

    test("should check Severity alert configured", async () => {
        ConfigMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const config = await ConfigModel.findOne<Config>({_id: id}) as Config;
        const severity = config['severity_alerts'][0];
        expect(severity.id.toString()).toEqual('6269def62b7e18add54e96f1');
        expect(severity.status).toEqual(true);

        //1651528966 = 2022-05-02T22:02:46.000Z
        const created: number = new Date(severity.created).getTime() / 1000;
        expect(created).toEqual(1651528966);

        expect(severity.modified).toEqual(null);
        expect(typeof severity.type).toEqual('object');
    });

    test("should check Time Window alert configured", async () => {
        ConfigMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const config = await ConfigModel.findOne<Config>({_id: id}) as Config;
        const time_window = config['time_window_alerts'][0];

        expect(time_window.id.toString()).toEqual('6269def62b7e18add54e96e9');
        expect(time_window.status).toEqual(true);

        //1651528966 = 2022-05-02T22:02:46.000Z
        const created: number = new Date(time_window.created).getTime() / 1000;
        expect(created).toEqual(1651528966);

        expect(time_window.modified).toEqual(null);

        expect(time_window.warning.enabled).toEqual(true);
        expect(time_window.warning.threshold).toEqual(0);
        expect(time_window.warning['time_window']).toEqual(120);

        expect(time_window.critical.enabled).toEqual(true);
        expect(time_window.critical['repeat_enabled']).toEqual(true);
        expect(time_window.critical.threshold).toEqual(120);
        expect(time_window.critical.repeat).toEqual(300);
        expect(time_window.critical['time_window']).toEqual(120);
    });

    test("should check Repository configured", async () => {
        ConfigMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const config = await ConfigModel.findOne<Config>({_id: id}) as Config;
        const repository = config.repositories[0];

        expect(repository.id.toString()).toEqual('6269d75a5a34daa2cc7744e0');
        expect(repository.status).toEqual(true);

        //1651528966 = 2022-05-02T22:02:46.000Z
        const created: number = new Date(repository.created).getTime() / 1000;
        expect(created).toEqual(1651528966);

        expect(repository.modified).toEqual(null);
        expect(repository.name).toEqual('Tendermint');
        expect(repository.value).toEqual('tendermint/tendermint/');
        expect(repository.namespace).toEqual(null);

        expect(typeof repository.type).toEqual('object');

        expect(repository.monitor).toEqual(true);
    });

    test("should check RepositoryType inside Repository configured", async () => {
        ConfigMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const config = await ConfigModel.findOne<Config>({_id: id}) as Config;
        const type = config.repositories[0].type;

        TestUtil.repository(type);
    });

    test("should check EVMNode configured", async () => {
        ConfigMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const config = await ConfigModel.findOne<Config>({_id: id}) as Config;
        const evm = config.evm_nodes[0];

        expect(evm.id.toString()).toEqual('6267683dc0e201f1edbbdc39');
        expect(evm.status).toEqual(false);

        //1651528966 = 2022-05-02T22:02:46.000Z
        const created: number = new Date(evm.created).getTime() / 1000;
        expect(created).toEqual(1651528966);

        expect(evm.modified).toEqual(null);
        expect(evm.name).toEqual('bsc_139');
        expect(evm.nodeHttpUrl).toEqual('http://ip11:1234');
        expect(evm.monitor).toEqual(true);
    });

    test("should check Node configured", async () => {
        ConfigMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const config = await ConfigModel.findOne<Config>({_id: id}) as Config;

        const node = config.nodes[0];

        expect(node.id.toString()).toEqual('626765f4d9d14938006c3250');
        expect(node.status).toEqual(true);

        //1651528966 = 2022-05-02T22:02:46.000Z
        const created: number = new Date(node.created).getTime() / 1000;
        expect(created).toEqual(1651528966);

        expect(node.modified).toEqual(null);
        expect(node.name).toEqual('chainlink_bsc_ocr');

        const urls = 'https://ip6:82/metrics,https://ip7:82/metrics';
        expect(node.nodePrometheusUrls).toEqual(urls);

        expect(node.monitorPrometheus).toEqual(true);
        expect(node.monitorNode).toEqual(false);

        const evm_urls = 'http://ip8:1234,http://ip9:1234,http://ip10:1234';
        expect(node.evmNodesUrls).toEqual(evm_urls);

        const weiwatcher_url = `https://weiwatchers.com/feeds-bsc-mainnet.json`;
        expect(node.weiwatchersUrl).toEqual(weiwatcher_url);

        expect(node.monitorContracts).toEqual(true);

        const governance_addresses = 'x1,x2,x3';
        expect(node.governanceAddresses).toEqual(governance_addresses);
    });

    test("should check System configured", async () => {
        ConfigMockService.mock();

        const id = '62675e2d8891cd77b87f5b16';
        const config = await ConfigModel.findOne<Config>({_id: id}) as Config;
        const system = config.systems[0];

        expect(system.id.toString()).toEqual('62676606c72149c8dfa37c4e');
        expect(system.status).toEqual(true);

        //1651528966 = 2022-05-02T22:02:46.000Z
        const created: number = new Date(system.created).getTime() / 1000;
        expect(created).toEqual(1651528966);

        expect(system.modified).toEqual(null);
        expect(system.name).toEqual('system_chainlink_ocr_2');

        const url = 'http://ip12:7200/metrics';
        expect(system.exporterUrl).toEqual(url);

        expect(system.monitor).toEqual(true);
    });
});

describe('config endpoints family', () => {
    test("should check could_not_save_data error when put config", async () => {
        ConfigMockService.mockUpdate();
        ConfigMockService.saveError();

        const newConfig = {...config};
        delete newConfig.subChain;
        const endpoint = '/v1/configs/62675e2d8331c477b85f5b15';
        const res = await request(app).put(endpoint).send(newConfig);

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    test("should check put config", async () => {
        ConfigMockService.mockUpdate();
        ConfigMockService.save();

        const newConfig = {...config};
        delete newConfig.subChain;
        const endpoint = '/v1/configs/62675e2d8331c477b85f5b15';
        const res = await request(app).put(endpoint).send(newConfig);

        expect(res.statusCode).toEqual(Status.SUCCESS);
        expect(res.body.status).toEqual(Status.SUCCESS);
    });

    test("should check not found when put config", async () => {
        ConfigMockService.save();

        const endpoint = '/v1/configs/62675e2d8331c477b85f5b15';
        const res = await request(app).put(endpoint).send(config);

        expect(res.statusCode).toEqual(Status.NOT_FOUND);
        expect(res.body.status).toEqual(Status.NOT_FOUND);
    });

    test("should check post config", async () => {
        ConfigMockService.mockPost();
        ConfigMockService.save();

        const endpoint = '/v1/configs';
        const res = await request(app).post(endpoint).send({
            baseChain: {id: new ObjectID()},
            subChain: {name: 'test'}
        });

        expect(res.statusCode).toEqual(Status.SUCCESS);
        expect(res.body.status).toEqual(Status.SUCCESS);
    });

    test("should check could_not_save_data error when post config", async () => {
        ConfigMockService.mockPost();
        ConfigMockService.saveError();

        const endpoint = '/v1/configs';
        const res = await request(app).post(endpoint).send({
            baseChain: {id: new ObjectID()},
            subChain: {name: 'test'}
        });

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    test("should check duplicate sub chain on post config", async () => {
        ConfigMockService.mock();
        ConfigMockService.save();

        const endpoint = '/v1/configs';
        const res = await request(app).post(endpoint).send(config);

        expect(res.statusCode).toEqual(Status.CONFLICT);
        expect(res.body.status).toEqual(Status.CONFLICT);
    });

    test("should check remove config", async () => {
        ConfigMockService.remove();

        const endpoint = '/v1/configs/62675e2d8331c477b85f5b15';
        const res = await request(app).delete(endpoint);

        expect(res.statusCode).toEqual(Status.NO_CONTENT);
        expect(res.body).toEqual({});
    });

    test("should check remove config and not found", async () => {
        ConfigMockService.notRemoved();

        const endpoint = '/v1/configs/62675e2d8331c477b85f5b15';
        const res = await request(app).delete(endpoint);

        console.log(res.body);

        expect(res.statusCode).toEqual(Status.NOT_FOUND);
        expect(res.body.status).toEqual(Status.NOT_FOUND);
    });

    test("should check remove config and Server Error", async () => {
        ConfigMockService.mockError();

        const endpoint = '/v1/configs/62675e2d8331c477b85f5b15';
        const res = await request(app).delete(endpoint);

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    test("should check Config item by findOne and Server Error", async () => {
        ConfigMockService.mockError();

        const endpoint = '/v1/configs/62675e2d8331c477b85f5b15';
        const res = await request(app).get(endpoint);

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    test("should check Config item by findOne and NotFoundWarning", async () => {
        ConfigMockService.notFound();

        const endpoint = '/v1/configs/62675e2d8331c477b85f5b15';
        const res = await request(app).get(endpoint);

        expect(Status.NOT_FOUND).toEqual(res.statusCode);
    });

    test("should check Config list and Server Error", async () => {
        ConfigMockService.mockError();

        const endpoint = '/v1/configs';
        const res = await request(app).get(endpoint);

        expect(res.statusCode).toEqual(Status.E_536);
        expect(res.body.status).toEqual(Status.E_536);
    });

    test("should check Config list", async () => {
        ConfigMockService.mock();

        const endpoint = '/v1/configs';
        const res = await request(app).get(endpoint);

        const configs = res.body.result;

        expect(res.statusCode).toEqual(Status.SUCCESS);
        expect(res.body.status).toEqual(Status.SUCCESS);
        expect(configs.length).toEqual(1);
    });
});

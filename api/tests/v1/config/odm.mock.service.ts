import {ObjectID} from "mongodb";
import {ObjectUtil} from "../../../src/util/ObjectUtil";
import {BaseChainModel, BaseChainSchema} from "../../../src/v1/entity/model/BaseChainModel";
import {ConfigModel} from "../../../src/v1/entity/model/ConfigModel";
import {GenericModel, GenericSchema} from "../../../src/v1/entity/model/GenericModel";
import {
    SeverityAlertSubconfigModel,
    SeverityAlertSubconfigSchema
} from "../../../src/v1/entity/model/SeverityAlertSubconfigSchema";
import {basechain} from "../basechain/odm.mock.service";
import {RepositorySubconfigSchema} from "../../../src/v1/entity/model/RepositorySubconfigSchema";
import {Generic} from "../../../../entities/ts/Generic";

const mockingoose = require('mockingoose');

const node2 = ObjectUtil.snakeToCamel({
    "_id": "626765f4d9d14938006c0523",
    "status": true,
    "name": "chainlink_bsc_ocr_2",
    "node_prometheus_urls": "https://ip1:82/metrics,https://ip2:82/metrics",
    "monitor_prometheus": true,
    "monitor_node": true,
    "evm_nodes_urls": "http://ip3:1234,http://ip4:1234,http://ip5:1234",
    "weiwatchers_url": "https://weiwatchers.com/feeds-bsc-mainnet.json",
    "monitor_contracts": true,
    "governance_addresses": "x1,x2,x3"
})

const node1 = ObjectUtil.snakeToCamel({
    "_id": "626765f4d9d14938006c3250",
    "status": true,
    "created": "2022-05-02T22:02:46.000Z",
    "modified": null,
    "name": "chainlink_bsc_ocr",
    "node_prometheus_urls": "https://ip6:82/metrics,https://ip7:82/metrics",
    "monitor_prometheus": true,
    "monitor_node": false,
    "evm_nodes_urls": "http://ip8:1234,http://ip9:1234,http://ip10:1234",
    "weiwatchers_url": "https://weiwatchers.com/feeds-bsc-mainnet.json",
    "monitor_contracts": true,
    "governance_addresses": "x1,x2,x3"
});

const severityType = {
    "_id": "6265d08efdb17d641746dcf0",
    "status": true,
    "created": "2022-05-02T22:02:46.000Z",
    "modified": null,
    "name": "Warning",
    "value": null,
    "description": null,
    "group": "severity_type"
};

const severityAlert = {
    "_id": "6269def62b7e18add54e96f1",
    "created": "2022-05-02T22:02:46.000Z",
    "modified": null,
    "status": true,
    "name": "Slashed",
    "value": "slashed",
    "description": "Raised when your validator has been slashed.",
    "group": "severity_alert",
    "type": severityType
};

const thresholdAlert = {
    "_id": "6269def62b7e18add54e96e9",
    "status": true,
    "created": "2022-05-02T22:02:46.000Z",
    "modified": null,
    "name": "Cannot access validator",
    "value": "cannot_access_validator",
    "description": "Raised when a validator is unaccessible.",
    "group": "threshold_alert",
    "critical": {
        "enabled": true,
        "repeat_enabled": true,
        "threshold": 120,
        "repeat": 300
    },
    "warning": {
        "enabled": true,
        "threshold": 0
    }
};

const timeWindowAlert = {
    "_id": "6269def62b7e18add54e96e9",
    "status": true,
    "created": "2022-05-02T22:02:46.000Z",
    "modified": null,
    "name": "Cannot access validator",
    "value": "cannot_access_validator",
    "description": "Raised when a validator is unaccessible.",
    "group": "threshold_alert",
    "critical": {
        "enabled": true,
        "repeat_enabled": true,
        "threshold": 120,
        "repeat": 300,
        "time_window": 120
    },
    "warning": {
        "enabled": true,
        "threshold": 0,
        "time_window": 120
    }
};

const channelType = {
    "_id": "62656ebafdb17d641746dcda",
    "created": "2022-04-01T00:00:00Z",
    "modified": null,
    "status": true,
    "name": "Telegram",
    "value": 'telegram',
    "description": null,
    "group": "channel_type"
};

const repositoryType = {
    "_id": "6269d55af66c0c5b67d125a6",
    "created": "2022-05-02T22:02:46.000Z",
    "modified": null,
    "status": true,
    "name": "Github Repo",
    "value": 'git',
    "description": null,
    "group": "repository_type"
};

const configType = {
    "_id": "6265758cfdb17d641746dce4",
    "created": "2022-05-02T22:02:46.000Z",
    "modified": null,
    "status": true,
    "name": "Sub Chain",
    "value": null,
    "description": null,
    "group": "config_type"
};

const sourceType = {
    "_id": "6271178cf740ef3847a7d27e",
    "status": true,
    "created": "2022-04-01T00:00:00.000Z",
    "modified": null,
    "name": "Contract",
    "value": "contract",
    "description": null,
    "group": 'source_type'
};

export const config = {
    "_id": "62675e2d8891cd77b87f5b16",
    "config_type": "6265758cfdb17d641746dce4",
    "status": true,
    "created": "2022-05-02T22:02:46.000Z",
    "modified": "2022-05-02T23:02:46.000Z",
    "baseChain": {
        "_id": "6265cefcfdb17d641746dced",
        "created": "2022-05-03T22:02:46.000Z",
        "modified": "2022-05-06T23:02:46.000Z",
        "status": true,
        "name": "Chainlink",
        "sources": [sourceType]
    },
    "subChain": {
        "_id": "626aeb43980cf43ee7bbf683",
        "status": true,
        "created": "2022-05-02T22:02:46.000Z",
        "modified": null,
        "name": "binance"
    },
    "contract": {
        "_id": "6267661fbe66cae642f57fb7",
        "status": false,
        "created": "2022-05-02T22:02:46.000Z",
        "modified": null,
        "name": "Weiwatcher",
        "url": "https://weiwatchers.com/feeds-bsc-mainnet.json",
        "monitor": true
    },
    "threshold_alerts": [
        thresholdAlert,
    ],
    "severity_alerts": [
        severityAlert
    ],
    "time_window_alerts": [
        timeWindowAlert,
    ],
    "repositories": [
        {
            "_id": "6269d75a5a34daa2cc7744e0",
            "status": true,
            "created": "2022-05-02T22:02:46.000Z",
            "modified": null,
            "name": "Tendermint",
            "value": "tendermint/tendermint/",
            "namespace": null,
            "type": repositoryType,
            "monitor": true
        },
        {
            "_id": "6269d81f3f76d2c6ababbafe",
            "status": true,
            "created": "2022-05-02T22:02:46.000Z",
            "modified": null,
            "name": "tendermint",
            "value": "tendermit",
            "namespace": "tendermint",
            "type": {
                "_id": "6269d568d509ee91767dbfd6",
                "status": true,
                "created": "2022-05-02T22:02:46.000Z",
                "modified": null,
                "name": "Dockerhub Repo",
                "value": null,
                "description": null
            },
            "monitor": true
        }
    ],
    "evm_nodes": [
        ObjectUtil.snakeToCamel({
            "_id": "6267683dc0e201f1edbbdc39",
            "status": false,
            "created": "2022-05-02T22:02:46.000Z",
            "modified": null,
            "name": "bsc_139",
            "node_http_url": "http://ip11:1234",
            "monitor": true
        })
    ],
    "nodes": [node1, node2],
    "systems": [
        ObjectUtil.snakeToCamel({
            "_id": "62676606c72149c8dfa37c4e",
            "status": true,
            "created": "2022-05-02T22:02:46.000Z",
            "modified": null,
            "name": "system_chainlink_ocr_2",
            "exporter_url": "http://ip12:7200/metrics",
            "monitor": true
        })
    ]
};

/**
 * Service to mock Configuration Document
 */
export class ConfigMockService {
    public static mock(): void {

        //to mock populate of mongoose
        ConfigModel.schema.path('baseChain', BaseChainSchema);
        BaseChainModel.schema.path('sources', [GenericSchema]);

        SeverityAlertSubconfigSchema.path('status', Boolean);
        SeverityAlertSubconfigSchema.path('type', Object);
        RepositorySubconfigSchema.path('type', Object);

        //mock findone
        mockingoose(ConfigModel).toReturn(config, 'findOne');
        mockingoose(ConfigModel).toReturn(config);
        mockingoose(ConfigModel).toReturn([config], 'find');
    }

    public static mockUpdate(): void {
        //to mock validators result
        mockingoose(GenericModel).toReturn(1, 'countDocuments');
        mockingoose(BaseChainModel).toReturn(1, 'countDocuments');

        //to avoid not found error
        mockingoose(ConfigModel).toReturn(config, 'findOne');

        //to avoid duplicate error
        mockingoose(ConfigModel).toReturn([], 'find');
    }

    public static mockPost(): void {
        //to mock validators result
        mockingoose(BaseChainModel).toReturn(1, 'countDocuments');
        mockingoose(GenericModel).toReturn(1, 'countDocuments');

        //to avoid duplicate error
        mockingoose(ConfigModel).toReturn([], 'find');
    }

    public static count(total: number): void {
        mockingoose(ConfigModel).toReturn(total, 'countDocuments');
        mockingoose(ConfigModel).toReturn(total, 'count');
    }

    public static mockError(): void {
        mockingoose(ConfigModel).toReturn(new Error('erro'), 'findOne');
        mockingoose(ConfigModel).toReturn(new Error('erro'), 'find');
    }

    public static notFound(): void {
        mockingoose(ConfigModel).toReturn(null, 'findOne');
    }

    public static remove(): void {
        mockingoose(GenericModel).toReturn(1, 'countDocuments');
        mockingoose(BaseChainModel).toReturn(1, 'countDocuments');
        mockingoose(ConfigModel).toReturn(config, 'findOne');
        
        mockingoose(ConfigModel).toReturn({deletedCount: 1}, 'deleteOne');
    }

    public static notRemoved(): void {
        mockingoose(GenericModel).toReturn(1, 'countDocuments');
        mockingoose(BaseChainModel).toReturn(1, 'countDocuments');
        mockingoose(ConfigModel).toReturn(config, 'findOne');
        
        mockingoose(ConfigModel).toReturn({deletedCount: 0}, 'deleteOne');
        
    }

    public static save(): void {
        const obj = Object.assign(
            JSON.parse(JSON.stringify(config)), //to avoid change mock reference
            {baseChain: new ObjectID().toHexString()}
        );
        mockingoose(ConfigModel).toReturn(obj, 'save');
        mockingoose(BaseChainModel).toReturn(basechain, 'findOne');
    }

    public static saveError(): void {
        mockingoose(ConfigModel).toReturn(new Error(), 'save');
        mockingoose(BaseChainModel).toReturn(basechain, 'findOne');
    }
}

/**
 * Service to mock Generic Domain Types
 */
export class GenericMockService {
    public static mockChannelType(): void {
        mockingoose(GenericModel).toReturn([channelType], 'find');
    }

    public static mockThresholdAlert(): void {
        mockingoose(GenericModel).toReturn([thresholdAlert], 'find');
    }

    public static mockSeverityAlert(): void {
        mockingoose(SeverityAlertSubconfigModel).toReturn([severityAlert], 'find');
    }

    public static mockTimeWindowAlert(): void {
        mockingoose(GenericModel).toReturn([timeWindowAlert], 'find');
    }

    public static mockSeverityType(): void {
        mockingoose(GenericModel).toReturn([severityType], 'find');
    }

    public static mockConfigType(): void {
        mockingoose(GenericModel).toReturn([configType], 'find');
    }

    public static mockSourceType(): void {
        mockingoose(GenericModel).toReturn([sourceType], 'find');
    }

    public static mockRepositoryType(): void {
        mockingoose(GenericModel).toReturn([repositoryType], 'find');
    }
}


/**
 * Service to mock Errors for Generic Domain
 */
export class GenericErrorMockService {
    public static mockFind(): void {
        mockingoose(GenericModel).toReturn(new Error("Error to find a document!"), 'find');
        mockingoose(SeverityAlertSubconfigModel).toReturn(new Error("Error to find a document!"), 'find');
    }
}

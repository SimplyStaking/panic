import {BaseChainModel} from "../../../src/v1/entity/model/BaseChainModel";
import {GenericSchema} from "../../../src/v1/entity/model/GenericModel";
import {
    SeverityAlertSubconfigModel,
    SeverityAlertSubconfigSchema
} from "../../../src/v1/entity/model/SeverityAlertSubconfigSchema";

const mockingoose = require('mockingoose');

const severityType = {
    "id": "6265d08efdb17d641746dcf0",
    "status": true,
    "created": "2022-05-02T22:02:46.000Z",
    "modified": null,
    "name": "Warning",
    "value": null,
    "description": null,
    "group": "severity_type"
};

const severityAlert = {
    "id": "6269def62b7e18add54e96f1",
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
    "id": "6269def62b7e18add54e96e9",
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
    "id": "6269def62b7e18add54e96e9",
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

const sourceType = {
    "id": "6271178cf740ef3847a7d27e",
    "status": true,
    "created": "2022-04-01T00:00:00.000Z",
    "modified": null,
    "name": "Contract",
    "value": "contract",
    "description": null,
    "group": 'source_type'
};

export const basechain = {
    "_id": "62675e2d8891cd77b87f5b16",
    "status": true,
    "created": "2022-05-02T22:02:46.000Z",
    "modified": "2022-05-02T23:02:46.000Z",
    "name": "Test Chain",
    "value": "test_chain",
    "sources": [sourceType],
    "severity_alerts": [severityAlert],
    "threshold_alerts": [thresholdAlert],
    "time_window_alerts": [timeWindowAlert]
};

/**
 * Service to mock Base Chain Document
 */
export class BaseChainMockService {
    public static mock(): void {
        //to mock populate of mongoose
        BaseChainModel.schema.path('sources', [GenericSchema]);
        BaseChainModel.schema.path('severity_alerts', [SeverityAlertSubconfigSchema]);
        BaseChainModel.schema.path('threshold_alerts', [GenericSchema]);
        BaseChainModel.schema.path('time_window_alerts', [GenericSchema]);

        SeverityAlertSubconfigModel.schema.path('type', GenericSchema);

        //mock findone
        mockingoose(BaseChainModel).toReturn(basechain, 'findOne');
        mockingoose(BaseChainModel).toReturn(basechain);
        mockingoose(BaseChainModel).toReturn([basechain], 'find');
    }

    public static mockError(): void {
        mockingoose(BaseChainModel).toReturn(new Error('erro'), 'findOne');
        mockingoose(BaseChainModel).toReturn(new Error('erro'), 'find');
    }

    public static findOneNotFound(): void {
        mockingoose(BaseChainModel).toReturn(null, 'findOne');
    }
}

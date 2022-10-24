import * as core from 'express-serve-static-core';
import {GenericResource} from "../rest/generic/GenericResource";

/**
 * Generic Routes
 */
export class GenericRoute {

    public constructor(app: core.Express) {
        const generic = new GenericResource();

        app.get('/v1/channel-types', generic.channelTypeList.bind(generic));
        app.get('/v1/threshold-alerts', generic.thresholdAlertList.bind(generic));
        app.get('/v1/severity-alerts', generic.severityAlertList.bind(generic));
        app.get('/v1/time-window-alerts', generic.timeWindowAlertList.bind(generic));
        app.get('/v1/severity-types', generic.severityTypeList.bind(generic));
        app.get('/v1/repository-types', generic.repositoryTypeList.bind(generic));
        app.get('/v1/source-types', generic.sourceTypeList.bind(generic));
        app.get('/v1/config-types', generic.configTypeList.bind(generic));
    }
}

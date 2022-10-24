import * as core from 'express-serve-static-core';
import {ConfigResource} from '../rest/config/ConfigResource';

/**
 * Configuration routes
 */
export class ConfigRoute {
    private readonly _config: ConfigResource = null;

    public constructor(app: core.Express) {
        this._config = new ConfigResource();

        app.get('/v1/configs', this._config.getAll.bind(this._config));
        app.post('/v1/configs', this._config.create.bind(this._config));
        app.get('/v1/configs/:id', this._config.getItem.bind(this._config));
        app.put('/v1/configs/:id', this._config.update.bind(this._config));
        app.delete('/v1/configs/:id', this._config.remove.bind(this._config));
    }

    public get config(): ConfigResource {
        return this._config;
    }
}

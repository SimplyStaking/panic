import * as core from 'express-serve-static-core';
import {InstallationResource} from '../rest/installation/InstallationResource';

/**
 * Installation routes
 */
export class InstallationRoute {

    public constructor(app: core.Express) {
        const install = new InstallationResource();

        app.get('/v1/installation/is-first', install.isFirstInstall.bind(install));
    }
}

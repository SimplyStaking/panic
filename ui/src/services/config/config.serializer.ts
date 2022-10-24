import { Config } from "../../../../entities/ts/Config";

/**
 * Converts "raw data" (JSON response) into {@link ConfigInterface} object and vice-versa.
 */
export class ConfigSerializer {

    unserialize(jsonObject: object): Config {
        return Config.fromJSON(jsonObject, Config);
    }

    serialize(entity: Config): string {
        return JSON.stringify(entity);
    }
}

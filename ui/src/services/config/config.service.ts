import {ServiceInterface} from "../service.interface";
import {BaseSerializer} from "../serializer.interface";
import {ConfigSerializer} from "./config.serializer";
import {Config} from "../../../../entities/ts/Config";
import {API_URL} from "../../utils/constants";
import { HelperAPI } from "../../utils/helpers";

/**
 * Fetches "raw data" from the base chain endpoints and convert them to the
 * equivalent entity model.
 *
 * ConfigService is a singleton. To get the instance of this service, you must
 * call `ConfigService.getInstance()`.
 */
export class ConfigService implements ServiceInterface<Config> {

    ENDPOINT_URL: string = `${API_URL}v1/configs`;
    serializer: BaseSerializer<Config> = new ConfigSerializer();

    /**
     * It represents the `single` instance shared across the consumers of
     * `ConfigService`.
     */
    private static _instance: ConfigService;

    /**
     * Since this class is a `singleton`, we cannot allow object creation.
     */
    private constructor() { }

    /**
     * This static method is used to get an instance of {@link ConfigService}.
     *
     * @returns the `singleton` instance of {@link ConfigService}
     */
    public static getInstance(): ConfigService {
        if (!ConfigService._instance)
            ConfigService._instance = new ConfigService();

        return ConfigService._instance;
    }

    async getAll(): Promise<Config[]> {
        try {
            const configs: Config[] = [];
            const response = await fetch(this.ENDPOINT_URL);
            const json = await response.json();

            json.result.forEach((serializedConfig) => {
                configs.push(serializedConfig);
            });

            return new Promise((resolve) => { resolve(configs); });
        } catch (error) {
            HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
        }
    }

    async getByID(id: string, suppressToast: boolean = false): Promise<Config> {
        try {
            const config = await fetch(`${this.ENDPOINT_URL}/${id}`, { method: 'GET' });
            const json = await config.json();

            return Config.fromJSON(json.result, Config);
        } catch (error) {
            if(!suppressToast){
                HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
            }
        }
    }

    async save(config: Config): Promise<Response> {
        const endpoint: string = config.id ? `${this.ENDPOINT_URL}/${config.id}` : this.ENDPOINT_URL;
        const httpMethod: string = config.id ? 'PUT' : 'POST';

        try {
            return await fetch(endpoint,
                {
                    method: httpMethod,
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(config),
                });
        } catch (error) {
            HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
        }
    }

    async delete(configId: string): Promise<boolean> {
        try {
            const response = await fetch(`${this.ENDPOINT_URL}/${configId}`, { method: "DELETE" });

            return response.ok;
        } catch (error) {
            HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
        }
    }
}

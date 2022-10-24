import {ServiceInterface} from "../service.interface";
import {BaseSerializer} from "../serializer.interface";
import {ChannelSerializer} from "./channel.serializer";
import {API_URL} from "../../utils/constants";
import {Channel} from "../../../../entities/ts/channels/AbstractChannel";
import { HelperAPI } from "../../utils/helpers";

/**
 * Fetches "raw data" from the base chain endpoints and convert them to the equivalent entity model.
 *
 * ConfigService is a singleton. To get the instance of this service, you must call `ConfigService.getInstance()`.
 */
export class ChannelService implements ServiceInterface<Channel> {

    ENDPOINT_URL: string = `${API_URL}v1/channels`;
    serializer: BaseSerializer<Channel> = new ChannelSerializer();

    /**
     * It represents the `single` instance shared across the consumers of `ConfigService`.
     */
    private static _instance: ChannelService;

    /**
     * Since this class is a `singleton`, we cannot allow object creation.
     */
    private constructor() { }

    /**
     * This static method is used to get an instance of {@link ChannelService}.
     *
     * @returns the `singleton` instance of {@link ChannelService}
     */
    public static getInstance(): ChannelService {
        if (!ChannelService._instance)
            ChannelService._instance = new ChannelService();

        return ChannelService._instance;
    }

    async getAll(): Promise<Channel[]> {
        try {
            const channels: Channel[] = [];
            const response = await fetch(this.ENDPOINT_URL);
            const json = await response.json();

            json.result.forEach((serializedChannel) => {
                channels.push(serializedChannel);
            });

            return new Promise((resolve) => {
                resolve(channels);
            });
        } catch (error) {
            HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
        }
    }

    async getByID(id: string): Promise<Channel> {
        try {
                const response = await fetch(`${this.ENDPOINT_URL}/${id}`, { method: "GET" });
                const json = await response.json();
                const channel: Channel = json.result;

                return new Promise((resolve) => { resolve(channel); });
        } catch (error) {
            HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
        }
    }

    async enableChannelOnConfig(channelId: string, configId: string): Promise<boolean> {
        try {
            const response = await fetch(`${this.ENDPOINT_URL}/${channelId}/configs/${configId}`, { method: 'POST' });

            return response.ok;
        } catch (error) {
            HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
        }
    }

    async disableChannelOnConfig(channelId: string, configId: string): Promise<boolean> {
        try {
            const response = await fetch( `${this.ENDPOINT_URL}/${channelId}/configs/${configId}`, { method: 'DELETE'} );

            return response.ok;
        } catch (error) {
            HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
        }
    }

    async save(channel: Channel): Promise<Response> {
        try {
            const endpoint: string = channel.id ? `${this.ENDPOINT_URL}/${channel.id}` : this.ENDPOINT_URL;
            const httpMethod: string = channel.id ? 'PUT' : 'POST';

            return await fetch(endpoint,
                {
                    method: httpMethod,
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(channel)
            });
        } catch (error) {
            HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
        }
    }

    async delete(channelId: number|string): Promise<boolean> {
        try {
            const response = await fetch(`${this.ENDPOINT_URL}/${channelId}`, { method: 'DELETE' });

            return response.ok;
        } catch (error) {
            HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
        }
    }
}
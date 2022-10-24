import {BaseSerializer} from "../serializer.interface";
import {API_URL} from "../../utils/constants";
import {Generic} from "../../../../entities/ts/Generic";
import {DomainSerializer} from "./domain.serializer";
import {ChannelType} from "../../../../entities/ts/ChannelType";
import {SeverityType} from "../../../../entities/ts/SeverityType";
import {RepositoryType} from "../../../../entities/ts/RepositoryType";
import {SourceType} from "../../../../entities/ts/SourceType";
import { HelperAPI } from "../../utils/helpers";

/**
 * Fetches "raw data" from the domain endpoints and convert them to the equivalent entity model.
 *
 * DomainService is a singleton. To get the instance of this service, you must call `DomainService.getInstance()`.
 */
export class DomainService {

    serializer: BaseSerializer<Generic> = new DomainSerializer();

    /**
     * It represents the `single` instance shared across the consumers of `DomainService`.
     */
    private static _instance: DomainService;

    /**
     * Since this class is a `singleton`, we cannot allow object creation.
     */
    private constructor() { }

    /**
     * This static method is used to get an instance of {@link DomainService}.
     *
     * @returns the `singleton` instance of {@link DomainService}
     */
    public static getInstance(): DomainService {
        if (!DomainService._instance)
            DomainService._instance = new DomainService();

        return DomainService._instance;
    }

    async getAllChannelTypes(): Promise<ChannelType[]> {
        try {
            const channelTypes: ChannelType[] = [];
            const response = await fetch(`${API_URL}v1/channel-types`);
            const json = await response.json();

            json.result.forEach((rawChannelType) => {
                const model: ChannelType = this.serializer.unserialize(rawChannelType);
                channelTypes.push(model);
            });

            return new Promise((resolve) => {
                resolve(channelTypes);
            });
        } catch (error) {
            HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
        }
    }

    async getAllSeverityTypes(): Promise<SeverityType[]> {
        try {
            const severityTypes: SeverityType[] = [];
            const response = await fetch(`${API_URL}v1/severity-types`);
            const json = await response.json();

            json.result.forEach((rawSeverityType) => {
                const model: SeverityType = this.serializer.unserialize(rawSeverityType);
                severityTypes.push(model);
            });

            return new Promise((resolve) => {
                resolve(severityTypes);
            });
        } catch (error) {
            HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
        }
    }

    async getAllRepositoryTypes(): Promise<RepositoryType[]> {
        try {
            const repositoryTypes: RepositoryType[] = [];
            const response = await fetch(`${API_URL}v1/repository-types`);
            const json = await response.json();

            json.result.forEach((rawRepositoryType) => {
                const model: RepositoryType = this.serializer.unserialize(rawRepositoryType);
                repositoryTypes.push(model);
            });

            return new Promise((resolve) => {
                resolve(repositoryTypes);
            });
        } catch (error) {
            HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
        }
    }

    async getAllSourceTypes(): Promise<SourceType[]> {
        try {
            const sourceTypes: SourceType[] = [];
            const response = await fetch(`${API_URL}v1/source-types`);
            const json = await response.json();

            json.result.forEach((rawSourceType) => {
                const model: ChannelType = this.serializer.unserialize(rawSourceType);
                sourceTypes.push(model);
            });

            return new Promise((resolve) => {
                resolve(sourceTypes);
            });
        } catch (error) {
            HelperAPI.raiseToast("Could not communicate with the database. Check the API Docker service!", 3000, "danger");
        }
    }
}
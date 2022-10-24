import {BaseChain} from "../../../../entities/ts/BaseChain";
import {ServiceInterface} from "../service.interface";
import {BaseSerializer} from "../serializer.interface";
import {BaseChainSerializer} from "./base-chain.serializer";
import {API_URL} from "../../utils/constants";

/**
 * Fetches "raw data" from the base chain endpoints and convert them to the equivalent entity model.
 *
 * BaseChainService is a singleton. To get the instance of this service, you must call `BaseChainService.getInstance()`.
 */
export class BaseChainService implements ServiceInterface<BaseChain> {

    ENDPOINT_URL: string = `${API_URL}v1/basechains`;
    serializer: BaseSerializer<BaseChain> = new BaseChainSerializer();

    /**
     * It represents the `single` instance shared across the consumers of `BaseChainService`.
     */
    private static _instance: BaseChainService;

    /**
     * Since this class is a `singleton`, we cannot allow object creation.
     */
    private constructor() { }

    /**
     * This static method is used to get an instance of {@link BaseChainService}.
     *
     * @returns the `singleton` instance of {@link BaseChainService}
     */
    public static getInstance(): BaseChainService {
        if (!BaseChainService._instance)
            BaseChainService._instance = new BaseChainService();

        return BaseChainService._instance;
    }

    async getAll(): Promise<BaseChain[]> {
        const baseChains: BaseChain[] = [];
        const response = await fetch(this.ENDPOINT_URL);
        const json = await response.json();

        json.result.forEach((serialisedBaseChain) => {
            baseChains.push(serialisedBaseChain);
        });

        return new Promise((resolve) => {
            resolve(baseChains);
        });
    }

    async getByID(id: string): Promise<BaseChain> {
        const config = await fetch(`${this.ENDPOINT_URL}/${id}`, {
            method: 'GET'
        });

        const json = await config.json();

        return BaseChain.fromJSON(json.result, BaseChain);
    }
}

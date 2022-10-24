import { BaseSerializer } from "./serializer.interface";

/**
 * Fetches data from the API and converts it to the equivalent model.
 */
export interface ServiceInterface<EntityInterface> {

    /**
     * Each `entity` has a specific endpoint.
     */
    ENDPOINT_URL: string,

    /**
     * Object reponsible for serializing requests and unserializing responses for each `entity`.
     */
    serializer: BaseSerializer<EntityInterface>,

    /**
     * Fetches from the API all entities of a particular type.
     *
     * @returns an array of a particular `entity` type.
     */
    getAll(): Promise<EntityInterface[]>,

    /**
     * Fetches from the API a single `entity` identified by the attribute `id`.
     *
     * @param id the unique identifier for a given `entity`.
     */
    getByID(id: string): Promise<EntityInterface>,

    /**
     * Saves (insert or update) an `entity` in the DB.
     *
     * @param entity the `entity` to be added/updated in the DB.
     * @returns boolean whether the operation succeed.
     */
    save?(entity: EntityInterface): Promise<Response>

}

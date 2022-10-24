/**
 * Maps "raw data" (JSON present in responses) to a specifc model and vice-versa.
 */
export interface BaseSerializer<EntityInterface> {

    /**
     * Transforms the data in JSON format to an object of type specified by `EntityInterface`.
     * 
     * Used in the logic that runs after making a call to the API.  
     * 
     * @param data json representation of a given `entity`
     * @returns an object of type `EntityInterface`
     */
    unserialize(data: any): EntityInterface,

    /**
     * Serializes the `entity` and returns it in JSON format.
     * 
     * 
     * @param entity the entity to be serialized
     * @returns a JSON representing the `entity`
     */
    serialize(entity: EntityInterface): string
}
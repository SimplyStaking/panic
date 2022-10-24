import { Model, Schema } from "mongoose";

/**
 * Interface of building steps to create 
 */
export interface IModelBuilder<T> {
    /** Step to load all dependencies for model */
    loadDependencies?(): void;
    /** Step to produce Mongoose Schema  */
    produceSchema(): void;
    /** Step to produce Mongoose Model  */
    produceModel(): void;
    /** Returns a Mongoose Model  */
    model: Model<T>;
    /** Returns a Mongoose Schema  */
    schema: Schema;
}




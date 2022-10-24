import {IModelBuilder} from "./IModelBuilder";

/**
 * Responsible for executing the building Schemas and Models in a particular
 * sequence. The Model Director is not optional in this app.
 */
export class ModelBuildDirector<T> {
    public constructor(builder: IModelBuilder<T>) {
        builder.produceSchema();
        builder.produceModel();
    }
}

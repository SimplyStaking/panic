import mongoose, { Model, Schema } from 'mongoose';
import { Config } from '../../../../entities/ts/Config';
import { Collection, ModelName } from '../../constant/mongoose';
import { MongooseUtil } from '../../util/MongooseUtil';
import { IModelBuilder } from './IModelBuilder';
import { ConfigModelBuilder } from './ConfigModelBuilder';

/**
 * Builder to create Mongoose Schema and Model of Config Entity
 */
export class ConfigOldModelBuilder implements IModelBuilder<Config> {

    private _schema: Schema = null;
    private _model: Model<Config> = null;

    public produceSchema(): void {

        //make copy
        const builder = new ConfigModelBuilder()
        builder.produceSchema();

        this._schema = builder.schema;

        MongooseUtil.virtualize(this._schema);
    }

    public produceModel(): void {
        this._model = mongoose.model(
            ModelName.CONFIG_OLD,
            this._schema,
            Collection.CONFIG_OLD
        ) as Model<Config>;
    }

    public get model(): Model<Config> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}

import {Model, Schema} from "mongoose";
import {RepositorySubconfig} from "../../../../entities/ts/RepositorySubconfig";
import {MongooseUtil} from "../../util/MongooseUtil";
import {ObjectUtil} from "../../util/ObjectUtil";
import {BaseMongoose} from "../entity/model/BaseMongoose";
import {IModelBuilder} from "./IModelBuilder";
import {ModelName} from "../../constant/mongoose";
import {GenericRepository} from "../entity/repository/GenericRepository";

/**
 * Builder to create Mongoose Schema of RepositorySubconfig Entity
 */
export class RepositorySubconfigModelBuilder
    implements IModelBuilder<RepositorySubconfig> {

    private _schema: Schema = null;
    private _model: Model<RepositorySubconfig> = null;

    public produceSchema(): void {

        const entity = {} as RepositorySubconfig;
        entity.monitor = {type: Boolean, default: null} as any;
        entity.value = {type: String, default: null} as any;
        entity.namespace = {type: String, default: null} as any;
        entity.type = {
            type: Schema.Types.ObjectId,
            ref: ModelName.GENERIC,
            required: [true, 'Repository type is required!'],
            default: null,
            validate: {
                validator: async (id: string) => {
                    const repo = new GenericRepository();
                    const repo_type = await repo.findOneByGroupAndId('repository_type', id);
                    return repo_type !== null;
                },
                message: props => `Reference with id ${props.value} doesn't exists`
            }
        } as any;

        const obj = Object.assign(entity, new BaseMongoose());
        this._schema = new Schema(ObjectUtil.camelToSnake<object>(obj),
            {versionKey: false});

        MongooseUtil.virtualize(this._schema);
    }

    public produceModel(): void {
        this._model = null;
    }

    public get model(): Model<RepositorySubconfig> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}
import mongoose, {Model, Schema} from "mongoose";
import {TimeWindowAlertSubconfig} from "../../../../entities/ts/TimeWindowAlertSubconfig";
import {ObjectUtil} from "../../util/ObjectUtil";
import {IModelBuilder} from "./IModelBuilder";
import {MongooseUtil} from "../../util/MongooseUtil";
import {StringUtil} from "../../util/StringUtil";
import {Collection, ModelName} from "../../constant/mongoose";

/**
 * Builder to create Mongoose Schema of TimeWindowAlertSubconfig Entity
 */
export class TimeWindowAlertSubconfigModelBuilder implements IModelBuilder<TimeWindowAlertSubconfig> {

    private _schema: Schema = null;
    private _model: Model<TimeWindowAlertSubconfig> = null;

    public produceSchema(): void {

        const entity = {} as TimeWindowAlertSubconfig;
        entity.status = {type: Boolean, default: true} as any;
        entity.created = {type: Date, default: Date.now} as any;
        entity.modified = {type: Date, default: null} as any;
        entity.name = {
            type: String,
            default: null,
            set: StringUtil.trim
        } as any;
        entity.value = {type: String, default: null} as any;
        entity.description = {type: String, default: null} as any;
        entity.group = {type: String, default: null} as any;
        entity.warning = {
            enabled: {type: Boolean, default: false} as any,
            threshold: {type: Number, default: 0} as any,
            time_window: {type: Number, default: 0, alias: 'timeWindow'} as any,
        } as any;
        entity.critical = {
            enabled: {type: Boolean, default: false} as any,
            repeat_enabled: {type: Boolean, default: false, alias: 'repeatEnabled'} as any,
            threshold: {type: Number, default: 0} as any,
            repeat: {type: Number, default: 0} as any,
            time_window: {type: Number, default: 0, alias: 'timeWindow'} as any,
        } as any;
        entity.adornment = {type: String, default: null} as any;
        entity.enabled = {type: Boolean, default: true} as any;

        this._schema = new Schema(ObjectUtil.camelToSnake<object>(entity),
            {versionKey: false});
        MongooseUtil.virtualize(this._schema);
    }

    public produceModel(): void {
        this._model = mongoose.model(
            ModelName.TIME_WINDOW_ALERT_SUBCONFIG,
            this._schema,
            Collection.GENERIC
        ) as Model<TimeWindowAlertSubconfig>;
    }

    public get model(): Model<TimeWindowAlertSubconfig> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}

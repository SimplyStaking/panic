import {Model, Schema} from "mongoose";
import {NodeSubconfig} from "../../../../entities/ts/NodeSubconfig";
import {MongooseUtil} from "../../util/MongooseUtil";
import {ObjectUtil} from "../../util/ObjectUtil";
import {BaseMongoose} from "../entity/model/BaseMongoose";
import {IModelBuilder} from "./IModelBuilder";

/**
 * Builder to create Mongoose Schema of NodeSubconfig Entity
 */
export class NodeSubconfigModelBuilder implements IModelBuilder<NodeSubconfig> {

    private _schema: Schema = null;
    private _model: Model<NodeSubconfig> = null;

    public produceSchema(): void {

        const entity = {} as NodeSubconfig;
        entity.nodePrometheusUrls = {
            type: String,
            alias: 'nodePrometheusUrls',
            default: null
        } as any;
        entity.monitorPrometheus = {
            type: Boolean,
            alias: 'monitorPrometheus',
            default: null
        } as any;
        entity.monitorNode = {
            type: Boolean,
            alias: 'monitorNode',
            default: null
        } as any;
        entity.evmNodesUrls = {
            type: String,
            alias: 'evmNodesUrls',
            default: null
        } as any;
        entity.weiwatchersUrl = {
            type: String,
            alias: 'weiwatchersUrl',
            default: null
        } as any;
        entity.monitorContracts = {
            type: Boolean,
            alias: 'monitorContracts',
            default: null
        } as any;
        entity.cosmosRestUrl = {
            type: String,
            alias: 'cosmosRestUrl',
            default: null
        } as any;
        entity.monitorCosmosRest = {
            type: Boolean,
            alias: 'monitorCosmosRest',
            default: null
        } as any;
        entity.prometheusUrl = {
            type: String,
            alias: 'prometheusUrl',
            default: null
        } as any;
        entity.exporterUrl = {
            type: String,
            alias: 'exporterUrl',
            default: null
        } as any;
        entity.monitorSystem = {
            type: Boolean,
            alias: 'monitorSystem',
            default: null
        } as any;
        entity.isValidator = {
            type: Boolean,
            alias: 'isValidator',
            default: null
        } as any;
        entity.isArchiveNode = {
            type: Boolean,
            alias: 'isArchiveNode',
            default: null
        } as any;
        entity.useAsDataSource = {
            type: Boolean,
            alias: 'useAsDataSource',
            default: null
        } as any;
        entity.monitorNetwork = {
            type: Boolean,
            alias: 'monitorNetwork',
            default: null
        } as any;
        entity.operatorAddress = {
            type: String,
            alias: 'operatorAddress',
            default: null
        } as any;
        entity.monitorTendermintRpc = {
            type: Boolean,
            alias: 'monitorTendermintRpc',
            default: null
        } as any;
        entity.tendermintRpcUrl = {
            type: String,
            alias: 'tendermintRpcUrl',
            default: null
        } as any;
        entity.nodeWsUrl = {
            type: String,
            alias: 'nodeWsUrl',
            default: null
        } as any;
        entity.stashAddress = {
            type: String,
            alias: 'stashAddress',
            default: null
        } as any;
        entity.governanceAddresses = {
            type: String,
            alias: 'governanceAddresses',
            default: null
        } as any;

        const obj = Object.assign(entity, new BaseMongoose());
        this._schema = new Schema(ObjectUtil.camelToSnake<object>(obj),
            {versionKey: false});

        MongooseUtil.virtualize(this._schema);
    }

    public produceModel(): void {
        this._model = null;
    }

    public get model(): Model<NodeSubconfig> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}

import mongoose, {Model, Schema} from 'mongoose';
import {Config} from '../../../../entities/ts/Config';
import {Collection, ModelName} from '../../constant/mongoose';
import {MongooseUtil} from '../../util/MongooseUtil';
import {ObjectUtil} from '../../util/ObjectUtil';
import {BaseChainModel} from '../entity/model/BaseChainModel';
import {ContractSubconfigSchema} from '../entity/model/ContractSubconfigSchema';
import {EVMNodeSubconfigSchema} from '../entity/model/EVMNodeSubconfigSchema';
import {NodeSubconfigSchema} from '../entity/model/NodeSubconfigSchema';
import {RepositorySubconfigSchema} from '../entity/model/RepositorySubconfigSchema';
import {SeverityAlertSubconfigSchema} from '../entity/model/SeverityAlertSubconfigSchema';
import {SubChainSchema} from '../entity/model/SubChainSchema';
import {SystemSubconfigSchema} from '../entity/model/SystemSubconfigSchema';
import {ThresholdAlertSubconfigSchema} from '../entity/model/ThresholdAlertSubconfigSchema';
import {IModelBuilder} from './IModelBuilder';
import {TimeWindowAlertSubconfigSchema} from "../entity/model/TimeWindowAlertSubconfigSchema";
import {GenericRepository} from '../entity/repository/GenericRepository';
import {BaseChainRepository} from '../entity/repository/BaseChainRepository';
import {Base} from '../../../../entities/ts/Base';

/**
 * Builder to create Mongoose Schema and Model of Config Entity
 */
export class ConfigModelBuilder implements IModelBuilder<Config> {

    private _schema: Schema = null;
    private _model: Model<Config> = null;

    public produceSchema(): void {

        new BaseChainModel();

        const config = {} as Config;

        config['configType'] = {
            type: Schema.Types.ObjectId,
            ref: ModelName.GENERIC,
            validate: {
                validator: async (id: string) => {
                    const repo = new GenericRepository();
                    return await repo.exists(id);
                },
                message: props => `Reference with id ${props.value} doesn't exists`
            }
        } as any;
        config.status = Boolean as any;
        config.created = {
            type: Date,
            default: null
        } as any;
        config.modified = {
            type: Date,
            default: null
        } as any;
        config.ready = Boolean as any;
        config.baseChain = {
            type: Schema.Types.ObjectId,
            ref: ModelName.BASE_CHAIN,
            required: [true, 'Base chain is required!'],
            alias: 'baseChain',
            default: null,
            validate: {
                validator: async (id: string) => {
                    const repo = new BaseChainRepository();
                    return await repo.exists(id);
                },
                message: props => `Reference with id ${props.value} doesn't exists`
            }
        } as any;
        config.subChain = {
            type: SubChainSchema,
            required: [true, 'Sub chain is required!'],
            alias: 'subChain',
            default: null
        } as any;
        config.contract = {
            type: ContractSubconfigSchema,
            default: null
        } as any;
        config.nodes = {
            type: [NodeSubconfigSchema],
            validate: this.nameDuplicateValidator(),
        } as any;
        config.evm_nodes = {
            type: [EVMNodeSubconfigSchema],
            validate: this.nameDuplicateValidator(),
        } as any;
        config.systems = {
            type: [SystemSubconfigSchema],
            validate: this.nameDuplicateValidator(),
        } as any;
        config.repositories = {
            type: [RepositorySubconfigSchema],
            validate: this.nameDuplicateValidator(),
        } as any;
        config.thresholdAlerts = {
            type: [ThresholdAlertSubconfigSchema],
            alias: 'thresholdAlerts',
        } as any;
        config.severityAlerts = {
            type: [SeverityAlertSubconfigSchema],
            alias: 'severityAlerts',
        } as any;
        config.timeWindowAlerts = {
            type: [TimeWindowAlertSubconfigSchema],
            alias: 'timeWindowAlerts',
        } as any;

        this._schema = new Schema(
            ObjectUtil.camelToSnake<object>(config),
            {versionKey: false}
        );

        MongooseUtil.virtualize(this._schema);
    }

    public produceModel(): void {
        this._model = mongoose.model(
            ModelName.CONFIG,
            this._schema,
            Collection.CONFIG
        ) as Model<Config>;
    }

    public get model(): Model<Config> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }

    /**
     * Custom validator for arrays/lists by property name
     * @returns
     */
    private nameDuplicateValidator(): object {
        return {
            validator: async (list: Base[]) => {
                const uniques = new Set(list.map(item => item.name));
                return list.length === uniques.size;
            },
            message: 'Name duplicated'
        }
    }
}

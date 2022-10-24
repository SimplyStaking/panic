import {ObjectID} from "mongodb";
import mongoose from "mongoose";
import {Config} from "../../../../../entities/ts/Config";
import {GenericDocument, ModelName} from "../../../constant/mongoose";
import {ConfigModel} from "../model/ConfigModel";
import {AbstractRepository} from "./AbstractRepository";

/**
 * Implements specific operations for Config model in database
 */
export class ConfigRepository extends AbstractRepository<Config> {
    public constructor() {
        super(ConfigModel);
    }

    /**
     * Return a list of Config from database
     */
    public async findAll(): Promise<Array<Config>> {
        return this.model.find({
            config_type: new ObjectID(GenericDocument.CONFIG_TYPE_SUB_CHAIN)
        }).populate({path: 'base_chain', select: {'name': 1, 'value': 1}})
          .populate({path: 'repositories', populate: {path: 'type'}})
          .populate({path: 'severity_alerts', populate: {path: 'type'}});
    }

    /**
     * Return item Config from database by id
     *
     */
    public async findOneById(id: string): Promise<Config> {
        return this.model.findOne({
            _id: new ObjectID(id),
            config_type: new ObjectID(GenericDocument.CONFIG_TYPE_SUB_CHAIN)
        }).populate({path: 'base_chain', select: {'name': 1, 'value': 1}})
          .populate({path: 'repositories', populate: {path: 'type'}})
          .populate({path: 'severity_alerts', populate: {path: 'type'}});
    }

    /**
     * Return a list of Config from database by criteria
     *
     * @param criteria
     */
    public async findBy(criteria: object): Promise<Array<Config>> {
        criteria['config_type'] = new ObjectID(GenericDocument.CONFIG_TYPE_SUB_CHAIN);
        return this.model.find(criteria);
    }

    /**
     * Check if sub chain within the config already exists on Database
     *
     * @param config The config or request object
     * @returns true if sub chain name exists, otherwise false
     */
    public async isDuplicateSubChain(config: Config): Promise<Boolean> {

        const hasName = config && config.subChain && config.subChain.name;
        if (hasName) {

            const criteria = {
                'sub_chain.name': config.subChain.name
            }

            // for edit case, to ignore self register
            const isValidConfigID = 'id' in config && mongoose.Types.ObjectId.isValid(config.id);

            if (isValidConfigID) {
                criteria['_id'] = {'$ne': new ObjectID(config.id)};
            }

            const configs = await this.findBy(criteria);
            return configs && configs.length > 0;
        }

        return false;
    }
}

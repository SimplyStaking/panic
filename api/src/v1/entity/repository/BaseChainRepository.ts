import {ObjectID} from "mongodb";
import {BaseChain} from "../../../../../entities/ts/BaseChain";
import {BaseChainModel} from "../model/BaseChainModel";
import {AbstractRepository} from "./AbstractRepository";

/**
 * Implements specific operations for Base Chain model in database
 */
export class BaseChainRepository extends AbstractRepository<BaseChain> {
    public constructor() {
        super(BaseChainModel);
    }

    /**
     * Return item BaseChain from database by id and deep populate references
     *
     * @param id The mongo hash id
     * @param fieldsToPopulate reference fields to populate within document
     * @param populateObject object which contains information regarding deep 
     * population
     * @returns item BaseChain with populated references
     */
    public async findOneByIdAndDeepPopulate(
        id: string,
        fieldsToPopulate: string[],
        populateObject = null
    ): Promise<any> {
        const query = this.model.findOne({ _id: new ObjectID(id) })
            .populate(fieldsToPopulate);

        if (populateObject) {
            query.populate(populateObject);
        }

        return query;
    }
}

import {Generic} from "../../../../../entities/ts/Generic";
import {SeverityAlertSubconfig} from "../../../../../entities/ts/SeverityAlertSubconfig";
import {GenericModel} from "../model/GenericModel";
import {AbstractRepository} from "./AbstractRepository";
import {SeverityAlertSubconfigModel} from "../model/SeverityAlertSubconfigSchema";
import {ObjectID} from "mongodb";

/**
 * Implements specific operations for Generic Types model in database
 */
export class GenericRepository extends AbstractRepository<Generic> {
    public constructor() {
        super(GenericModel);
    }

    /**
     * Return a list of Generic types by group
     *
     * @param group The name of group that you want to filter
     */
    public async findByGroup(group: string): Promise<Generic[]> {
        return this.findBy({group: group});
    }

    /**
     * Return a list of Generic types by group and populate references
     *
     * @param group The name of group that you want to filter
     * @param fieldsToPopulate reference fields to populate within documents
     */
    public async findByGroupAndPopulate(group: string, fieldsToPopulate: string[]): Promise<Generic[]> {
        return this.findByAndPopulate({group: group}, fieldsToPopulate);
    }

    /**
     * Return a Generic type by group and ID
     *
     * @param group The name of group that you want to filter
     * @param id The mongo hash id
     */
    public async findOneByGroupAndId(group: string, id: string): Promise<Generic> {
        return this.findOneBy({group: group, _id: new ObjectID(id)});
    }
}

/**
 * Implements specific operations for SeverityAlertSubconfig model in database
 */
export class SeverityAlertSubconfigRepository extends AbstractRepository<SeverityAlertSubconfig> {
    public constructor() {
        super(SeverityAlertSubconfigModel);
    }

    /**
     * Return a list of Generic types by group and populate references
     *
     * @param group The name of group that you want to filter
     * @param fieldsToPopulate reference fields to populate within documents
     */
    public async findByGroupAndPopulate(group: string, fieldsToPopulate: string[]): Promise<SeverityAlertSubconfig[]> {
        return this.findByAndPopulate({group: group}, fieldsToPopulate);
    }
}

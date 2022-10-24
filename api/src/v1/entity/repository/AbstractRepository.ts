import {ObjectID} from 'mongodb';
import * as mongoose from 'mongoose';

/**
 * Implements generic operations to interact with database
 */
export class AbstractRepository<T> {

    public constructor(protected model: mongoose.Model<T>) {
    }

    /**
     * Return a list of <T> from database
     *
     * @returns an array of items <T>
     */
    public async findAll(): Promise<Array<T>> {
        return this.model.find();
    }

    /**
     * Return a list of <T> from database by id and deep populate references
     *
     * @param fieldsToPopulate reference fields to populate within document
     * @param populateObject object which contains information regarding deep population
     * @returns an array of items <T> with populated references
     */
    public async findAllAndDeepPopulate(fieldsToPopulate: string[], populateObject): Promise<Array<T>> {
        return this.model.find().populate(fieldsToPopulate).populate(populateObject);
    }

    /**
     * Return a list of <T> from database by criteria
     *
     * @param criteria
     * @returns an array of items <T>
     */
    public async findBy(criteria: object): Promise<Array<T>> {
        return this.model.find(criteria);
    }

    /**
     * Return a list of <T> from database by criteria
     *
     * @param criteria
     * @param fieldsToPopulate reference fields to populate within documents
     */
    public async findByAndPopulate(criteria: object, fieldsToPopulate: string[]): Promise<Array<T>> {
        return this.model.find(criteria).populate(fieldsToPopulate);
    }

    /**
     * Return item <T> from database by id
     *
     * @param id The mongo hash id
     * Return item <T>
     *
     */
    public async findOneById(id: string): Promise<T> {
        return this.model.findOne({_id: new ObjectID(id)});
    }

    /**
     * Return <T> from database by criteria
     *
     * @param criteria
     * @returns an item <T>
     */
    public async findOneBy(criteria: object): Promise<T> {
        return this.model.findOne(criteria);
    }    

    /**
     * Return true if document exists
     *
     * @param id The mongo hash id
     * @returns true if document exists, false otherwise
     */
    public async exists(id: string): Promise<boolean> {
        const result = await this.model.find({_id: id}).countDocuments();
        return result > 0;
    }

    /**
     * Deletes an item <T> from database by id
     *
     * @param id The mongo hash id
     * @returns true if document was deleted
     */
    public async deleteOneById(id: string): Promise<boolean> {
        const result = await this.model.deleteOne({_id: new ObjectID(id)});
        return result.deletedCount === 1;
    }
}

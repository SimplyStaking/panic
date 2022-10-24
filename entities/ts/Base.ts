import {AbstractEntity} from "./AbstractEntity";

/**
 * Abstract Base Entity Class for Config, Subconfig, Generic and Basechain.
 */
export abstract class Base extends AbstractEntity {

    private _id: string = null;
    private _status: boolean = null;
    private _created: Date = null;
    private _modified: Date = null;
    private _name: string = null;

    public constructor() {
        super();
        this._created = new Date();
    }

    /**
     * A Document MongoId as hash string
     * @type string
     */
    public get id(): string {
        return this._id;
    }

    /**
     * A Document Status, if false mean that document was removed
     * @type boolean
     */
    public get status(): boolean {
        return this._status;
    }

    /**
     * Created date as a string value in ISO format
     * @type Date
     */
    public get created(): Date {
        return this._created;
    }

    /**
     * Modified date as a string value in ISO format
     * @type Date
     */
    public get modified(): Date {
        return this._modified;
    }

    /**
     * Name/Alias of document
     * @type string
     */
    public get name(): string {
        return this._name;
    }


    public set status(status: boolean) {
        this._status = status;
    }

    public set created(created: Date) {
        this._created = created;
    }

    public set modified(modified: Date) {
        this._modified = modified;
    }

    public set name(name: string) {
        this._name = name;
    }

    /**
     * Returns all getters in JSON format
     * @param excludeFields List of fields to exclude
     *
     * @returns JSON object
     */
    public toJSON(excludeFields: string[] = []): object {
        const json = {
            id: this.id,
            status: this.status,
            created: this.created,
            modified: this.modified,
            name: this.name
        }

        excludeFields.forEach(x => {
            delete json[x];
        });

        return json;
    }
}

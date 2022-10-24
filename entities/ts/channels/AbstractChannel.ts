import {ChannelType} from '../ChannelType';
import {EmailChannel} from "./EmailChannel";
import {OpsgenieChannel} from "./OpsgenieChannel";
import {PagerDutyChannel} from "./PagerDutyChannel";
import {SlackChannel} from "./SlackChannel";
import {TelegramChannel} from "./TelegramChannel";
import {TwilioChannel} from "./TwilioChannel";
import {Config} from "../Config";
import {AbstractEntity} from "../AbstractEntity";

export type Channel = (
    EmailChannel | OpsgenieChannel | PagerDutyChannel |
    SlackChannel | TelegramChannel | TwilioChannel);

/**
 * AbstractChannel Entity Class for Config
 */
export abstract class AbstractChannel extends AbstractEntity{

    private _id: string = null;
    private _created: Date = null;
    private _modified: Date = null;
    private _name: string = null;
    private _type: ChannelType = null;
    private _configs: Array<Config> = [];

    protected constructor() {
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
     * Name of channel
     * @type string
     */
    public get name(): string {
        return this._name;
    }

    /**
     * Type of AbstractChannel
     * @type ChannelType
     */
    public get type(): ChannelType {
        return this._type;
    }

    /**
     * List of configurations enabled to this channel
     * @type string
     */
    public get configs(): Array<Config> {
        return this._configs;
    }

    public set id(value: string) {
        this._id = value;
    }

    public set name(value: string) {
        this._name = value;
    }

    public set type(value: ChannelType) {
        this._type = value;
    }

    public set configs(value: Array<Config>) {
        this._configs = value;
    }

    public set created(value: Date) {
        this._created = value;
    }

    public set modified(value: Date) {
        this._modified = value;
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
            created: this.created,
            modified: this.modified,
            name: this.name,
            type: this.type && typeof this.type === 'object' ? this.type.toJSON(excludeFields) : this.type,
            configs: this.configs.map((config) => config.id)
        }

        if (excludeFields)
            excludeFields.forEach(x => {
                delete json[x];
            });

        return json;
    }
}

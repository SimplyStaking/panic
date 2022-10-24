import {StringUtil} from "../../../util/StringUtil";

/**
 * Mongoose Base Model Class for Config, Subconfig, Generic and Basechain Models
 */
export class BaseMongoose {

    public status;
    public created;
    public modified;
    public name;

    public constructor() {
        this.status = {type: Boolean, default: true} as any;
        this.created = {type: Date, default: Date.now} as any;
        this.modified = {type: Date, default: null} as any;
        this.name = {
            type: String,
            required: [true, 'Name is required!'],
            default: null,
            set: StringUtil.trim
        } as any;
    }
}

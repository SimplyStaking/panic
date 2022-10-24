import { Base } from "./Base";

/**
 * Abstract Generic Entity Class
 */
export abstract class Generic extends Base {

    private _value: string = null;
    private _description: string = null;
    private _group: string = null;

    constructor() {
        super();
    }

    /**
     * Virtual value of Document
     * @type string
     */
    public get value(): string {
        return this._value;
    }

    /**
     * Full description of Document
     * @type string
     */
    public get description(): string {
        return this._description;
    }

    /**
     * Group reference
     * @type boolean
     */
    public get group(): string {
        return this._group;
    }

    public set value(value: string) {
        this._value = value;
    }

    public set description(value: string) {
        this._description = value;
    }

    public set group(value: string) {
        this._group = value;
    }

    /**
     * Returns all getters in JSON format
     * @param excludeFields List of fields to exclude
     *
     * @returns JSON object
     */
    public toJSON(excludeFields: string[] = []): object {

        const json = {
            ...super.toJSON(excludeFields),
            value: this.value,
            description: this.description,
            group: this.group
        }

        if (excludeFields)
            excludeFields.forEach(x => {
                delete json[x];
            });

        return json;
    }
}

import { Base } from './Base';
import { RepositoryType } from './RepositoryType';

/**
 * RepositorySubconfig Entity Class
 */
export class RepositorySubconfig extends Base {

    private _monitor: boolean = null;
    private _value: string = null;
    private _namespace: string = null;
    private _type: RepositoryType = null;

    /**
     * Node Monitor flag
     * @type boolean
     */
    public get monitor(): boolean {
        return this._monitor;
    }

    /**
     * Value
     * @type string
     */
    public get value(): string {
        return this._value;
    }

    /**
     * Namespace
     * @type string
     */
    public get namespace(): string {
        return this._namespace;
    }

    /**
     * Generic reference for Repository Type
     * @type string
     */
    public get type(): RepositoryType {
        return this._type;
    }

    public set monitor(value: boolean) {
        this._monitor = value;
    }

    public set value(value: string) {
        this._value = value;
    }

    public set namespace(value: string) {
        this._namespace = value;
    }

    public set type(value: RepositoryType) {
        this._type = value;
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
            monitor: this.monitor,
            value: this.value,
            namespace: this.namespace,
            type: this.type ? this.type.toJSON(excludeFields) : null
        }

        if (excludeFields)
            excludeFields.forEach(x => {
                delete json[x];
            });

        return json;
    }
}

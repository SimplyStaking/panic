import {SeverityType} from './SeverityType';
import {Generic} from "./Generic";

/**
 * SeverityAlertSubconfig Entity Class
 */
export class SeverityAlertSubconfig extends Generic{

    private _type: SeverityType = null;
    private _enabled: boolean = null;

    constructor() {
        super();
    }

    /**
     * Generic reference for Severity Type
     * @type SeverityType
     */
    public get type(): SeverityType {
        return this._type;
    }

    public set type(value: SeverityType) {
        this._type = value;
    }

    public get enabled(): boolean {
        return this._enabled;
    }

    public set enabled(value: boolean) {
        this._enabled = value;
    }
}

import {Generic} from "./Generic";
import {ICriticalThresholdSeverity, IWarningThresholdSeverity} from "./ThresholdAlertSubconfig";

interface IWarningTimeWindowThresholdSeverity extends IWarningThresholdSeverity{
    timeWindow: number
}

interface ICriticalTimeWindowThresholdSeverity extends ICriticalThresholdSeverity{
    timeWindow: number
}

/**
 * TimeWindowAlertSubconfig Class for Config
 */
export class TimeWindowAlertSubconfig extends Generic{

    private _warning: IWarningTimeWindowThresholdSeverity = null;
    private _critical: ICriticalTimeWindowThresholdSeverity = null;
    private _adornment: string = null;
    private _enabled: boolean = null;

    constructor() {
        super();
    }

    /**
     * Warning time window threshold severity info
     * @type IWarningTimeWindowThresholdSeverity
     */
    public get warning(): IWarningTimeWindowThresholdSeverity {
        return this._warning;
    }

    /**
     * Critical time window threshold severity info
     * @type ICriticalTimeWindowThresholdSeverity
     */
    public get critical(): ICriticalTimeWindowThresholdSeverity {
        return this._critical;
    }

    /**
     * Adornment type
     * @type string
     */
    public get adornment(): string {
        return this._adornment;
    }

    /**
     * Whether enabled
     * @type boolean
     */
    public get enabled(): boolean {
        return this._enabled;
    }

    public set warning(value: IWarningTimeWindowThresholdSeverity) {
        this._warning = value;
    }

    public set critical(value: ICriticalTimeWindowThresholdSeverity) {
        this._critical = value;
    }

    public set adornment(value: string) {
        this._adornment = value;
    }

    public set enabled(value: boolean) {
        this._enabled = value;
    }
}

import {Generic} from "./Generic";

export interface IWarningThresholdSeverity {
    enabled: boolean,
    threshold: number
}

export interface ICriticalThresholdSeverity {
    enabled: boolean,
    repeatEnabled: boolean,
    threshold: number,
    repeat: number
}

/**
 * ThresholdAlertSubconfig Class for Config
 */
export class ThresholdAlertSubconfig extends Generic{

    private _warning: IWarningThresholdSeverity = null;
    private _critical: ICriticalThresholdSeverity = null;
    private _adornment: string = null;
    private _enabled: boolean = null;

    constructor() {
        super();
    }

    /**
     * Warning threshold severity info
     * @type IWarningThresholdSeverity
     */
    public get warning(): IWarningThresholdSeverity {
        return this._warning;
    }

    /**
     * Critical threshold severity info
     * @type ICriticalThresholdSeverity
     */
    public get critical(): ICriticalThresholdSeverity {
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

    public set warning(value: IWarningThresholdSeverity) {
        this._warning = value;
    }

    public set critical(value: ICriticalThresholdSeverity) {
        this._critical = value;
    }

    public set adornment(value: string) {
        this._adornment = value;
    }

    public set enabled(value: boolean) {
        this._enabled = value;
    }
}

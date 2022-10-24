import {Base} from './Base';
import {SourceType} from './SourceType';
import {ThresholdAlertSubconfig} from "./ThresholdAlertSubconfig";
import {SeverityAlertSubconfig} from "./SeverityAlertSubconfig";
import {TimeWindowAlertSubconfig} from "./TimeWindowAlertSubconfig";

/**
 * Base Chain Entity Class for Config
 */
export class BaseChain extends Base {

    private _value: string = null;
    private _sources: Array<SourceType> = [];
    private _thresholdAlerts: Array<ThresholdAlertSubconfig> = [];
    private _severityAlerts: Array<SeverityAlertSubconfig> = [];
    private _timeWindowAlerts: Array<TimeWindowAlertSubconfig> = [];

    /**
     * Virtual value of Document
     * @type string
     */
    public get value(): string {
        return this._value;
    }

    /**
     * List of sources enabled to this base chain
     */
    public get sources(): Array<SourceType> {
        return this._sources;
    }

    /**
     * List of threshold alerts configured
     * @type Array<ThresholdAlertSubconfig>
     */
    public get thresholdAlerts(): Array<ThresholdAlertSubconfig> {
        return this._thresholdAlerts;
    }

    /**
     * List of severity alerts configured
     * @type Array<SeverityAlertSubconfig>
     */
    public get severityAlerts(): Array<SeverityAlertSubconfig> {
        return this._severityAlerts;
    }

    /**
     * List of time window alerts configured
     * @type Array<TimeWindowAlertSubconfig>
     */
    public get timeWindowAlerts(): Array<TimeWindowAlertSubconfig> {
        return this._timeWindowAlerts;
    }

    public set value(value: string) {
        this._value = value;
    }

    public set sources(sources: Array<SourceType>) {
        this._sources = sources;
    }

    public set thresholdAlerts(value: Array<ThresholdAlertSubconfig>) {
        this._thresholdAlerts = value;
    }

    public set severityAlerts(value: Array<SeverityAlertSubconfig>) {
        this._severityAlerts = value;
    }

    public set timeWindowAlerts(value: Array<TimeWindowAlertSubconfig>) {
        this._timeWindowAlerts = value;
    }

    /**
     * Add new source to sources list
     *
     * @param source Source that you want to add
     * @returns A instance of current BaseChain
     */
    public addSources(source: SourceType): BaseChain {
        this._sources.push(source);
        return this;
    }
}

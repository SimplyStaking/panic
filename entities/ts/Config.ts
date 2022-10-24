import {AbstractEntity} from "./AbstractEntity";
import {BaseChain} from './BaseChain';
import {ContractSubconfig} from './ContractSubconfig';
import {EVMNodeSubconfig} from './EVMNodeSubconfig';
import {NodeSubconfig} from './NodeSubconfig';
import {RepositorySubconfig} from './RepositorySubconfig';
import {SeverityAlertSubconfig} from './SeverityAlertSubconfig';
import {SubChain} from './SubChain';
import {SystemSubconfig} from './SystemSubconfig';
import {ThresholdAlertSubconfig} from './ThresholdAlertSubconfig';
import {TimeWindowAlertSubconfig} from "./TimeWindowAlertSubconfig";

/**
 * Basechain Class for Config.
 * @link https://wiki.simply-vc.com.mt/display/PT/PANIC+API+-+Entities%2C+Persistence+and+Endpoints
 */
export class Config extends AbstractEntity{

    private _id: string = null;
    private _status: boolean = true;
    private _ready: boolean = false;
    private _created: Date = null;
    private _modified: Date = null;
    private _baseChain: BaseChain = null;
    private _subChain: SubChain = null;

    private _contract: ContractSubconfig = null;
    private _nodes: Array<NodeSubconfig> = [];
    private _evm_nodes: Array<EVMNodeSubconfig> = [];
    private _systems: Array<SystemSubconfig> = [];
    private _repositories: Array<RepositorySubconfig> = [];

    private _thresholdAlerts: Array<ThresholdAlertSubconfig> = [];
    private _severityAlerts: Array<SeverityAlertSubconfig> = [];
    private _timeWindowAlerts: Array<TimeWindowAlertSubconfig> = [];

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
     * A configuration is ready if the UI informs the API that installation
     * procedure is done
     * @type boolean
     */
    public get ready(): boolean {
        return this._ready;
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
     * Base chain info
     * @type BaseChain
     */
    public get baseChain(): BaseChain {
        return this._baseChain;
    }

    /**
     * Sub chain info
     * @type SubChain
     */
    public get subChain(): SubChain {
        return this._subChain;
    }

    /**
     * Contract info
     * @type ContractSubconfig
     */
    public get contract(): ContractSubconfig {
        return this._contract;
    }

    /**
     * List of nodes configured
     * @type Array<NodeSubconfig>
     */
    public get nodes(): Array<NodeSubconfig> {
        return this._nodes;
    }

    /**
     * List of evm nodes configured
     * @type Array<EVMNodeSubconfig>
     */
    public get evm_nodes(): Array<EVMNodeSubconfig> {
        return this._evm_nodes;
    }

    /**
     * List of systems configured
     * @type Array<SystemSubconfig>
     */
    public get systems(): Array<SystemSubconfig> {
        return this._systems;
    }

    /**
     * List of repositories configured
     * @type Array<RepositorySubconfig>
     */
    public get repositories(): Array<RepositorySubconfig> {
        return this._repositories;
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

    public set id(value: string) {
        this._id = value;
    }

    public set status(value: boolean) {
        this._status = value;
    }

    public set ready(value: boolean) {
        this._ready = value;
    }

    public set created(value: Date) {
        this._created = value;
    }

    public set modified(value: Date) {
        this._modified = value;
    }

    public set baseChain(value: BaseChain) {
        this._baseChain = value;
    }

    public set subChain(value: SubChain) {
        this._subChain = value;
    }

    public set contract(value: ContractSubconfig) {
        this._contract = value;
    }

    public set nodes(value: Array<NodeSubconfig>) {
        this._nodes = value;
    }

    public set evm_nodes(value: Array<EVMNodeSubconfig>) {
        this._evm_nodes = value;
    }

    public set systems(value: Array<SystemSubconfig>) {
        this._systems = value;
    }

    public set repositories(value: Array<RepositorySubconfig>) {
        this._repositories = value;
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
     * Returns all getters in JSON format
     * @param excludeFields List of fields to exclude
     *
     * @returns JSON object
     */
    public toJSON(excludeFields: string[] = []): object {

        const json = {
            id: this.id,
            status: this.status,
            ready: this.ready,
            created: this.created,
            modified: this.modified,
            baseChain: this.baseChain,
            subChain: this.subChain,
            contract: this.contract,
            nodes: this.nodes,
            evm_nodes: this.evm_nodes,
            systems: this.systems,
            repositories: this.repositories,
            thresholdAlerts: this.thresholdAlerts,
            severityAlerts: this.severityAlerts,
            timeWindowAlerts: this.timeWindowAlerts
        }

        if (excludeFields)
            excludeFields.forEach(x => {
                delete json[x];
            });

        return json;
    }
}

import { Base } from './Base';

/**
 * NodeSubconfig Class for Macro Config
 */
export class NodeSubconfig extends Base {

    private _nodePrometheusUrls: string = null;
    private _monitorPrometheus: boolean = null;
    private _monitorNode: boolean = null;
    private _evmNodesUrls: string = null;
    private _weiwatchersUrl: string = null;
    private _monitorContracts: boolean = null;
    private _cosmosRestUrl: string = null;
    private _monitorCosmosRest: boolean = null;
    private _prometheusUrl: string = null;
    private _exporterUrl: string = null;
    private _monitorSystem: boolean = null;
    private _isValidator: boolean = null;
    private _isArchiveNode: boolean = null;
    private _useAsDataSource: boolean = null;
    private _monitorNetwork: boolean = null;
    private _operatorAddress: string = null;
    private _monitorTendermintRpc: boolean = null;
    private _tendermintRpcUrl: string = null;
    private _nodeWsUrl: string = null;
    private _stashAddress: string = null;
    private _governanceAddresses: string = null;

    /**
     * URLs (separeted by comma) for node Prometheus
     * @type string
     */
    public get nodePrometheusUrls(): string {
        return this._nodePrometheusUrls;
    }

    /**
     * Prometheus Monitor flag
     * @type boolean
     */
    public get monitorPrometheus(): boolean {
        return this._monitorPrometheus;
    }

    /**
     * Node Monitor flag
     * @type boolean
     */
    public get monitorNode(): boolean {
        return this._monitorNode;
    }

    /**
     * URLs (separeted by comma) for EVM node
     * @type string
     */
    public get evmNodesUrls(): string {
        return this._evmNodesUrls;
    }

    /**
     * URLs (separeted by comma) for weiwatchers
     * @type string
     */
    public get weiwatchersUrl(): string {
        return this._weiwatchersUrl;
    }

    /**
     * Contract Monitor flag
     * @type boolean
     */
    public get monitorContracts(): boolean {
        return this._monitorContracts;
    }

    /**
     * REST URLs (separeted by comma) for cosmos
     * @type string
     */
    public get cosmosRestUrl(): string {
        return this._cosmosRestUrl;
    }

    /**
     * REST Cosmos Monitor flag
     * @type boolean
     */
    public get monitorCosmosRest(): boolean {
        return this._monitorCosmosRest;
    }

    /**
     * URLs (separeted by comma) for prometheus
     * @type string
     */
    public get prometheusUrl(): string {
        return this._prometheusUrl;
    }

    /**
     * URLs (separeted by comma) for exporter
     * @type string
     */
    public get exporterUrl(): string {
        return this._exporterUrl;
    }

    /**
     * Monitor System flag
     * @type boolean
     */
    public get monitorSystem(): boolean {
        return this._monitorSystem;
    }

    /**
     * Validator flag
     * @type boolean
     */
    public get isValidator(): boolean {
        return this._isValidator;
    }

    /**
     * Archive Node flag
     * @type boolean
     */
    public get isArchiveNode(): boolean {
        return this._isArchiveNode;
    }

    /**
     * Data Source flag
     * @type boolean
     */
    public get useAsDataSource(): boolean {
        return this._useAsDataSource;
    }

    /**
     * Monitor Network flag
     * @type boolean
     */
    public get monitorNetwork(): boolean {
        return this._monitorNetwork;
    }

    /**
     * Operator addesses (separeted by comma)
     * @type string
     */
    public get operatorAddress(): string {
        return this._operatorAddress;
    }

    /**
     * Monitor Tendermint RPC flag
     * @type boolean
     */
    public get monitorTendermintRpc(): boolean {
        return this._monitorTendermintRpc;
    }

    /**
     * URLs (separeted by comma) for Tendermint RPC
     * @type string
     */
    public get tendermintRpcUrl(): string {
        return this._tendermintRpcUrl;
    }

    /**
     * URLs (separeted by comma) for Node WS
     * @type string
     */
    public get nodeWsUrl(): string {
        return this._nodeWsUrl;
    }

    /**
     * Stash addesses (separeted by comma)
     * @type string
     */
    public get stashAddress(): string {
        return this._stashAddress;
    }

    /**
     * Governance Addresses (separeted by comma) for Substrate
     * @type string
     */
    public get governanceAddresses(): string {
        return this._governanceAddresses;
    }

    public set nodePrometheusUrls(value: string) {
        this._nodePrometheusUrls = value;
    }

    public set monitorPrometheus(value: boolean) {
        this._monitorPrometheus = value;
    }

    public set monitorNode(value: boolean) {
        this._monitorNode = value;
    }

    public set evmNodesUrls(value: string) {
        this._evmNodesUrls = value;
    }

    public set weiwatchersUrl(value: string) {
        this._weiwatchersUrl = value;
    }

    public set monitorContracts(value: boolean) {
        this._monitorContracts = value;
    }

    public set cosmosRestUrl(value: string) {
        this._cosmosRestUrl = value;
    }

    public set monitorCosmosRest(value: boolean) {
        this._monitorCosmosRest = value;
    }

    public set prometheusUrl(value: string) {
        this._prometheusUrl = value;
    }

    public set exporterUrl(value: string) {
        this._exporterUrl = value;
    }

    public set monitorSystem(value: boolean) {
        this._monitorSystem = value;
    }

    public set isValidator(value: boolean) {
        this._isValidator = value;
    }

    public set isArchiveNode(value: boolean) {
        this._isArchiveNode = value;
    }

    public set useAsDataSource(value: boolean) {
        this._useAsDataSource = value;
    }

    public set monitorNetwork(value: boolean) {
        this._monitorNetwork = value;
    }

    public set operatorAddress(value: string) {
        this._operatorAddress = value;
    }

    public set monitorTendermintRpc(value: boolean) {
        this._monitorTendermintRpc = value;
    }

    public set tendermintRpcUrl(value: string) {
        this._tendermintRpcUrl = value;
    }

    public set nodeWsUrl(value: string) {
        this._nodeWsUrl = value;
    }

    public set stashAddress(value: string) {
        this._stashAddress = value;
    }

    public set governanceAddresses(value: string) {
        this._governanceAddresses = value;
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
            nodePrometheusUrls: this.nodePrometheusUrls,
            monitorPrometheus: this.monitorPrometheus,
            monitorNode: this.monitorNode,
            evmNodesUrls: this.evmNodesUrls,
            weiwatchersUrl: this.weiwatchersUrl,
            monitorContracts: this.monitorContracts,
            cosmosRestUrl: this.cosmosRestUrl,
            monitorCosmosRest: this.monitorCosmosRest,
            prometheusUrl: this.prometheusUrl,
            exporterUrl: this.exporterUrl,
            monitorSystem: this.monitorSystem,
            isValidator: this.isValidator,
            isArchiveNode: this.isArchiveNode,
            useAsDataSource: this.useAsDataSource,
            monitorNetwork: this.monitorNetwork,
            operatorAddress: this.operatorAddress,
            monitorTendermintRpc: this.monitorTendermintRpc,
            tendermintRpcUrl: this.tendermintRpcUrl,
            nodeWsUrl: this.nodeWsUrl,
            stashAddress: this.stashAddress,
            governanceAddresses: this.governanceAddresses
        }

        if (excludeFields)
            excludeFields.forEach(x => {
                delete json[x];
            });

        return json;
    }
}

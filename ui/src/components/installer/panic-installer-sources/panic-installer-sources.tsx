import {dismissModal} from "@simply-vc/uikit";
import {Component, h, Host, Listen, Prop, State} from "@stencil/core";
import {ConfigService} from "../../../services/config/config.service";
import {BaseChainService} from "../../../services/base-chain/base-chain.service";
import {HelperAPI} from "../../../utils/helpers";
import {Config} from "../../../../../entities/ts/Config";
import {SourceType} from "../../../../../entities/ts/SourceType";
import {NodeSubconfig} from "../../../../../entities/ts/NodeSubconfig";
import {EVMNodeSubconfig} from "../../../../../entities/ts/EVMNodeSubconfig";
import {ContractSubconfig} from "../../../../../entities/ts/ContractSubconfig";
import {SystemSubconfig} from "../../../../../entities/ts/SystemSubconfig";
import {BaseChain} from "../../../../../entities/ts/BaseChain";
import {Router} from "stencil-router-v2";

export type Sources = NodeSubconfig | EVMNodeSubconfig | SystemSubconfig;

@Component({
    tag: 'panic-installer-sources',
    styleUrl: 'panic-installer-sources.scss'
})
export class PanicInstallerSources {

    /**
     * The identifier used to represent the Config.
     */
    @Prop() configId: string;

    /**
     * Stencil Router object for page navigation.
     */
    @Prop() router: Router;

    /**
     * List containing the Generic Source Types.
     */
    @Prop() sourceTypes: SourceType[];

    /**
     * The Config object being read & modified.
     */
    @State() config: Config;

    /**
     * The Config object being read.
     */
    @State() baseChain: BaseChain;

    /**
     * Whether to monitor network (cosmos and substrate nodes).
     */
    @State() monitorNetwork: boolean = true;

    /**
     * Governance addresses (substrate nodes).
     */
    @State() governanceAddresses: string = '';

    /**
     * Listens to an event for when a new source is added via a source form modal.
     * @param event The event sent by one of the source form modals.
     */
    @Listen("save", {target: "window"})
    async saveHandler(event: CustomEvent) {
        const sourceTypeValue: string = event.detail.type;
        const source: Sources = event.detail.source;
        await this.save(source, sourceTypeValue);
    }

    /**
     * Attempt to save a given source into the database. An error is raised if source has a duplicate name.
     * @param source The source to be saved.
     * @param sourceTypeValue The value of the source type.
     */
    async save(source: Sources, sourceTypeValue: string): Promise<void> {
        let sources: Sources[] = this.config[sourceTypeValue];

        // updating = removing then adding
        if (source.id) {
            sources = this.remove(sources, source);
            sources.push(source);
        } else {
            sources.push(source);
        }
        this.config[sourceTypeValue] = [...sources];

        const resp: Response = await this.saveSourcesInConfig(sourceTypeValue);

        if(HelperAPI.isDuplicateName(resp)) {
            HelperAPI.raiseToast(
                `A source named '${source.name}' already exists!`,
                2000,
                "warning");
            sources.pop();
            this.config[sourceTypeValue] = [...sources];
        } else {
            await this.getDataFromAPI();
            HelperAPI.raiseToast("Source saved.");
            await dismissModal();
        }
    }

    /**
     * Remove a given source from an array of sources.
     * @param sources Array of sources to remove the source from.
     * @param sourceToRemove The source to be removed.
     *
     * @returns array of sources with the removed source.
     */
    remove(sources: Sources[], sourceToRemove: Sources): Sources[] {
        sources = sources.filter((n) => {
            return n.id !== sourceToRemove.id;
        });

        return [...sources];
    }

    /**
     * Listens to an event sent from the alert created when a delete button is pressed.
     * @param event The event sent by the delete source alert.
     */
    @Listen("deleteSource", {target: "window"})
    async deleteHandler(event: CustomEvent) {
        if (event.detail.confirmed) {
            const sourceTypeValue: string = event.detail.data.type;
            const sourceToDelete = this.config[sourceTypeValue].find((source) => source.id === event.detail.data.id);
            this.config[sourceTypeValue] = this.config[sourceTypeValue].filter(item => item !== sourceToDelete);

            await this.saveSourcesInConfig(sourceTypeValue);

            await this.getDataFromAPI();
            HelperAPI.raiseToast("Source deleted.");
            await dismissModal();
        }
    }

    /**
     * Listens to an event sent from the `panic-installer-sources-contract` component when contact
     * data has been updated. This is required to populate nodes and reload data.
     * @param event The event sent by the `panic-installer-sources-contract` component.
     */
    @Listen("updateContract", {target: "window"})
    async updateContractHandler(event: CustomEvent) {
        this.config.contract = event.detail;

        let toastText = 'Contract monitoring {status}';
        if(this.config.contract['monitor']){
            toastText = toastText.replace('{status}', 'enabled.');
        } else {
            toastText = toastText.replace('{status}', 'disabled.');
        }

        await this.saveSourcesInConfig('contract');
        await this.saveSourcesInConfig('nodes');

        HelperAPI.raiseToast(toastText);
    }

    /**
     * Save the list of sources within the config object via the API.
     */
    async saveSourcesInConfig(sourceTypeValue: string): Promise<Response>{
        const requestBody = this.createSourcesRequestBody(sourceTypeValue) as Config;

        return await ConfigService.getInstance().save(requestBody);
    }

    /**
     * Generates a request body to be sent via API.
     * @returns a request object containing the config id and the parsed arrays
     * of sources to be sent via the API.
     */
    createSourcesRequestBody(sourceTypeValue: string): object{
        let sources = [];

        switch (sourceTypeValue) {
            case 'nodes':
                sources = this.config.nodes.map(node => {
                    return {
                        id: node.id,
                        name: node.name,
                        nodePrometheusUrls: node.nodePrometheusUrls,
                        monitorPrometheus: HelperAPI.isTruthy(node.monitorPrometheus),
                        monitorNode: HelperAPI.isTruthy(node.monitorNode),
                        evmNodesUrls: node.evmNodesUrls,
                        weiwatchersUrl: this.config.contract?.url,
                        monitorContracts: HelperAPI.isTruthy(this.config.contract?.monitor),
                        cosmosRestUrl: node.cosmosRestUrl,
                        monitorCosmosRest: HelperAPI.isTruthy(node.monitorCosmosRest),
                        prometheusUrl: node.prometheusUrl,
                        exporterUrl: node.exporterUrl,
                        monitorSystem: HelperAPI.isTruthy(node.monitorSystem),
                        isValidator: HelperAPI.isTruthy(node.isValidator),
                        isArchiveNode: HelperAPI.isTruthy(node.isArchiveNode),
                        useAsDataSource: HelperAPI.isTruthy(node.useAsDataSource),
                        monitorNetwork: this.monitorNetwork,
                        operatorAddress: node.operatorAddress,
                        monitorTendermintRpc: HelperAPI.isTruthy(node.monitorTendermintRpc),
                        tendermintRpcUrl: node.tendermintRpcUrl,
                        nodeWsUrl: node.nodeWsUrl,
                        stashAddress: node.stashAddress,
                        governanceAddresses: this.governanceAddresses
                    }
                });
                break;
            case 'systems':
                sources = this.config.systems.map(system => {
                    return {
                        id: system.id,
                        name: system.name,
                        monitor: HelperAPI.isTruthy(system.monitor),
                        exporterUrl: system.exporterUrl
                    }
                });
                break;
            case 'evm_nodes':
                sources = this.config.evm_nodes.map(evm_node => {
                    return {
                        id: evm_node.id,
                        name: evm_node.name,
                        nodeHttpUrl: evm_node.nodeHttpUrl,
                        monitor: HelperAPI.isTruthy(evm_node.monitor)
                    }
                });
                break;
            case 'contract':
                const contractSource = {
                    id: this.config.contract.id,
                    name: this.config.contract.name,
                    url: this.config.contract.url,
                    monitor: HelperAPI.isTruthy(this.config.contract.monitor)
                };

                if(!contractSource.id){
                    delete contractSource.id;
                }

                return {
                    id: this.config.id,
                    [sourceTypeValue]: contractSource
                };
        }

        sources.forEach(source=>{
            if(!source.id){
                delete source.id;
            }
        })

        return {
            id: this.config.id,
            [sourceTypeValue]: sources
        };
    }

    /**
     * Listens to an event sent from the sources data table when a user ticks the enable checkbox.
     * @param event The event sent from panic-installer-sources-card.
     */
    @Listen("enableSource", {target: "window"})
    async enableSourceHandler(event: CustomEvent) {
        const id = event.detail.id;
        const sourceType: SourceType = event.detail.sourceType;
        const sourceListIndex: string = sourceType.value;
        const source = this.findSourceByID(this.config[sourceListIndex], id);
        const monitoringFieldName: string = event.detail.monitoringFieldName;

        source[monitoringFieldName] = !source[monitoringFieldName];

        await this.save(source, sourceType.value);
    }

    /**
     * Finds a source from a list of sources by id.
     * @param sources The list of sources to search from.
     * @param id The id of the source to search.
     *
     * @returns a source if found, `undefined` otherwise
     */
    findSourceByID(sources: Sources[], id: string): Sources {
        return sources.find((source) => {
            return source.id == id;
        })
    }

    /**
     * Listens to an event sent from the monitor network toggle when a user toggles the svc-toggle.
     * @param event The event sent from panic-installer-sources-card.
     */
    @Listen("monitorNetworkChange", {target: "window"})
    async monitorNetworkChangeHandler(event: CustomEvent) {
        const checked: boolean = event.detail.checked;
        this.monitorNetwork = checked;

        await this.saveSourcesInConfig('nodes');

        HelperAPI.raiseToast(checked ? "Network Monitoring enabled." : "Network Monitoring disabled.");
        await dismissModal();
    }

    /**
     */
    @Listen("governanceAddressesAdd", {target: "window"})
    async governanceAddressesAddHandler(event: CustomEvent) {
        if(this.governanceAddresses === ''){
            this.governanceAddresses = `${event.detail.value}`;
        }else{
            this.governanceAddresses = `${this.governanceAddresses},${event.detail.value}`
        }

        await this.saveSourcesInConfig('nodes');

        HelperAPI.raiseToast("Governance addresses updated");
        await dismissModal();
    }

    /**
     */
    @Listen("governanceAddressesRemove", {target: "window"})
    async governanceAddressesRemoveHandler(event: CustomEvent) {
        const valueToRemove: string = event.detail.value;
        if(this.governanceAddresses.includes(`${valueToRemove},`)){
            this.governanceAddresses = this.governanceAddresses.replace(`${valueToRemove},`, '')
        }else if(this.governanceAddresses.includes(`,${valueToRemove}`)){
            this.governanceAddresses = this.governanceAddresses.replace(`,${valueToRemove}`, '')
        }else{
            this.governanceAddresses = this.governanceAddresses.replace(valueToRemove, '')
        }

        await this.saveSourcesInConfig('nodes');

        HelperAPI.raiseToast("Governance addresses updated");
        await dismissModal();
    }

    /**
     * Used to navigate to the repositories page in the installer.
     */
    @Listen("nextStep", {target: "window"})
    nextStepHandler() {
        HelperAPI.changePage(this.router, `${
            HelperAPI.getUrlPrefix()}/repositories/${this.configId}`);
    }

    /**
     * Used to navigate back to the channels page in the installer.
     */
    @Listen("previousStep", {target: "window"})
    previousStepHandler() {
        HelperAPI.changePage(this.router, `${
            HelperAPI.getUrlPrefix()}/channels/${this.configId}`);
    }

    /**
     * Gets the config and base chain from the API.
     */
    async getDataFromAPI(getBaseChain: boolean=false) {
        this.config = await ConfigService.getInstance().getByID(this.configId);
        this.config.evm_nodes = this.config['_evmNodes'];
        delete this.config['_evmNodes'];

        if (getBaseChain)
            this.baseChain = await BaseChainService.getInstance().getByID(this.config.baseChain.id);

        if (this.config.nodes && this.config.nodes.length > 0 && (this.baseChain.value === "cosmos" || this.baseChain.value === "substrate")) {
            this.monitorNetwork = this.config.nodes[0].monitorNetwork;
            if(this.baseChain.value === "substrate") {
                this.governanceAddresses = this.config.nodes[0].governanceAddresses;
            }
        }

        if (this.baseChain.value === "chainlink" && !this.config.contract) {
            this.config.contract = {url: "", monitor: false} as ContractSubconfig;
        }
    }

    async componentWillLoad() {
        // might be necessary
        // i.e. when the node operator opens a modal and then clicks in the browser's back button
        dismissModal();

        await this.getDataFromAPI(true);
    }

    render() {
        return (
            <Host>
                <div>
                    <panic-header showMenu={false} />
                    <svc-progress-bar value={0.4} color={"tertiary"} />
                </div>

                <panic-installer-sources-cards
                    config={this.config}
                    baseChain={this.baseChain}
                    monitorNetwork={this.monitorNetwork}
                    governanceAddresses={this.governanceAddresses}
                />

                <panic-footer/>
            </Host>
        )
    }
}

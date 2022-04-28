import {Component, h, Host, Listen, State} from '@stencil/core';
import {BaseChain} from '../../interfaces/chains';
import {SeverityAPI} from '../../utils/severity';
import {ChainsAPI} from '../../utils/chains';
import {POLLING_FREQUENCY, Severity} from "../../utils/constants";
import {DashboardOverviewAPI} from './utils/panic-dashboard-overview.utils';
import {PanicDashboardOverviewInterface} from './panic-dashboard-overview.interface';
import {FilterState} from '../../interfaces/filterState';
import {FilterStateAPI} from '../../utils/filterState';
import {HelperAPI} from '../../utils/helpers';

@Component({
    tag: 'panic-dashboard-overview',
    styleUrl: 'panic-dashboard-overview.scss'
})
export class PanicDashboardOverview implements PanicDashboardOverviewInterface {

    @State() baseChains: BaseChain[] = [];
    _filterStates: FilterState[] = [];
    _updater: number;
    _updateFrequency: number = POLLING_FREQUENCY;

    async componentWillLoad() {
        try {
            await this.reRenderAction();

            this._updater = window.setInterval(async () => {
                await this.reRenderAction();
            }, this._updateFrequency);
        } catch (error: any) {
            console.error(error);
        }
    }

    async reRenderAction() {
        const latestBaseChains = await ChainsAPI.getAllBaseChains();
        this._filterStates = FilterStateAPI.getFilterStates(latestBaseChains, this._filterStates);
        this.baseChains = await ChainsAPI.updateBaseChainsWithAlerts(latestBaseChains, this._filterStates);
    }

    async componentDidLoad() {
        // Add text title to chain filter and severity filter.
        for (const baseChain of this.baseChains) {
            // Chain Filter text-placeholder (Chains).
            HelperAPI.addTitleToSVCSelect(`${baseChain.name}_chain-filter`, 'Chains')
            // Severity Filter text-placeholder (Severity).
            HelperAPI.addTitleToSVCSelect(`${baseChain.name}_severity-filter`, 'Severity')
        }
    }

    @Listen('filter-changed')
    async filterChanged(event: CustomEvent) {
        try {
            const baseChainName: string = event.detail['base-chain-name'];
            const selectedChains: string[] = event.detail['selected-chains'].split(',');

            // Remove empty string element from array if no chains are selected.
            if (selectedChains.length > 0 && selectedChains[0] === '') {
                selectedChains.pop();
            }

            // Get filter state which contains the altered filters.
            const filterState: FilterState = FilterStateAPI.getFilterState(baseChainName, this._filterStates);

            // Update active chain if chain filter was changed.
            if (!HelperAPI.arrayEquals(filterState.selectedSubChains, selectedChains)) {
                filterState.selectedSubChains = selectedChains;
                // Get base chain which contains the altered filters.
                const baseChain: BaseChain = this.baseChains.find(baseChain => baseChain.name === baseChainName);
                HelperAPI.updateTextSVCSelect(`${baseChainName}_chain-filter`, selectedChains.length === baseChain.subChains.length);
                await this.reRenderAction();
            } else {
                const selectedSeverities = event.detail['alerts-severity'].split(',');

                // Remove empty string element from array if no alerts are selected.
                if (selectedSeverities.length > 0 && selectedSeverities[0] === '') {
                    selectedSeverities.pop();
                }

                // Update severities shown if severity filter was changed.
                if (!HelperAPI.arrayEquals(filterState.selectedSeverities, selectedSeverities)) {
                    filterState.selectedSeverities = selectedSeverities;
                    HelperAPI.updateTextSVCSelect(`${baseChainName}_severity-filter`, selectedSeverities.length === Object.keys(Severity).length - 1);
                    await this.reRenderAction();
                }
            }
        } catch (error: any) {
            console.error(error);
        }
    }

    disconnectedCallback() {
        window.clearInterval(this._updater);
    }

    render() {
        return (
            <Host>
                <h1 class='panic-dashboard-overview__title'>DASHBOARD
                    OVERVIEW</h1>
                {this.baseChains.map((baseChain) =>
                    <svc-surface label={baseChain.name}>
                        <svc-card class="panic-dashboard-overview__chain-card">
                            <div slot="expanded">
                                <svc-filter event-name="filter-changed"
                                            debounce={100}>
                                    <input name='base-chain-name'
                                           value={baseChain.name} hidden/>

                                    <div
                                        class="panic-dashboard-overview__chain-filter-container">
                                        {/* Chain filter */}
                                        <svc-select
                                            name="selected-chains"
                                            id={`${baseChain.name}_chain-filter`}
                                            multiple={true}
                                            value={FilterStateAPI.getFilterState(baseChain.name, this._filterStates).selectedSubChains}
                                            header="Select chains"
                                            placeholder="Select chains"
                                            options={DashboardOverviewAPI.getChainFilterOptionsFromBaseChain(baseChain)}
                                        />
                                    </div>

                                    <div
                                        class='panic-dashboard-overview__slots'>
                                        {/* A normal pie chart with the data is shown if there are any alerts. Otherwise,
                                         A green pie chart is shown with no text and without a tooltip */}
                                        <div
                                            class="panic-dashboard-overview__pie-chart">
                                            {DashboardOverviewAPI.getPieChartJSX(baseChain, FilterStateAPI.getFilterState(baseChain.name, this._filterStates).selectedSubChains)}
                                        </div>

                                        <div
                                            class="panic-dashboard-overview__data-table-container">
                                            <div>
                                                {/* Severity filter */}
                                                <svc-select
                                                    name="alerts-severity"
                                                    id={`${baseChain.name}_severity-filter`}
                                                    multiple={true}
                                                    value={FilterStateAPI.getFilterState(baseChain.name, this._filterStates).selectedSeverities}
                                                    header="Select severities"
                                                    placeholder="Select severities"
                                                    options={SeverityAPI.getSeverityFilterOptions(true)}
                                                />

                                                {/* Data table */}
                                                {DashboardOverviewAPI.getDataTableJSX(baseChain, FilterStateAPI.getFilterState(baseChain.name, this._filterStates))}
                                            </div>
                                        </div>
                                    </div>
                                </svc-filter>
                            </div>
                            <div slot="collapsed"
                                 class="panic-dashboard-overview__collapsed-card">
                                {DashboardOverviewAPI.getCollapsedCardJSX(baseChain)}
                            </div>
                        </svc-card>
                        <svc-label color="dark" position="start"
                                   class="panic-dashboard-overview__info-message">This
                            section displays only warning, critical and error
                            alerts. For a full report, check <svc-anchor
                                label={"Alerts Overview."}
                                url={"#alerts-overview"}/></svc-label>
                    </svc-surface>
                )}
            </Host>
        );
    }
}

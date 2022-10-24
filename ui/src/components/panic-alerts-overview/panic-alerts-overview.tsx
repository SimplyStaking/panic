import {Component, h, Host, Listen, State} from '@stencil/core';
import {Alert} from '../../interfaces/alerts';
import {SubChain} from '../../interfaces/chains';
import {AlertsAPI} from '../../utils/alerts';
import {AlertsOverviewAPI} from './utils/panic-alerts-overview.utils';
import {ChainsAPI} from '../../utils/chains';
import {SeverityAPI} from '../../utils/severity';
import {POLLING_FREQUENCY, Severity} from "../../utils/constants";
import {PanicAlertsOverviewInterface} from './panic-alerts-overview.interface';
import {FilterStateV2} from '../../interfaces/filterState';
import {HelperAPI} from '../../utils/helpers';

@Component({
    tag: 'panic-alerts-overview',
    styleUrl: 'panic-alerts-overview.scss'
})
export class PanicAlertsOverview implements PanicAlertsOverviewInterface {
    @State() alerts: Alert[] = [];
    _subChains: SubChain[] = [];
    _filterState: FilterStateV2 = {
        chainName: '',
        selectedSubChains: [],
        selectedSeverities: [],
        selectedSources: [],
        fromDateTime: '',
        toDateTime: ''
    }
    _updater: number;
    _updateFrequency: number = POLLING_FREQUENCY;
    _isFirstRun: boolean = false;

    async componentWillLoad() {
        try {
            this._subChains = await ChainsAPI.getSubChains();
            await this.reRenderAction();

            this._updater = window.setInterval(async () => {
                await this.reRenderAction();
            }, this._updateFrequency);
        } catch (error: any) {
            console.error(error);
        }
    }

    async reRenderAction() {
        this._subChains = await ChainsAPI.getSubChains();
        this.alerts = await AlertsAPI.getAlerts(this._subChains, this._filterState);
    }

    async componentDidLoad() {
        // Chain Filter text-placeholder (Chains).
        HelperAPI.addTitleToSVCSelect('chains-filter', 'Chains');
        // Severity Filter text-placeholder (Severity).
        HelperAPI.addTitleToSVCSelect('severity-filter', 'Severity');
        // Sources Filter text-placeholder (Sources).
        HelperAPI.addTitleToSVCSelect('sources-filter', 'Sources');
    }

    @Listen('filter-changed')
    async filterChanged(event: CustomEvent) {
        try {
            // Check selected date/time
            if (event.detail['date-time-from'] !== this._filterState.fromDateTime) {
                // Check if datetime specified is out of bounds (future datetime).
                // TODO: In the future, this will be replaced (min/max datetime).
                if (HelperAPI.dateTimeStringToTimestamp(event.detail['date-time-from']) > HelperAPI.getCurrentTimestamp()) {
                    window.alert('Inputted \'from\' date/time value is not valid since it\'s in the future.');
                } else if (!AlertsOverviewAPI.validateDateTimeOrder(event.detail['date-time-from'], this._filterState.toDateTime)) {
                    window.alert('Inputted \'from\' date/time value is not valid since it\'s bigger than the \'to\' date/time value.');
                } else {
                    this._filterState.fromDateTime = event.detail['date-time-from'];
                }
                await this.reRenderAction();
            } else if (event.detail['date-time-to'] !== this._filterState.toDateTime) {
                // Check if datetime specified is out of bounds (future datetime).
                // TODO: In the future, this will be replaced (min/max datetime).
                if (HelperAPI.dateTimeStringToTimestamp(event.detail['date-time-to']) > HelperAPI.getCurrentTimestamp()) {
                    window.alert('Inputted \'to\' date/time value is not valid since it\'s in the future.');
                } else if (!AlertsOverviewAPI.validateDateTimeOrder(this._filterState.fromDateTime, event.detail['date-time-to'])) {
                    window.alert('Inputted \'to\' date/time value is not valid since it\'s smaller than the \'from\' date/time value.');
                } else {
                    this._filterState.toDateTime = event.detail['date-time-to'];
                }
                await this.reRenderAction();
            } else if (!HelperAPI.arrayEquals(this._filterState.selectedSubChains, AlertsOverviewAPI.formatEventData(event.detail['selected-chains']))) {
                // Update active chains if chains filter was changed.
                this._filterState.selectedSubChains = AlertsOverviewAPI.formatEventData(event.detail['selected-chains']);
                this._filterState.selectedSources = [];
                HelperAPI.updateTextSVCSelect('chains-filter', this._filterState.selectedSubChains.length === this._subChains.length);
                await this.reRenderAction();
            } else if (!HelperAPI.arrayEquals(this._filterState.selectedSeverities, AlertsOverviewAPI.formatEventData(event.detail['selected-severities']))) {
                // Update severities shown if severity filter was changed.
                this._filterState.selectedSeverities = AlertsOverviewAPI.formatEventData(event.detail['selected-severities']) as Severity[];
                HelperAPI.updateTextSVCSelect('severity-filter', this._filterState.selectedSeverities.length === Object.keys(Severity).length);
                await this.reRenderAction();
            } else if (!HelperAPI.arrayEquals(this._filterState.selectedSources, AlertsOverviewAPI.formatEventData(event.detail['selected-sources']))) {
                // Update sources shown if sources filter was changed.
                this._filterState.selectedSources = AlertsOverviewAPI.formatEventData(event.detail['selected-sources']);
                HelperAPI.updateTextSVCSelect('sources-filter', this._filterState.selectedSources.length === ChainsAPI.activeChainsSources(this._subChains, this._filterState.selectedSubChains).length);
                await this.reRenderAction();
            }
        } catch (error: any) {
            console.error(error);
        }
    }

    disconnectedCallback() {
        window.clearInterval(this._updater);
    }

    render() {
        if (this._isFirstRun) {
            return "";
        }

        return (
            <Host>
                <h1 class='panic-alerts-overview__title'
                    id="alerts-overview">ALERTS OVERVIEW</h1>
                <svc-surface>
                    <div class="panic-alerts-overview__data-table-container">
                        <svc-event-emitter eventName="filter-changed" debounce={100}>
                            <div class="panic-alerts-overview__slots">
                                {/* Chain filter */}
                                <svc-select
                                    name="selected-chains"
                                    id="chains-filter"
                                    multiple={true}
                                    value={this._filterState.selectedSubChains}
                                    header="Select chains"
                                    placeholder="Select chains"
                                    options={AlertsOverviewAPI.getChainFilterOptionsFromChains(this._subChains)}
                                />
                                {/* Severity filter */}
                                <svc-select
                                    name="selected-severities"
                                    id="severity-filter"
                                    multiple={true}
                                    value={this._filterState.selectedSeverities}
                                    header="Select severities"
                                    placeholder="Select severities"
                                    options={SeverityAPI.getSeverityFilterOptions()}
                                />
                            </div>
                            <div class="panic-alerts-overview__slots">
                                {/* Sources filter */}
                                <svc-select
                                    name="selected-sources"
                                    id="sources-filter"
                                    multiple={true}
                                    value={this._filterState.selectedSources}
                                    header="Select sources"
                                    placeholder="Select sources"
                                    options={AlertsOverviewAPI.getSourcesFilterOptions(ChainsAPI.activeChainsSources(this._subChains, this._filterState.selectedSubChains))}
                                />
                                {/* Date/time picker */}
                                <div
                                    class="panic-alerts-overview__date-time-container">
                                    <h4>From:</h4>
                                    <svc-date-time
                                        name="date-time-from"
                                        mode="datetime-local"
                                        value={this._filterState.fromDateTime}
                                    />
                                    <h4> To:</h4>
                                    <svc-date-time
                                        name="date-time-to"
                                        mode="datetime-local"
                                        value={this._filterState.toDateTime}
                                    />
                                </div>
                            </div>
                        </svc-event-emitter>
                        {/* Data table */}
                        {AlertsOverviewAPI.getDataTableJSX(this.alerts)}
                    </div>
                </svc-surface>
            </Host>
        );
    }
}

import { Component, Host, h, State, Listen } from '@stencil/core';
import { Alert } from '../../interfaces/alerts';
import { Chain } from '../../interfaces/chains';
import { AlertsAPI } from '../../utils/alerts';
import { AlertsOverviewAPI } from './utils/panic-alerts-overview.utils';
import { ChainsAPI } from '../../utils/chains';
import { SeverityAPI } from '../../utils/severity';
import { pollingFrequency } from '../../utils/constants';
import { PanicAlertsOverviewInterface } from './panic-alerts-overview.interface';
import { addTitleToSVCSelect, arrayEquals } from '../../utils/helpers';
import { FilterState } from '../../interfaces/filterState';

@Component({
  tag: 'panic-alerts-overview',
  styleUrl: 'panic-alerts-overview.scss'
})
export class PanicAlertsOverview implements PanicAlertsOverviewInterface {
  @State() alerts: Alert[] = [];
  _chains: Chain[];
  _filterState: FilterState = {
    chainName: '',
    activeSeverities: SeverityAPI.getAllSeverityValues(),
    lastClickedColumnIndex: 1,
    ordering: 'descending'
  }
  _updater: number;
  _updateFrequency: number = pollingFrequency;

  async componentWillLoad() {
    try {
      const chains = await ChainsAPI.getChains();
      this._chains = await ChainsAPI.updateChains(chains);
      this.alerts = await AlertsAPI.getAlerts(this._chains, this._filterState.activeSeverities, 0, 2625677273);

      this._updater = window.setInterval(async () => {
        await this.reRenderAction();
      }, this._updateFrequency);
    } catch (error: any) {
      console.error(error);
    }
  }

  async reRenderAction() {
    this._chains = await ChainsAPI.updateChains(this._chains);
    this.alerts = await AlertsAPI.getAlerts(this._chains, this._filterState.activeSeverities, 0, 2625677273);
  }

  async componentDidLoad() {
    // Chain Filter text-placeholder (Chains).
    addTitleToSVCSelect('chains-filter', 'Chains');
    // Severity Filter text-placeholder (Severity).
    addTitleToSVCSelect('severity-filter', 'Severity');
  }

  @Listen('filter-changed')
  async filterChanged(event: CustomEvent) {
    try {
      const selectedChains: string[] = event.detail['selected-chains'].split(',');

      // Remove empty string element from array if no chains are selected.
      if (selectedChains.length > 0 && selectedChains[0] === '') {
        selectedChains.pop();
      }

      // Update active chains if chains filter was changed.
      if (!arrayEquals(ChainsAPI.getChainFilterValue(this._chains), selectedChains)) {
        this._chains = ChainsAPI.updateActiveChains(this._chains, selectedChains);
        await this.reRenderAction();
      } else {
        const selectedSeverities = event.detail['alerts-severity'].split(',');

        // Remove empty string element from array if no alerts are selected.
        if (selectedSeverities.length > 0 && selectedSeverities[0] === '') {
          selectedSeverities.pop();
        }

        // Update severities shown if severity filter was changed.
        if (!arrayEquals(SeverityAPI.getSeverityFilterValue(this._filterState.activeSeverities), selectedSeverities)) {
          if (selectedSeverities.length > 0) {
            this._filterState.activeSeverities = selectedSeverities;
          } else {
            this._filterState.activeSeverities = SeverityAPI.getAllSeverityValues();
          }
          await this.reRenderAction();
        }
      }
    } catch (error: any) {
      console.error(error);
    }
  }

  // Used to keep track of the last clicked column index and the order of the
  // sorted column within the data table (and base chain since correlated).
  @Listen("svcDataTable__lastClickedColumnIndexEvent")
  setDataTableProperties(e: CustomEvent) {
    this._filterState.lastClickedColumnIndex = e.detail.index;
    this._filterState.ordering = e.detail.ordering;
  }

  render() {
    return (
      <Host>
        <h1 class='panic-alerts-overview__title'>ALERTS OVERVIEW</h1>
        <svc-card class="panic-alerts-overview__chain-card">
          <div slot='content' id='expanded' class="panic-alerts-overview__data-table-container">
            <svc-filter event-name="filter-changed" debounce={100}>
              <div class="panic-alerts-overview__slots">
                {/* Chain filter */}
                <svc-select
                  name="selected-chains"
                  id="chains-filter"
                  multiple={true}
                  value={ChainsAPI.getChainFilterValue(this._chains)}
                  header="Select chains"
                  placeholder="All"
                  options={AlertsOverviewAPI.getChainFilterOptionsFromChains(this._chains)}>
                </svc-select>
                {/* Severity filter */}
                <svc-select
                  name="alerts-severity"
                  id="severity-filter"
                  multiple={true}
                  value={SeverityAPI.getSeverityFilterValue(this._filterState.activeSeverities)}
                  header="Select severities"
                  placeholder="All"
                  options={SeverityAPI.getSeverityFilterOptions()}>
                </svc-select>
              </div>
              {/* Data table */}
              {AlertsOverviewAPI.getDataTableJSX(this.alerts, this._chains, this._filterState)}
            </svc-filter>
          </div>
        </svc-card>
      </Host>
    );
  }
}

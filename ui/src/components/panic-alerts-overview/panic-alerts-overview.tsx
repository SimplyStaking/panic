import { Component, Host, h, State, Listen } from '@stencil/core';
import { Alert, Severity } from '../../interfaces/alerts';
import { Chain } from '../../interfaces/chains';
import { AlertsAPI } from '../../utils/alerts';
import { AlertsOverviewAPI } from './utils/panic-alerts-overview.utils';
import { ChainsAPI } from '../../utils/chains';
import { pollingFrequency } from '../../utils/constants';
import { PanicAlertsOverviewInterface } from './panic-alerts-overview.interface';
import { arrayEquals } from '../../utils/helpers';

@Component({
  tag: 'panic-alerts-overview',
  styleUrl: 'panic-alerts-overview.scss'
})
export class PanicAlertsOverview implements PanicAlertsOverviewInterface {
  @State() alerts: Alert[] = [];
  _chains: Chain[];
  _updater: number;
  _updateFrequency: number = pollingFrequency;
  _activeSeverities: Severity[] = AlertsAPI.getAllSeverityValues();
  _lastClickedColumnIndex: number = 1;
  _ordering: 'ascending' | 'descending' = 'descending';

  async componentWillLoad() {
    try {
      const chains = await ChainsAPI.getChains();
      this._chains = await ChainsAPI.updateChains(chains);
      this.alerts = await AlertsAPI.getAlertsFromMongoDB(this._chains, this._activeSeverities, 0, 2625677273);

      this._updater = window.setInterval(async () => {
        await this.reRenderAction();
      }, this._updateFrequency);
    } catch (error: any) {
      console.error(error);
    }
  }

  async reRenderAction() {
    this._chains = await ChainsAPI.updateChains(this._chains);
    this.alerts = await AlertsAPI.getAlertsFromMongoDB(this._chains, this._activeSeverities, 0, 2625677273);
  }

  async componentDidLoad() {
    // Chain Filter text-placeholder (Chains).
    const chainFilterShadow = document.querySelector('#chains-filter ion-select').shadowRoot;
    const chainFilterSelectText = chainFilterShadow.querySelector('.select-text');
    const chainFilterSelectIcon = chainFilterShadow.querySelector('.select-icon');
    const selectTextTitle = chainFilterSelectText.cloneNode() as Element;
    selectTextTitle.classList.remove('select-text');
    selectTextTitle.classList.add('select-text-title');
    selectTextTitle.setAttribute('part', 'text-title');
    selectTextTitle.textContent = 'Chains';
    chainFilterShadow.insertBefore(selectTextTitle, chainFilterSelectIcon);

    // Severity Filter text-placeholder (Severity).
    const severityFilterShadow = document.querySelector(`#severity-filter ion-select`).shadowRoot;
    const severityFilterSelectIcon = severityFilterShadow.querySelector('.select-icon');
    const selectTextTitle2 = selectTextTitle.cloneNode() as Element;
    selectTextTitle2.textContent = 'Severity';
    severityFilterShadow.insertBefore(selectTextTitle2, severityFilterSelectIcon);
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
      if (!arrayEquals(ChainsAPI.getActiveChainNames(this._chains), selectedChains)) {
        this._chains = ChainsAPI.updateActiveChains(this._chains, selectedChains);
        await this.reRenderAction();
      } else {
        const selectedAlerts = event.detail['alerts-severity'].split(',');

        // Remove empty string element from array if no alerts are selected.
        if (selectedAlerts.length > 0 && selectedAlerts[0] === '') {
          selectedAlerts.pop();
        }

        // Update severities shown if severity filter was changed.
        if (!arrayEquals(this._activeSeverities, selectedAlerts)) {
          this._activeSeverities = selectedAlerts;
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
    this._lastClickedColumnIndex = e.detail.index;
    this._ordering = e.detail.ordering;
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
                  value={ChainsAPI.getActiveChainNames(this._chains)}
                  header="Select chains"
                  placeholder="Select chains"
                  options={AlertsOverviewAPI.getChainFilterOptionsFromChains(this._chains)}>
                </svc-select>
                {/* Severity filter */}
                <svc-select
                  name="alerts-severity"
                  id="severity-filter"
                  multiple={true}
                  value={this._activeSeverities}
                  header="Select severities"
                  placeholder="Select severities"
                  options={AlertsAPI.getSeverityFilterOptions(false)}>
                </svc-select>
              </div>
              {/* Data table */}
              {AlertsOverviewAPI.getDataTableJSX(this.alerts, this._chains, this._lastClickedColumnIndex, this._ordering)}
            </svc-filter>
          </div>
        </svc-card>
      </Host>
    );
  }
}

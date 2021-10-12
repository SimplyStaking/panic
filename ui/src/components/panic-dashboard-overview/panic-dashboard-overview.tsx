import { Component, Host, h, State, Listen } from '@stencil/core';
import { BaseChain } from '../../interfaces/chains';
import { AlertsAPI } from '../../utils/alerts';
import { ChainsAPI } from '../../utils/chains';
import { pollingFrequency } from '../../utils/constants';
import { DashboardOverviewAPI } from './utils/panic-dashboard-overview.utils';
import { arrayEquals } from '../../utils/helpers';
import { PanicDashboardOverviewInterface } from './panic-dashboard-overview.interface';

@Component({
  tag: 'panic-dashboard-overview',
  styleUrl: 'panic-dashboard-overview.scss'
})
export class PanicDashboardOverview implements PanicDashboardOverviewInterface {

  @State() baseChains: BaseChain[] = [];
  _updater: number;
  _updateFrequency: number = pollingFrequency;

  async componentWillLoad() {
    try {
      const baseChains = await ChainsAPI.getBaseChains();
      this.baseChains = await ChainsAPI.updateBaseChains(baseChains);

      this._updater = window.setInterval(async () => {
        this.baseChains = await ChainsAPI.updateBaseChains(this.baseChains);
      }, this._updateFrequency);
    } catch (error: any) {
      console.error(error);
    }
  }

  async componentDidLoad() {
    // Add text title to chain filter and severity filter.
    for (const baseChain of this.baseChains) {
      // Chain Filter text-placeholder (Chains).
      const chainFilterShadow = document.querySelector(`#${baseChain.name}_chain-filter ion-select`).shadowRoot;
      const chainFilterSelectText = chainFilterShadow.querySelector('.select-text');
      const chainFilterSelectIcon = chainFilterShadow.querySelector('.select-icon');
      const selectTextTitle = chainFilterSelectText.cloneNode() as Element;
      selectTextTitle.classList.remove('select-text');
      selectTextTitle.classList.add('select-text-title');
      selectTextTitle.setAttribute('part', 'text-title');
      selectTextTitle.textContent = 'Chains';
      chainFilterShadow.insertBefore(selectTextTitle, chainFilterSelectIcon);

      // Severity Filter text-placeholder (Severity).
      const severityFilterShadow = document.querySelector(`#${baseChain.name}_severity-filter ion-select`).shadowRoot;
      const severityFilterSelectIcon = severityFilterShadow.querySelector('.select-icon');
      const selectTextTitle2 = selectTextTitle.cloneNode() as Element;
      selectTextTitle2.textContent = 'Severity';
      severityFilterShadow.insertBefore(selectTextTitle2, severityFilterSelectIcon);
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

      // Get base chain which contains the altered filters.
      const baseChain: BaseChain = this.baseChains.find(baseChain => baseChain.name === baseChainName);

      // Update active chain if chain filter was changed.
      if (!arrayEquals(baseChain.activeChains, selectedChains)) {
        this.baseChains = ChainsAPI.updateActiveChains(this.baseChains, baseChainName, selectedChains);
      } else {
        const selectedAlerts = event.detail['alerts-severity'].split(',');

        // Remove empty string element from array if no alerts are selected.
        if (selectedAlerts.length > 0 && selectedAlerts[0] === '') {
          selectedAlerts.pop();
        }

        // Update severities shown if severity filter was changed.
        if (!arrayEquals(baseChain.activeSeverities, selectedAlerts)) {
          baseChain.activeSeverities = selectedAlerts;
          // This is done to re-render since the above does not.
          this.baseChains = [...this.baseChains];
        }
      }
    } catch (error: any) {
      console.error(error);
    }
  }

  // Used to keep track of the last clicked column index and the order of the
  // sorted column within each data table (and base chain since correlated).
  @Listen("svcDataTable__lastClickedColumnIndexEvent")
  setDataTableProperties(e: CustomEvent) {
    // Get base chain which contains the altered ordering/sorting.
    const baseChain: BaseChain = this.baseChains.find(baseChain => baseChain.name === e.target['id']);
    baseChain.lastClickedColumnIndex = e.detail.index;
    baseChain.ordering = e.detail.ordering;
  }

  disconnectedCallback() {
    window.clearInterval(this._updater);
  }

  render() {
    return (
      <Host>
        <h1 class='panic-dashboard-overview__title'>DASHBOARD OVERVIEW</h1>
        {this.baseChains.map((baseChain) =>
          <svc-surface label={baseChain.name}>
            <svc-filter event-name="filter-changed" debounce={100}>
              <svc-card class="panic-dashboard-overview__chain-card">
                <div slot='content' id='expanded'>
                  <input name='base-chain-name' value={baseChain.name} hidden />

                  <div class="panic-dashboard-overview__chain-filter-container">
                    {/* Chain filter */}
                    <svc-select
                      name="selected-chains"
                      id={baseChain.name + '_chain-filter'}
                      multiple={true}
                      value={ChainsAPI.getActiveChainNames(baseChain.chains)}
                      header="Select chains"
                      placeholder="Select chains"
                      options={DashboardOverviewAPI.getChainFilterOptionsFromBaseChain(baseChain)}>
                    </svc-select>
                  </div>

                  <div class='panic-dashboard-overview__slots'>
                    {/* A normal pie chart with the data is shown if there are any alerts. Otherwise,
                      A green pie chart is shown with no text and without a tooltip */}
                    <div class="panic-dashboard-overview__pie-chart">
                      {DashboardOverviewAPI.getPieChartJSX(baseChain)}
                    </div>

                    <div class="panic-dashboard-overview__data-table-container">
                      <div>
                        {/* Severity filter */}
                        <svc-select
                          name="alerts-severity"
                          id={baseChain.name + '_severity-filter'}
                          multiple={true}
                          value={baseChain.activeSeverities}
                          header="Select severities"
                          placeholder="Select severities"
                          options={AlertsAPI.getSeverityFilterOptions(true)}>
                        </svc-select>

                        {/* Data table */}
                        {DashboardOverviewAPI.getDataTableJSX(baseChain)}
                      </div>
                    </div>
                  </div>
                </div>
              </svc-card>
            </svc-filter>
            <svc-label color="dark" position="start" class="panic-dashboard-overview__info-message">This section displays only warning, critical and error alerts. For a full report, check <svc-anchor label={"Alerts Overview."} url={"#alerts-overview"} /> </svc-label>

          </svc-surface>
        )}
      </Host >
    );
  }
}

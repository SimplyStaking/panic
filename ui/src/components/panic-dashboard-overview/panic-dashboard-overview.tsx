import { Component, Host, h, State, Listen } from '@stencil/core';
import { BaseChain } from '../../interfaces/chains';
import { ChainsAPI, getActiveChainNames, updateActiveChains } from '../../utils/chains';
import { getDataTableJSX, getPieChartJSX, getChainFilterOptionsFromBaseChain, getSeverityFilterOptions } from '../../utils/dashboard-overview';
import { arrayEquals } from '../../utils/helpers';
import { PanicDashboardOverviewInterface } from './panic-dashboard-overview.interface';

@Component({
  tag: 'panic-dashboard-overview',
  styleUrl: 'panic-dashboard-overview.scss'
})
export class PanicDashboardOverview implements PanicDashboardOverviewInterface {

  @State() baseChains: BaseChain[] = [];
  _updater: number;
  _updateFrequency: number = 5000;

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

  @Listen('filter-changed')
  async filterChanged(event: CustomEvent) {
    try {
      const baseChainName = event.detail['base-chain-name'];
      const selectedChains = event.detail['chain-name'].split(',');

      // Get base chain which contains the altered filters.
      const baseChain: BaseChain = this.baseChains.find(baseChain => baseChain.name === baseChainName);

      // Update active chain if chain filter was changed.
      if (!arrayEquals(baseChain.activeChains, selectedChains)) {
        this.baseChains = updateActiveChains(this.baseChains, baseChainName, selectedChains);
      } else {
        const selectedAlerts = event.detail['alerts-severity'].split(',');
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

  disconnectedCallback() {
    window.clearInterval(this._updater);
  }

  render() {
    return (
      <Host>
        <panic-header />
        <svc-content-container>
          {this.baseChains.map((baseChain) =>
            <svc-surface label={baseChain.name}>
              <svc-filter event-name="filter-changed" debounce={100}>
                <svc-card class="panic-dashboard-overview__chain-card">
                  <input name='base-chain-name' value={baseChain.name} hidden />
                  {/* Chain filter */}
                  <svc-select
                    name="chain-name"
                    id={baseChain.name + '_chain-filter'}
                    class="panic-dashboard-overview__chain-filter"
                    slot="header"
                    multiple={true}
                    value={getActiveChainNames(baseChain.chains)}
                    header="Select Chain"
                    placeholder="No Chains Selected"
                    options={getChainFilterOptionsFromBaseChain(baseChain)}>
                  </svc-select>

                  {/* A normal pie chart with the data is shown if there are any alerts. Otherwise,
                      A green pie chart is shown with no text and without a tooltip */}
                  {getPieChartJSX(baseChain)}

                  <div slot="large">
                    {/* Severity filter */}
                    <svc-select
                      name="alerts-severity"
                      id={baseChain.name + '_severity-filter'}
                      class="panic-dashboard-overview__severity-filter"
                      multiple={true}
                      value={baseChain.activeSeverities}
                      header="Select Alerts Severity"
                      placeholder="No Alerts Severities Selected"
                      options={getSeverityFilterOptions()}>
                    </svc-select>

                    {/* Data table */}
                    {getDataTableJSX(baseChain)}
                  </div>
                </svc-card>
              </svc-filter>
              <svc-label color="dark" position="start" class="panic-dashboard-overview__info-message">This section displays only warning, critical and error alerts. For a full report, check <svc-anchor label={"Alerts Overview."} url={"#alerts-overview"} /> </svc-label>

            </svc-surface>
          )}
        </svc-content-container>
        <panic-footer />
      </Host >
    );
  }
}

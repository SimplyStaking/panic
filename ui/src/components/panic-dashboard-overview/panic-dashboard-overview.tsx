import { Component, Host, h, State, Listen } from '@stencil/core';
import { BaseChain } from '../../interfaces/chains';
import { ChainsAPI, filterActiveChains } from '../../utils/chains';
import { getDataTableJSX, getPieChartJSX, getSelectOptionTypeFromBaseChain } from '../../utils/dashboard-overview';
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
  filterChanged(event: CustomEvent) {
    try {
      const baseChainName = event.detail['base-chain-name'];
      const chainName = event.detail['chain-name'];

      this.baseChains = this.baseChains.filter(filterActiveChains, { baseChainName, chainName });

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
              {baseChain.chains.map((chain) => {
                return chain.active &&
                  <svc-filter event-name="filter-changed" debounce={100}>
                    <svc-card class="panic-dashboard-overview__chain-card">
                      <input name='base-chain-name' value={baseChain.name} hidden />
                      <svc-select name="chain-name" id={baseChain.name} class="panic-dashboard-overview__chain-filter" slot="header" value="all" header="Choose Chain" options={getSelectOptionTypeFromBaseChain(baseChain)}></svc-select>

                      {/* A normal pie chart with the data is shown if there are any alerts. Otherwise,
                      A green pie chart is shown with no text and without a tooltip */}
                      {getPieChartJSX(chain.name, chain.criticalAlerts, chain.warningAlerts, chain.errorAlerts)}

                      <div slot="large">{getDataTableJSX(chain.name, chain.alerts)}</div>
                    </svc-card>
                  </svc-filter>
              })}
              <svc-label color="dark" position="start" class="panic-dashboard-overview__info-message">This section displays only warning, critical and error alerts. For a full report, check <svc-anchor label={"Alerts Overview."} url={"#alerts-overview"} /> </svc-label>

            </svc-surface>
          )}
        </svc-content-container>
        <panic-footer />
      </Host >
    );
  }
}

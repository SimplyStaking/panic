import { Component, Host, h, State, Listen } from '@stencil/core';
import { BaseChain } from '../../interfaces/chains';
import { ChainsAPI, filterActiveChains } from '../../utils/chains';
import { getPieChartJSX, getSubChainsByBaseChain } from '../../utils/dashboard-overview';
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

  @Listen('ionChange')
  changedValue(event: CustomEvent) {
    try {
      const parent = (event.target as HTMLElement).parentElement;
      const parentClassList = parent.classList;

      // Chain Filter case
      if (parentClassList.contains('panic-dashboard-overview__chain-filter')) {
        const baseChainName = parent.id;
        const chainName = event.detail['value'];

        this.baseChains = this.baseChains.filter(filterActiveChains, { baseChainName, chainName });
        // Severity Filter case
      } else if (parentClassList.contains('panic-dashboard-overview__severity-filter')) {
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
              {baseChain.chains.map((chain) => {
                return chain.active && <svc-card class="panic-dashboard-overview__chain-card">
                  <svc-select id={baseChain.name} class="panic-dashboard-overview__chain-filter" slot="header" value="all" header="Choose Chain" options={getSubChainsByBaseChain(baseChain)}></svc-select>

                  {/* A normal pie chart with the data is shown if there are any alerts. Otherwise,
                      A green pie chart is shown with no text and without a tooltip */}
                  {getPieChartJSX(chain.name, chain.criticalAlerts, chain.warningAlerts, chain.errorAlerts, chain.totalAlerts)}
                </svc-card>
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

import { Component, Host, h, State, Listen } from '@stencil/core';
import { BaseChain } from '../../interfaces/chains';
import { ChainsAPI } from '../../utils/chains';
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
      if (parentClassList.contains('chain-filter')) {
        const baseChainName = parent.id;
        const chainName = event.detail['value'];

        this.baseChains = ChainsAPI.updateActiveChain(this.baseChains, baseChainName, chainName);
        // Severity Filter case
      } else if (parentClassList.contains('severity-filter')) {
      }

    } catch (error: any) {
      console.error(error);
    }
  }

  disconnectedCallback() {
    window.clearInterval(this._updater);
  }

  render() {
    const alertsColors: string[] = ['#f4dd77', '#f7797b', '#a39293'];
    const noAlertsColors: string[] = ['#b0ea8f'];
    const cols = [{ title: 'Alert', type: 'string' }, { title: 'Amount', type: 'number' }];

    return (
      <Host>
        <panic-header />
        <svc-content-container>
          {this.baseChains.map((baseChain) =>
            <svc-surface label={baseChain.name}>
              {baseChain.chains.map((chain) => {
                return chain.active && <svc-card class="chain-card">
                  <svc-select id={baseChain.name} class="chain-filter" slot="header" value="all" header="Choose Chain" options={baseChain.chains.map(chain => ({ value: chain.name, label: chain.name }))}></svc-select>

                  {/* A normal pie chart with the data is shown if there are any alerts. Otherwise,
                      A green pie chart is shown with no text and without a tooltip */}
                  {chain.totalAlerts > 0 ?
                    <svc-pie-chart key={`${chain.name}-pie-chart-alerts`} slot="small" colors={alertsColors} cols={cols}
                      rows={[['Warning', chain.warningAlerts], ['Critical', chain.criticalAlerts], ['Error', chain.errorAlerts]]}>
                    </svc-pie-chart> :
                    <svc-pie-chart key={`${chain.name}-pie-chart-no-alerts`} slot="small" colors={noAlertsColors} cols={cols} rows={[['', 1]]}
                      pie-slice-text="none"
                      tooltip-trigger="none">
                    </svc-pie-chart>}
                </svc-card>
              })}
              <svc-label color="dark" position="start" class="info-message">This section displays only warning, critical and error alerts. For a full report, check <svc-anchor label={"Alerts Overview"} url={"#alerts-overview"} /> </svc-label>

            </svc-surface>
          )}
        </svc-content-container>
        <panic-footer />
      </Host >
    );
  }
}

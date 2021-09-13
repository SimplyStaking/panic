import { Component, Host, h, State } from '@stencil/core';
import { BaseChain } from '../../interfaces/chains';
import { getMonitorablesInfo, updateAllBaseChains } from '../../utils/chains';

@Component({
  tag: 'panic-dashboard-overview',
  styleUrl: 'panic-dashboard-overview.css'
})
export class PanicDashboardOverview {
  private baseChains: BaseChain[] = [];
  private updater: number;
  private updateFrequency: number = 3000;
  @State() alertsChanged: Boolean = false;

  async componentWillLoad() {
    try {
      this.baseChains = await getMonitorablesInfo();

      this.updateIfChanged(await updateAllBaseChains(true, this.baseChains));

      this.updater = window.setInterval(async () => {
        this.updateIfChanged(await updateAllBaseChains(false, this.baseChains));
      }, this.updateFrequency);
    } catch (error: any) {
      console.error(error);
    }
  }

  updateIfChanged(changed: Boolean): void {
    if (changed) {
      this.alertsChanged = !this.alertsChanged;
    }
  }

  disconnectedCallback() {
    window.clearInterval(this.updater);
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
                  {/* A normal pie chart with the data is shown if there are any alerts. Otherwise,
                      A green pie chart is shown with no text and without a tooltip */}
                  {chain.totalAlerts > 0 ?
                    <svc-pie-chart key={`${chain.name}-pie-chart`} slot="small" colors={alertsColors} cols={cols}
                      rows={[['Warning', chain.warningAlerts], ['Critical', chain.criticalAlerts], ['Error', chain.errorAlerts]]}>
                    </svc-pie-chart> :
                    <svc-pie-chart key={`${chain.name}-pie-chart`} slot="small" colors={noAlertsColors} cols={cols} rows={[['', 1]]}
                      pie-slice-text="none"
                      tooltip-trigger="none">
                    </svc-pie-chart>}
                </svc-card>
              })}
              <svc-label color="dark" position="start">This section displays only warning, critical and error alerts. For a full report, check <b><u>Alerts Overview.</u></b></svc-label>
            </svc-surface>
          )}
        </svc-content-container>
        <panic-footer />
      </Host >
    );
  }
}

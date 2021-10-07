import { Component, Host, h, State } from '@stencil/core';
import { Alert } from '../../interfaces/alerts';
import { BaseChain } from '../../interfaces/chains';
import { AlertsAPI } from '../../utils/alerts';
import { AlertsOverviewAPI } from '../../utils/alerts-overview';
import { ChainsAPI } from '../../utils/chains';
import { pollingFrequency } from '../../utils/constants';
import { PanicAlertsOverviewInterface } from './panic-alerts-overview.interface';

@Component({
  tag: 'panic-alerts-overview',
  styleUrl: 'panic-alerts-overview.scss'
})
export class PanicAlertsOverview implements PanicAlertsOverviewInterface {
  @State() alerts: Alert[] = [];
  _globalBaseChain: BaseChain;
  _updater: number;
  _updateFrequency: number = pollingFrequency;

  async componentWillLoad() {
    try {
      const globalBaseChain = await ChainsAPI.getBaseChain();
      this._globalBaseChain = await ChainsAPI.updateBaseChain(globalBaseChain);
      this.alerts = await AlertsAPI.getAlertsFromMongoDB(this._globalBaseChain, 0, 2625677273);

      this._updater = window.setInterval(async () => {
        this._globalBaseChain = await ChainsAPI.updateBaseChain(globalBaseChain);
        this.alerts = await AlertsAPI.getAlertsFromMongoDB(this._globalBaseChain, 0, 2625677273);
      }, this._updateFrequency);
    } catch (error: any) {
      console.error(error);
    }
  }

  render() {
    return (
      <Host>
        <h1 class='panic-alerts-overview__title'>ALERTS OVERVIEW</h1>
        <svc-card class="panic-alerts-overview__chain-card">
          <div slot='content' id='expanded' class="panic-alerts-overview__data-table-container">
            {/* Data table */}
            {AlertsOverviewAPI.getDataTableJSX(this.alerts)}
          </div>
        </svc-card>
      </Host>
    );
  }
}

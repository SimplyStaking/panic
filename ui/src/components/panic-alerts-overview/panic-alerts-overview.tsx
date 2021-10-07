import { Component, Host, h, State } from '@stencil/core';
import { Alert } from '../../interfaces/alerts';
import { BaseChain } from '../../interfaces/chains';
import { AlertsAPI } from '../../utils/alerts';
import { getDataTableJSX } from '../../utils/alerts-overview';
import { ChainsAPI } from '../../utils/chains';
import { PanicAlertsOverviewInterface } from './panic-alerts-overview.interface';

@Component({
  tag: 'panic-alerts-overview',
  styleUrl: 'panic-alerts-overview.scss'
})
export class PanicAlertsOverview implements PanicAlertsOverviewInterface {
  _globalBaseChain: BaseChain;
  @State() alerts: Alert[] = [];

  async componentWillLoad() {
    try {
      const globalBaseChain = await ChainsAPI.getBaseChain();
      this._globalBaseChain = await ChainsAPI.updateBaseChain(globalBaseChain);
      this.alerts = await AlertsAPI.getAlertsFromMongoDB(this._globalBaseChain, 0, 2625677273);
    } catch (error: any) {
      console.error(error);
    }
  }

  render() {
    return (
      <Host>
        <h1 class='panic-alerts-overview__title'>ALERTS OVERVIEW</h1>
        <svc-card class="panic-alerts-overview__chain-card">
          <div slot='content' id='expanded'>
            <div class="panic-alerts-overview__data-table-container">
              <div>
                {/* Data table */}
                {getDataTableJSX(this.alerts)}
              </div>
            </div>
          </div>
        </svc-card>
      </Host>
    );
  }
}

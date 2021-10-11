import { Component, Host, h, State, Listen } from '@stencil/core';
import { Alert } from '../../interfaces/alerts';
import { BaseChain } from '../../interfaces/chains';
import { AlertsAPI } from '../../utils/alerts';
import { AlertsOverviewAPI } from './utils/panic-alerts-overview.utils';
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
      const globalBaseChain = await ChainsAPI.getGlobalBaseChain();
      this._globalBaseChain = await ChainsAPI.updateGlobalBaseChain(globalBaseChain);
      this.alerts = await AlertsAPI.getAlertsFromMongoDB(this._globalBaseChain, 0, 2625677273);

      this._updater = window.setInterval(async () => {
        this._globalBaseChain = await ChainsAPI.updateGlobalBaseChain(this._globalBaseChain);
        this.alerts = await AlertsAPI.getAlertsFromMongoDB(this._globalBaseChain, 0, 2625677273);
      }, this._updateFrequency);
    } catch (error: any) {
      console.error(error);
    }
  }

  // Used to keep track of the last clicked column index and the order of the
  // sorted column within the data table (and base chain since correlated).
  @Listen("svcDataTable__lastClickedColumnIndexEvent")
  setDataTableProperties(e: CustomEvent) {
    this._globalBaseChain.lastClickedColumnIndex = e.detail.index;
    this._globalBaseChain.ordering = e.detail.ordering;
  }

  render() {
    return (
      <Host>
        <h1 class='panic-alerts-overview__title'>ALERTS OVERVIEW</h1>
        <svc-card class="panic-alerts-overview__chain-card">
          <div slot='content' id='expanded' class="panic-alerts-overview__data-table-container">
            {/* Data table */}
            {AlertsOverviewAPI.getDataTableJSX(this.alerts, this._globalBaseChain)}
          </div>
        </svc-card>
      </Host>
    );
  }
}

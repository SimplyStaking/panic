import { Component, Host, h } from '@stencil/core';
import { getDataTableJSX } from '../../utils/alerts-overview';
import { PanicAlertsOverviewInterface } from './panic-alerts-overview.interface';

@Component({
  tag: 'panic-alerts-overview',
  styleUrl: 'panic-alerts-overview.scss'
})
export class PanicAlertsOverview implements PanicAlertsOverviewInterface {

  render() {
    return (
      <Host>
        <h1 class='panic-alerts-overview__title'>ALERTS OVERVIEW</h1>
        <svc-card class="panic-alerts-overview__chain-card">
          <div slot='content' id='expanded'>
            <div class="panic-alerts-overview__data-table-container">
              <div>
                {/* Data table */}
                {getDataTableJSX()}
              </div>
            </div>
          </div>
        </svc-card>
      </Host>
    );
  }
}

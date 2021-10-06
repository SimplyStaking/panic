import { Component, Host, h } from '@stencil/core';
import { PanicAlertsOverviewInterface } from './panic-alerts-overview.interface';


@Component({
    tag: 'panic-alerts-overview',
    styleUrl: 'panic-alerts-overview.scss'
})
export class PanicAlertsOverview implements PanicAlertsOverviewInterface {

    render() {
        return (
            <Host>
                <panic-header />
                <svc-content-container>
                    <h1 class='panic-alerts-overview__title'>ALERTS OVERVIEW</h1>
                </svc-content-container>
                <panic-footer />
            </Host >
        );
    }
}

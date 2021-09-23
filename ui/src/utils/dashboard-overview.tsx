import { h } from '@stencil/core';
import { BaseChain } from '../interfaces/chains';


export const getPieChartJSX = (chainName: string, criticalAlerts: number, warningAlerts: number, errorAlerts: number): any => {
    const hasAlerts = criticalAlerts + warningAlerts + errorAlerts > 0;
    // PieChart config with alerts
    const cols = [{ title: 'Alert', type: 'string' }, { title: 'Amount', type: 'number' }];
    const rows = [['Critical', criticalAlerts], ['Warning', warningAlerts], ['Error', errorAlerts]];
    const alertsColors: string[] = ['#f4dd77', '#f7797b', '#a39293'];
    // PieChart config without alerts
    const noAlertsRows = [['', 1]];
    const noAlertsColors: string[] = ['#b0ea8f'];

    return <svc-pie-chart
        key={hasAlerts ? `${chainName}-pie-chart-no-alerts` : `${chainName}-pie-chart-alerts`}
        slot="small"
        colors={hasAlerts ? alertsColors : noAlertsColors}
        cols={cols}
        rows={hasAlerts ? rows : noAlertsRows}
        pie-slice-text={hasAlerts ? "percentage" : "none"}
        tooltip-trigger={hasAlerts ? "focus" : "none"}
    />
}

export const getSubChainsByBaseChain = (baseChain: BaseChain): { value: string, label: string }[] => {
    return baseChain.chains.map(chain => ({ value: chain.name, label: chain.name }))
}
import { h } from '@stencil/core';
import { Alert, Severity } from '../../../interfaces/alerts';
import { BaseChain } from '../../../interfaces/chains';
import { DataTableRecordType } from '../../../lib/types/types/datatable';
import { OrderingType } from '../../../lib/types/types/ordering';
import { SelectOptionType } from '../../../lib/types/types/select';
import { AlertsAPI } from '../../../utils/alerts';

export const DashboardOverviewAPI = {
    getChainFilterOptionsFromBaseChain: getChainFilterOptionsFromBaseChain,
    getPieChartJSX: getPieChartJSX,
    getDataTableJSX: getDataTableJSX
}

/**
 * Formats base chain to SelectOptionType type.
 * @param baseChain base chain to be converted.
 * @returns populated list of required object type.
 */
function getChainFilterOptionsFromBaseChain(baseChain: BaseChain): SelectOptionType {
    return baseChain.chains.map(chain => ({ label: chain.name, value: chain.name }))
}

/**
 * Gets the JSX for the pie chart.
 * @param chainName the respective chain's name.
 * @param criticalAlerts number of critical alerts.
 * @param warningAlerts number of warning alerts.
 * @param errorAlerts number of error alerts.
 * @returns populated pie chart JSX.
 */
function getPieChartJSX(baseChain: BaseChain): JSX.Element {
    let criticalAlerts: number = 0;
    let warningAlerts: number = 0;
    let errorAlerts: number = 0;

    for (const chain of baseChain.chains) {
        if (chain.active) {
            criticalAlerts += chain.alerts.filter(alert => Severity[alert.severity] === Severity.CRITICAL).length;
            warningAlerts += chain.alerts.filter(alert => Severity[alert.severity] === Severity.WARNING).length;
            errorAlerts += chain.alerts.filter(alert => Severity[alert.severity] === Severity.ERROR).length;
        }
    }

    const hasAlerts: boolean = criticalAlerts + warningAlerts + errorAlerts > 0;
    // PieChart config with alerts
    const cols = [{ title: 'Alert', type: 'string' }, { title: 'Amount', type: 'number' }];
    const rows = [['Critical', criticalAlerts], ['Warning', warningAlerts], ['Error', errorAlerts]];
    const alertsColors: string[] = ['#a39293', '#f4dd77', '#f7797b'];
    // PieChart config without alerts
    const noAlertsRows = [['', 1]];
    const noAlertsColors: string[] = ['#b0ea8f'];

    return <svc-pie-chart
        key={hasAlerts ? `${baseChain.name}-pie-chart-no-alerts` : `${baseChain.name}-pie-chart-alerts`}
        colors={hasAlerts ? alertsColors : noAlertsColors}
        cols={cols}
        rows={hasAlerts ? rows : noAlertsRows}
        pie-slice-text={hasAlerts ? "percentage" : "none"}
        tooltip-trigger={hasAlerts ? "focus" : "none"}
    />
}

/**
 * Gets the JSX for the data table.
 * @param alerts list of alerts to be displayed.
 * @returns populated data table JSX.
 */
function getDataTableJSX(baseChain: BaseChain): JSX.Element {
    let alerts: Alert[] = [];

    for (const chain of baseChain.chains) {
        if (chain.active) {
            alerts.push.apply(alerts, chain.alerts);
        }
    }

    const hasAlerts = alerts.length > 0;
    const cols: string[] = ['Severity', 'Time Stamp', 'Message'];
    const rows: DataTableRecordType = hasAlerts ? getDataTableRecordTypeFromAlerts(alerts, baseChain.activeSeverities) : [];

    return <svc-data-table
        id={baseChain.name}
        key={hasAlerts ? `${baseChain.name}-data-table-no-alerts` : `${baseChain.name}-data-table-alerts`}
        cols={cols}
        rows={rows}
        ordering={baseChain.ordering as OrderingType}
        last-clicked-column-index={baseChain.lastClickedColumnIndex}
        no-records-message="There are no alerts to display at this time"
    />
}

/**
 * Filters alerts which do not have an active severity and formats alerts to DataTableRecordType type.
 * @param alerts list of alerts.
 * @param activeSeverities list of active severities.
 * @returns populated list of lists of required object type.
 */
function getDataTableRecordTypeFromAlerts(alerts: Alert[], activeSeverities: Severity[]): DataTableRecordType {
    // Filter alerts.
    const filteredAlerts = alerts.filter(function (alert) {
        return activeSeverities.includes(alert.severity);
    });

    // Format filtered alerts into DataTableRecordType type.
    return filteredAlerts.map(alert => [
        { label: AlertsAPI.getSeverityIcon(alert.severity), value: alert.severity },
        { label: new Date(alert.timestamp * 1000).toLocaleString(), value: new Date(alert.timestamp * 1000) },
        { label: alert.message, value: alert.message }]);
}

import { h } from '@stencil/core';
import { Alert, BaseChain, Severity } from '../interfaces/chains';
import { DataTableRecordType } from '../lib/types/types/datatable';
import { SelectOptionType } from '../lib/types/types/select';
import { criticalIcon, errorIcon, warningIcon } from './constants';

/**
 * Formats base chain to SelectOptionType type.
 * @param baseChain base chain to be converted.
 * @returns populated list of required object type.
 */
export const getSelectOptionTypeFromBaseChain = (baseChain: BaseChain): SelectOptionType => {
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
export const getPieChartJSX = (chainName: string, criticalAlerts: number, warningAlerts: number, errorAlerts: number): JSX.Element => {
    const hasAlerts = criticalAlerts + warningAlerts + errorAlerts > 0;
    // PieChart config with alerts
    const cols = [{ title: 'Alert', type: 'string' }, { title: 'Amount', type: 'number' }];
    const rows = [['Critical', criticalAlerts], ['Warning', warningAlerts], ['Error', errorAlerts]];
    const alertsColors: string[] = ['#a39293', '#f4dd77', '#f7797b'];
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

/**
 * Gets the JSX for the data table.
 * @param alerts list of alerts to be displayed.
 * @returns populated data table JSX.
 */
export const getDataTableJSX = (chainName: string, alerts: Alert[]): JSX.Element => {
    const hasAlerts = alerts.length > 0;
    const cols: string[] = ['Severity', 'Time Stamp', 'Message'];
    const rows: DataTableRecordType = hasAlerts ? getDataTableRecordTypeFromAlerts(alerts) : [];

    return <svc-data-table
        key={hasAlerts ? `${chainName}-data-table-no-alerts` : `${chainName}-data-table-alerts`}
        cols={cols}
        rows={rows}
        no-records-message="There are no alerts to display at this time"
    />
}

/**
 * Formats alerts to DataTableRecordType type.
 * @param alerts list of alerts.
 * @returns populated list of lists of required object type.
 */
const getDataTableRecordTypeFromAlerts = (alerts: Alert[]): DataTableRecordType => {
    return alerts.map(alert => [
        { label: getSeverityIcon(alert.severity), value: alert.severity },
        { label: new Date(alert.timestamp * 1000).toLocaleString(), value: new Date(alert.timestamp * 1000) },
        { label: alert.message, value: alert.message }]);
}

const getSeverityIcon = (severity: Severity): JSX.Element => {
    switch (severity) {
        case Severity.CRITICAL:
            return criticalIcon;
        case Severity.WARNING:
            return warningIcon;
        case Severity.ERROR:
            return errorIcon;
        default:
            break;
    }
}
import {h} from '@stencil/core';
import {Alert, AlertsCount} from '../../../interfaces/alerts';
import {BaseChain} from '../../../interfaces/chains';
import {FilterState} from '../../../interfaces/filterState';
import {
    DataTableHeaderType,
    DataTableRecordType
} from "@simply-vc/uikit/dist/types/types/datatable";
import {SelectOptionType} from '@simply-vc/uikit/dist/types/types/select';
import {AlertsAPI} from '../../../utils/alerts';
import {ChartColumnType} from '@simply-vc/uikit/dist/types/types/piechart';
import {SeverityAPI} from '../../../utils/severity';
import {ALERTS_DATA_TABLE_HEADER, Severity} from "../../../utils/constants";

export const DashboardOverviewAPI = {
    getChainFilterOptionsFromBaseChain: getChainFilterOptionsFromBaseChain,
    getPieChartJSX: getPieChartJSX,
    getDataTableJSX: getDataTableJSX,
    getCollapsedCardJSX: getCollapsedCardJSX
}

/**
 * Formats base chain to {@link SelectOptionType}.
 * @param baseChain base chain to be converted.
 * @returns populated {@link SelectOptionType} object.
 */
function getChainFilterOptionsFromBaseChain(baseChain: BaseChain): SelectOptionType {
    return baseChain.subChains.map(chain => ({
        label: chain.name,
        value: chain.name
    }))
}

/**
 * Gets the JSX for the pie chart.
 * @param baseChain base chain.
 * @param selectedChains active (selected) chains as an array of strings.
 * @returns populated pie chart {@link JSX.Element}.
 */
function getPieChartJSX(baseChain: BaseChain, selectedChains: string[]): JSX.Element {
    let criticalAlerts: number = 0;
    let warningAlerts: number = 0;
    let errorAlerts: number = 0;
    const noFilter: boolean = selectedChains.length === 0;

    for (const chain of baseChain.subChains) {
        if (noFilter || selectedChains.includes(chain.name)) {
            criticalAlerts += chain.alerts.filter(alert => Severity[alert.severity] === Severity.CRITICAL).length;
            warningAlerts += chain.alerts.filter(alert => Severity[alert.severity] === Severity.WARNING).length;
            errorAlerts += chain.alerts.filter(alert => Severity[alert.severity] === Severity.ERROR).length;
        }
    }

    const hasAlerts: boolean = criticalAlerts + warningAlerts + errorAlerts > 0;
    // PieChart config with alerts
    const cols: ChartColumnType[] = [{
        title: 'Alert',
        type: 'string'
    }, {title: 'Amount', type: 'number'}];
    const rows: any[][] = [['Critical', criticalAlerts], ['Warning', warningAlerts], ['Error', errorAlerts]];
    const alertsColors: string[] = ['#f7797b', '#f4dd77', '#a39293'];
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
 * @param baseChain base chain object which contains various chains with alerts.
 * @param filterState the filter state of the base chain passed.
 * @returns @returns populated data table as {@link JSX.Element}.
 */
function getDataTableJSX(baseChain: BaseChain, filterState: FilterState): JSX.Element {
    let alerts: Alert[] = [];
    const noChainFilterSelected: boolean = filterState.selectedSubChains.length === 0;

    for (const chain of baseChain.subChains) {
        if (noChainFilterSelected || filterState.selectedSubChains.includes(chain.name)) {
            alerts.push.apply(alerts, chain.alerts);
        }
    }

    const hasAlerts = alerts.length > 0;
    const cols: DataTableHeaderType[] = ALERTS_DATA_TABLE_HEADER;
    const rows: DataTableRecordType = hasAlerts ? getDataTableRecordTypeFromAlerts(alerts, filterState.selectedSeverities) : [];

    return <svc-data-table
        id={baseChain.name}
        key={hasAlerts ? `${baseChain.name}-data-table-no-alerts` : `${baseChain.name}-data-table-alerts`}
        cols={cols}
        rows={rows}
        ordering={'descending'}
        last-clicked-column-index={1}
        no-records-message="There are no alerts to display at this time"
    />
}

/**
 * Filters alerts which do not have an active (selected) severity and
 * formats alerts to {@link DataTableRecordType}.
 * @param alerts array of alerts.
 * @param activeSeverities array of active (selected) severities.
 * @returns populated {@link DataTableRecordType} object.
 */
function getDataTableRecordTypeFromAlerts(alerts: Alert[], activeSeverities: Severity[]): DataTableRecordType {
    const noSeverityFilterSelected: boolean = activeSeverities.length === 0;

    // Filter alerts.
    const filteredAlerts = alerts.filter(function (alert) {
        return noSeverityFilterSelected || activeSeverities.includes(alert.severity);
    });

    // Format filtered alerts into DataTableRecordType type.
    return filteredAlerts.map(alert => [
        {
            label: SeverityAPI.getSeverityIcon(alert.severity),
            value: alert.severity
        },
        {
            label: new Date(alert.timestamp * 1000).toLocaleString(),
            value: new Date(alert.timestamp * 1000)
        },
        {label: alert.message, value: alert.message}]);
}

/**
 * Gets the JSX for the collapsed card.
 * @param baseChain base chain object which contains various chains with alerts.
 * @returns populated collapsed card as {@link JSX.Element}.
 */
function getCollapsedCardJSX(baseChain: BaseChain): JSX.Element {
    if (baseChain.subChains.every(chain => chain.alerts.length === 0)) {
        return <svc-label color="success">No issues here! The network is running
            smoothly...</svc-label>
    } else {
        const alertsCount: AlertsCount = AlertsAPI.getAlertsCount(baseChain.subChains);

        return <svc-buttons-container>
            <svc-button
                icon-name="warning" icon-position="icon-only" color="warning"
                badge={alertsCount.warning}
            />
            <svc-button
                icon-name="alert-circle" icon-position="icon-only"
                color="danger"
                badge={alertsCount.error}
            />
            <svc-button
                icon-name="skull" icon-position="icon-only" color="dark"
                badge={alertsCount.critical}
            />
        </svc-buttons-container>
    }
}

import { h } from "@stencil/core";
import { Alert } from "../../../interfaces/alerts";
import { Chain } from "../../../interfaces/chains";
import { DataTableRecordType } from "../../../lib/types/types/datatable";
import { SelectOptionType } from "../../../lib/types/types/select";
import { SeverityAPI } from "../../../utils/severity";
import { ChainsAPI } from "../../../utils/chains";
import { FilterState } from "../../../interfaces/filterState";

export const AlertsOverviewAPI = {
    getChainFilterOptionsFromChains: getChainFilterOptionsFromChains,
    getDataTableJSX: getDataTableJSX
}

/**
 * Formats chains to SelectOptionType type.
 * @param chains chains to be converted.
 * @returns populated list of required object type.
 */
function getChainFilterOptionsFromChains(chains: Chain[]): SelectOptionType {
    return chains.map(chain => ({ label: chain.name, value: chain.name }))
}

/**
 * Gets the JSX for the data table.
 * @param alerts list of alerts to be displayed.
 * @returns populated data table JSX.
 */
function getDataTableJSX(alerts: Alert[], chains: Chain[], filterState: FilterState): JSX.Element {
    let hasAlerts = alerts.length > 0;
    const cols: string[] = ['Severity', 'Time Stamp', 'Message'];
    const rows: DataTableRecordType = hasAlerts ? getDataTableRecordTypeFromAlerts(alerts, chains) : [];
    hasAlerts = rows.length > 0;

    return <svc-data-table
        key={hasAlerts ? 'data-table-no-alerts' : 'data-table-alerts'}
        cols={cols}
        rows={rows}
        last-clicked-column-index={filterState.lastClickedColumnIndex}
        ordering={filterState.ordering}
        no-records-message="There are no alerts to display at this time"
    />
}

/**
 * Filters alerts which do not have an active severity and formats alerts to DataTableRecordType type.
 * @param alerts list of alerts.
 * @param activeSeverities list of active severities.
 * @returns populated list of lists of required object type.
 */
function getDataTableRecordTypeFromAlerts(alerts: Alert[], chains: Chain[]): DataTableRecordType {
    const activeChainsSources: string[] = ChainsAPI.activeChainsSources(chains);

    // Filter alerts by source.
    const filteredAlerts = alerts.filter(function (alert) {
        return activeChainsSources.includes(alert.origin);
    });

    // Format filtered alerts into DataTableRecordType type.
    return filteredAlerts.map(alert => [
        { label: SeverityAPI.getSeverityIcon(alert.severity), value: alert.severity },
        { label: new Date(alert.timestamp * 1000).toLocaleString(), value: new Date(alert.timestamp * 1000) },
        { label: alert.message, value: alert.message }]);
}

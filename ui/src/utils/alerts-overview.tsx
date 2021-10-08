import { h } from "@stencil/core";
import { Alert } from "../interfaces/alerts";
import { BaseChain } from "../interfaces/chains";
import { DataTableRecordType } from "../lib/types/types/datatable";
import { OrderingType } from "../lib/types/types/ordering";
import { AlertsAPI } from "./alerts";

export const AlertsOverviewAPI = {
    getDataTableJSX: getDataTableJSX
}

/**
 * Gets the JSX for the data table.
 * @param alerts list of alerts to be displayed.
 * @returns populated data table JSX.
 */
function getDataTableJSX(alerts: Alert[], globalBaseChain: BaseChain): JSX.Element {
    const hasAlerts = alerts.length > 0;
    const cols: string[] = ['Severity', 'Time Stamp', 'Message'];
    const rows: DataTableRecordType = hasAlerts ? getDataTableRecordTypeFromAlerts(alerts) : [];

    return <svc-data-table
        key={hasAlerts ? 'data-table-no-alerts' : 'data-table-alerts'}
        cols={cols}
        rows={rows}
        ordering={globalBaseChain.ordering as OrderingType}
        last-clicked-column-index={globalBaseChain.lastClickedColumnIndex}
        no-records-message="There are no alerts to display at this time"
    />
}

/**
 * Filters alerts which do not have an active severity and formats alerts to DataTableRecordType type.
 * @param alerts list of alerts.
 * @param activeSeverities list of active severities.
 * @returns populated list of lists of required object type.
 */
function getDataTableRecordTypeFromAlerts(alerts: Alert[]): DataTableRecordType {
    // Format filtered alerts into DataTableRecordType type.
    return alerts.map(alert => [
        { label: AlertsAPI.getSeverityIcon(alert.severity), value: alert.severity },
        { label: new Date(alert.timestamp * 1000).toLocaleString(), value: new Date(alert.timestamp * 1000) },
        { label: alert.message, value: alert.message }]);
}

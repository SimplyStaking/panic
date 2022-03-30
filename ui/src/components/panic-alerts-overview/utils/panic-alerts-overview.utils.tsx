import {h} from "@stencil/core";
import {Alert} from "../../../interfaces/alerts";
import {SubChain, Source} from "../../../interfaces/chains";
import {
    DataTableHeaderType,
    DataTableRecordType
} from "@simply-vc/uikit/dist/types/types/datatable";
import {SelectOptionType} from "@simply-vc/uikit/dist/types/types/select";
import {HelperAPI} from "../../../utils/helpers";
import {SeverityAPI} from "../../../utils/severity";
import {ALERTS_DATA_TABLE_HEADER} from "../../../utils/constants";

export const AlertsOverviewAPI = {
    getChainFilterOptionsFromChains: getChainFilterOptionsFromChains,
    getSourcesFilterOptions: getSourcesFilterOptions,
    getDataTableJSX: getDataTableJSX,
    validateDateTimeOrder: validateDateTimeOrder,
    formatEventData: formatEventData
}

/**
 * Formats sub-chains to {@link SelectOptionType}.
 * @param subChains array of sub-chains to be formatted.
 * @returns populated {@link SelectOptionType} object.
 */
function getChainFilterOptionsFromChains(subChains: SubChain[]): SelectOptionType {
    return subChains.map(chain => ({label: chain.name, value: chain.name}));
}

/**
 * Formats sources to {@link SelectOptionType}.
 * @param sources array of sources to be formatted.
 * @returns populated {@link SelectOptionType} object.
 */
function getSourcesFilterOptions(sources: Source[]): SelectOptionType {
    return sources.map(source => ({label: source.name, value: source.id}));
}

/**
 * Gets the JSX for the data table.
 * @param alerts array of alerts to be displayed.
 * @returns populated data table as {@link JSX.Element}.
 */
function getDataTableJSX(alerts: Alert[]): JSX.Element {
    let hasAlerts = alerts.length > 0;
    const cols: DataTableHeaderType[] = ALERTS_DATA_TABLE_HEADER;
    const rows: DataTableRecordType = hasAlerts ? getDataTableRecordTypeFromAlerts(alerts) : [];
    hasAlerts = rows.length > 0;

    return <svc-data-table
        key={hasAlerts ? 'data-table-no-alerts' : 'data-table-alerts'}
        cols={cols}
        rows={rows}
        last-clicked-column-index={1}
        ordering={"descending"}
        no-records-message={"There are no alerts to display at this time"}
    />
}

/**
 * Gets {@link DataTableRecordType} from an array of alerts.
 * @param alerts array of alerts.
 * @returns populated {@link DataTableRecordType} object.
 */
function getDataTableRecordTypeFromAlerts(alerts: Alert[]): DataTableRecordType {
    return alerts.map(alert => [
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
 * Validates the 'from' and 'to' datetime values where the 'from' datetime value
 * should be smaller than or equal to the 'to' datetime value.
 * @param from from datetime value in string format.
 * @param to to datetime value in string format.
 * @returns true if valid, false if invalid.
 */
function validateDateTimeOrder(from: string, to: string): boolean {
    // Return true if any of the date/time values is not set.
    if (from === '' || to === '') {
        return true;
    }

    return HelperAPI.dateTimeStringToTimestamp(from) <= HelperAPI.dateTimeStringToTimestamp(to);
}

/**
 * Formats the event data generated by the svc-filter/svc-select components.
 * @param eventData event data in string format.
 * @returns formatted event data as an array of strings.
 */
function formatEventData(eventData: string): string[] {
    // Split selected options from event data string using commas.
    const selectedOptions: string[] = eventData.split(',');

    // Remove empty string element from array if no options are selected.
    if (selectedOptions.length > 0 && selectedOptions[0] === '') {
        selectedOptions.pop();
    }

    return selectedOptions;
}

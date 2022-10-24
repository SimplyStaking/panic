import {h} from "@stencil/core";
import {MetricAlert, Metrics} from "../../../interfaces/metrics";
import {
    DataTableHeaderType, DataTableRowsType, DataTableRowCellType
} from "@simply-vc/uikit/dist/types/types/datatable";
import {
    SystemMetricKeys,
    Severity,
    SYSTEM_METRICS_DATA_TABLE_HEADER
} from "../../../utils/constants";

export const SystemsOverviewAPI = {
    getDataTableJSX: getDataTableJSX,
    checkIfAnyNotAvailable: checkIfAnyNotAvailable,
}

/**
 * Gets the JSX for the data table.
 * @param metrics array of metrics.
 * @returns populated data table as {@link JSX.Element}.
 */
function getDataTableJSX(metrics: Metrics[]): JSX.Element {
    const cols: DataTableHeaderType[] = SYSTEM_METRICS_DATA_TABLE_HEADER;
    const rows: DataTableRowsType = getDataTableRowsTypeFromMetrics(metrics);
    let hasMetrics: boolean = metrics.length > 0;

    return <svc-data-table
        key={hasMetrics ? 'data-table-no-alerts' : 'data-table-alerts'}
        cols={cols}
        rows={rows}
        last-clicked-column-index={0}
        ordering={'ascending'}
        no-records-message="There are no metrics to display at this time"
    />
}

/**
 * Gets {@link DataTableRowsType} from an array of metrics.
 * @param metrics array of metrics.
 * @returns populated {@link DataTableRowsType} object.
 */
function getDataTableRowsTypeFromMetrics(metrics: Metrics[]): DataTableRowsType {
    return metrics.map(metric => ({
        cells: [
            {label: metric.name, value: metric.id},
            metricToCellType(metric.metrics.CPU, SystemMetricKeys.SYSTEM_CPU_USAGE, metric.metricAlerts),
            metricToCellType(metric.metrics.RAM, SystemMetricKeys.SYSTEM_RAM_USAGE, metric.metricAlerts),
            metricToCellType(metric.metrics.Storage, SystemMetricKeys.SYSTEM_STORAGE_USAGE, metric.metricAlerts),
            metricToCellType(metric.metrics.ProcessMemory),
            metricToCellType(metric.metrics.ProcessVirtualMemory),
            metricToCellType(metric.metrics.OpenFileDescriptors, SystemMetricKeys.OPEN_FILE_DESCRIPTORS, metric.metricAlerts)
        ],
        id: metric.id
    }));
}

/**
 * Formats metrics to {@link DataTableRowCellType}. If the metric passed is a
 * number, the cell's label is succeeded by a percentage. If the metric key and
 * metric alerts are passed, the css classes field is populated accordingly
 * using {@link checkMetricAlerts}.
 * @param metricValue the value of the metric, can be either a number or a string.
 * @param metricKey the metric key of the passed metric, optional.
 * @param metricAlerts array of metric alerts, optional.
 * @returns populated {@link DataTableRowCellType} object.
 */
function metricToCellType(metricValue: number | string, metricKey?: SystemMetricKeys, metricAlerts?: MetricAlert[]): DataTableRowCellType {
    if (metricValue === undefined || metricValue === null || Number.isNaN(metricValue)) {
        return {label: 'N/A', value: null, cssClasses: ['not-available']};
    }

    const cellType: DataTableRowCellType = {
        label: typeof metricValue === 'number' ? `${metricValue}%` : metricValue,
        value: metricValue
    };

    if (metricKey && metricAlerts) {
        cellType.cssClasses = [checkMetricAlerts(metricKey, metricAlerts)];
    }

    return cellType;
}

/**
 * Returns the status of a given metric based on an array of metric alerts.
 * @param metric metric key being checked.
 * @param metricAlerts array of metric alerts.
 * @returns string with severity of metric or 'INFO' severity if no metric alert
 * is found.
 */
function checkMetricAlerts(metric: SystemMetricKeys, metricAlerts: MetricAlert[]): string {
    const metricAlert: MetricAlert = metricAlerts.find(
      alert => SystemMetricKeys[alert.metric] === metric);

    if (metricAlert !== undefined) {
        return Severity[metricAlert.severity].toLowerCase();
    }

    return Severity.INFO.toLowerCase();
}

/**
 * Checks whether any metric is null (not available).
 * @param metrics array of metrics.
 * @returns true if any metric is null, otherwise returns false.
 */
function checkIfAnyNotAvailable(metrics: Metrics[]): boolean {
    return metrics.some((systemMetric) => {
        return Object.values(systemMetric.metrics).some(
          metric => metric === undefined || metric === null);
    });
}

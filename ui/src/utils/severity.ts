import { Severity } from "../interfaces/severity";
import { SelectOptionObjType, SelectOptionType } from "../lib/types/types/select";
import { criticalIcon, errorIcon, infoIcon, warningIcon } from "./constants";

export const SeverityAPI = {
    getAllSeverityValues: getAllSeverityValues,
    getSeverityFilterOptions: getSeverityFilterOptions,
    getSeverityFilterValue: getSeverityFilterValue,
    getSeverityIcon: getSeverityIcon,
}

/**
 * Returns all severity keys in a list.
 * @param skipInfoSeverity whether to skip info severity (false by default).
 * @returns list of all severity keys.
 */
function getAllSeverityValues(skipInfoSeverity: boolean = false): Severity[] {
    let filtered: string[] = Object.keys(Severity).filter((severity) => {
        return severity !== 'INFO' || (!skipInfoSeverity)
    });

    return filtered.map(severity => severity as Severity);
}

/**
 * Formats Severity enum to SelectOptionType type.
 * @param skipInfoSeverity whether to skip info severity (false by default).
 * @returns populated SelectOptionType object.
 */
function getSeverityFilterOptions(skipInfoSeverity: boolean = false): SelectOptionType {
    let filtered: string[] = Object.keys(Severity).filter((severity) => {
        return severity !== 'INFO' || (!skipInfoSeverity)
    });

    return filtered.map(severity => parseSeverity(Severity[severity], severity))
}

/**
 * Returns the value for the severity filter. If not all severities are chosen, it
 * returns the name of the chosen severities while if all severities are chosen, it
 * returns an empty list. This is the case since no severity should be
 * selected if all severities are active.
 * @returns list of name of all selected severities.
 */
function getSeverityFilterValue(severities: Severity[], skipInfoSeverity: boolean = false): string[] {
    let filtered: string[] = Object.keys(Severity).filter((severity) => {
        return severity !== 'INFO' || (!skipInfoSeverity)
    });

    // If all severities are chosen, set filter to empty.
    if (filtered.length === severities.length) {
        return [];
    }

    // Else return name of chosen severities.
    return severities;
}

/**
 * Parses label and value strings into SelectOptionObjType.
 * @param label label to be parsed.
 * @param value value to be parsed.
 * @returns populated SelectOptionObjType object.
 */
function parseSeverity(label: string, value: string): SelectOptionObjType {
    return { label: label, value: value }
}

/**
 * Returns icon markup as object according to the severity passed.
 * @param severity the alert severity.
 * @returns icon markup as object which corresponds to the severity.
 */
function getSeverityIcon(severity: Severity): Object {
    switch (Severity[severity]) {
        case Severity.CRITICAL: {
            return criticalIcon;
        }
        case Severity.WARNING: {
            return warningIcon;
        }
        case Severity.ERROR: {
            return errorIcon;
        }
        case Severity.INFO: {
            return infoIcon;
        }
        default: {
            return {};
        }
    }
}

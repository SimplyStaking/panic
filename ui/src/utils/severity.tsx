import {h} from "@stencil/core";
import {
    SelectOptionObjType,
    SelectOptionType
} from "@simply-vc/uikit/dist/types/types/select";
import {Severity} from "./constants";

export const SeverityAPI = {
    getAllSeverityValues: getAllSeverityValues,
    getSeverityFilterOptions: getSeverityFilterOptions,
    getSeverityIcon: getSeverityIcon,
}

/**
 * Returns all severity keys in an array.
 * @param skipInfoSeverity whether to skip info severity (false by default).
 * @returns array of all severity keys.
 */
function getAllSeverityValues(skipInfoSeverity: boolean = false): Severity[] {
    let filtered: string[] = Object.keys(Severity).filter((severity) => {
        return severity !== 'INFO' || (!skipInfoSeverity)
    });

    return filtered.map(severity => severity as Severity);
}

/**
 * Formats {@link Severity} enum to {@link SelectOptionType}.
 * @param skipInfoSeverity whether to skip info severity (false by default).
 * @returns populated {@link SelectOptionType} object.
 */
function getSeverityFilterOptions(skipInfoSeverity: boolean = false): SelectOptionType {
    let filtered: string[] = Object.keys(Severity).filter(
        (severity) => {
        return severity !== 'INFO' || (!skipInfoSeverity)
    });

    return filtered.map(severity => parseSeverity(Severity[severity], severity))
}

/**
 * Parses label and value strings into {@link SelectOptionObjType}.
 * @param label label to be parsed.
 * @param value value to be parsed.
 * @returns populated {@link SelectOptionObjType} object.
 */
function parseSeverity(label: string, value: string): SelectOptionObjType {
    return {label: label, value: value}
}

/**
 * Returns icon markup as JSX Element according to the severity passed.
 * @param severity the alert severity.
 * @returns icon markup as {@link JSX.Element} which corresponds to the severity.
 */
function getSeverityIcon(severity: Severity): JSX.Element {

    switch (Severity[severity]) {
        case Severity.ERROR: {
            return (
                <svc-buttons-container>
                    <svc-button iconName={"skull"}
                                iconPosition={"icon-only"}
                                color={"dark"}
                    />
                </svc-buttons-container>
            );
        }
        case Severity.WARNING: {
            return (
                <svc-buttons-container>
                    <svc-button iconName={"warning"}
                                iconPosition={"icon-only"}
                                color={"warning"}
                    />
                </svc-buttons-container>
            );
        }
        case Severity.CRITICAL: {
            return (
                <svc-buttons-container>
                    <svc-button iconName={"alert-circle"}
                                iconPosition={"icon-only"}
                                color={"danger"}
                    />
                </svc-buttons-container>
            );
        }
        case Severity.INFO: {
            return (
                <svc-buttons-container>
                    <svc-button iconName={"alert-circle"}
                                iconPosition={"icon-only"}
                                color={"success"}
                    />
                </svc-buttons-container>
            );
        }
    }
}

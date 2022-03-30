import {Severity} from "../utils/constants";

/**
 * Represents the filter state of a given base chain.
 * Used in the Dashboard Overview component.
 */
export interface FilterState {
    /**
     * Name of base chain which is represented by this filter state.
     */
    readonly chainName: string;
    /**
     * Selected sub-chains as an array of strings.
     */
    selectedSubChains: string[];
    /**
     * Selected severities as an array of {@link Severity} values.
     */
    selectedSeverities: Severity[];
}

/**
 * Represents an extension to the filter state of a given base chain.
 * Used in the Alerts Overview component.
 */
export interface FilterStateV2 extends FilterState {
    /**
     * Selected sources as an array of strings.
     */
    selectedSources: string[];
    /**
     * From date/time value as a string.
     */
    fromDateTime: string;
    /**
     * To date/time value as a string.
     */
    toDateTime: string;
}

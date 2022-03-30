import {Metrics} from "../../interfaces/metrics";

export interface PanicSystemsOverviewInterface {

    /**
     * The name of the selected base chain.
     */
    baseChainName: string,

    /**
     * Array of system metrics for the given base chain name available from the
     * API.
     */
    systemMetrics: Metrics[],

    /**
     * The {@link window.setInterval} ID, necessary to clear the 'time
     * interval' once the component is 'destroyed' (detached from the DOM).
     */
    _updater: number,

    /**
     * How frequent the data is fetched (in milliseconds).
     */
    _updateFrequency: number,
}

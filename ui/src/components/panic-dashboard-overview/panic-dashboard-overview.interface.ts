import { BaseChain } from "../../interfaces/chains";
import { FilterState } from "../../interfaces/filterState";

export interface PanicDashboardOverviewInterface {

    /**
     * The list of base chains available from the API.
     */
    baseChains: BaseChain[],

    /**
     * List of filter state objects which contains the active severities, last clicked column index, and ordering.
     */
    _filterStates: FilterState[],

    /**
     * The {@link window.setInterval} ID, necessary to clear the `time interval` once the component is "destroyed" (detached from the DOM).
     */
    _updater: number,

    /**
     * How frequent (in milliseconds) the alerts data must be fetched.
     */
    _updateFrequency: number
}
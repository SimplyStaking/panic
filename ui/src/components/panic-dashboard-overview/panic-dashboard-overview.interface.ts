import {BaseChain} from "../../interfaces/chains";
import {FilterState} from "../../interfaces/filterState";

export interface PanicDashboardOverviewInterface {

    /**
     * Array of base chains available from the API.
     */
    baseChains: BaseChain[],

    /**
     * Array of filter state objects which contains the active severities.
     */
    _filterStates: FilterState[],

    /**
     * The {@link window.setInterval} ID, necessary to clear the 'time
     * interval' once the component is 'destroyed' (detached from the DOM).
     */
    _updater: number,

    /**
     * How frequent the data is fetched (in milliseconds).
     */
    _updateFrequency: number
}

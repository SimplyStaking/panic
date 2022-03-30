import {Alert} from "../../interfaces/alerts";
import {SubChain} from "../../interfaces/chains";
import {FilterStateV2} from "../../interfaces/filterState";

export interface PanicAlertsOverviewInterface {

    /**
     * Array of alerts available from the API.
     */
    alerts: Alert[],

    /**
     * Array of sub-chains available from the API.
     */
    _subChains: SubChain[],

    /**
     * Filter state object which contains the selected severities, chains,
     * sources, 'from' timestamp, and 'to' timestamp.
     */
    _filterState: FilterStateV2,

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

import { Alert } from "../../interfaces/alerts";
import { Chain } from "../../interfaces/chains";
import { FilterState } from "../../interfaces/filtering";

export interface PanicAlertsOverviewInterface {

    /**
     * The list of alerts available from the API.
     */
    alerts: Alert[],

    /**
     * The list of chains available from the API.
     */
    _chains: Chain[],

    /**
     * Filter state object which contains the active severities, last clicked column index, and ordering.
     */
    _filterState: FilterState,

    /**
     * The {@link window.setInterval} ID, necessary to clear the `time interval` once the component is "destroyed" (detached from the DOM).
     */
    _updater: number,

    /**
     * How frequent (in milliseconds) the alerts data must be fetched.
     */
    _updateFrequency: number,
}

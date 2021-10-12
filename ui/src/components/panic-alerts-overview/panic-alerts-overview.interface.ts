import { Alert } from "../../interfaces/alerts";
import { Chain } from "../../interfaces/chains";

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
     * The {@link window.setInterval} ID, necessary to clear the `time interval` once the component is "destroyed" (detached from the DOM).
     */
    _updater: number,

    /**
     * How frequent (in milliseconds) the alerts data must be fetched.
     */
    _updateFrequency: number,

    /**
     * 
     */
    _activeSeverities: string[],

    /**
     * 
     */
    _lastClickedColumnIndex: number,

    /**
     * 
     */
    _ordering: string
}
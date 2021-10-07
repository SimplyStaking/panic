import { Alert } from "../../interfaces/alerts";
import { BaseChain } from "../../interfaces/chains";

export interface PanicAlertsOverviewInterface {

    /**
     * The global base chain object which stores all available chains from the API.
     */
    _globalBaseChain: BaseChain

    /**
     * The list of alerts available from the API.
     */
    alerts: Alert[]

    /**
     * The {@link window.setInterval} ID, necessary to clear the `time interval` once the component is "destroyed" (detached from the DOM).
     */
    _updater: number,

    /**
     * How frequent (in milliseconds) the alerts data must be fetched.
     */
    _updateFrequency: number
}
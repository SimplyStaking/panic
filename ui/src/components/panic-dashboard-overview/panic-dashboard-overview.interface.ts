import { BaseChain } from "../../interfaces/chains";

export interface PanicDashboardOverviewInterface {

    /**
     * The list of base chains available from the API.
     */
    baseChains: BaseChain[],

    /**
     * The {@link window.setInterval} ID, necessary to clear the `time interval` once the component is "destroyed" (detached from the DOM).
     */
    _updater: number,

    /**
     * How frequent (in milliseconds) the alerts data must be fetched.
     */
    _updateFrequency: number
}
import { BaseChain } from "../../interfaces/chains";

export interface PanicDashboardOverviewInterface {

    /**
     * The list of base chains to be displayed.
     */
    baseChains: BaseChain[],
    
    /**
     * The {@link window.setInterval} ID, necessary to clear the `time interval` once the component is "destroyed" (dettached from the DOM).
     */
    _updater: number,
    
    /**
     * How frequent (in milliseconds) the alerts data must be fetched.
     */
    _updateFrequency: number
}
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

}
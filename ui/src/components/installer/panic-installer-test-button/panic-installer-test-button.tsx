import {Component, h, Prop} from '@stencil/core';
import {HelperAPI} from "../../../utils/helpers";
import {ColorType} from "@simply-vc/uikit/dist/types/types/color";
import {PingsAPI} from "../../../utils/pings";
import {PingPropertiesType, PingResult, ServiceNames} from "../../../utils/types";
import {ChannelsServices, PingStatus, ServiceFullNames, Services} from "../../../utils/constants";

@Component({
    tag: 'panic-installer-test-button',
})
export class PanicInstallerTestButton {

    /**
     * The service to be pinged
     */
    @Prop() service!: ServiceNames;

    /**
     * the arguments to be used to call the ping function
     */
    @Prop() pingProperties!: PingPropertiesType;

    /**
     * the identifier of the service being tested (IP, channel name..)
     */
    @Prop() identifier!: string;

    /**
     * Raises a toast to signify an successful ping.
     */
    raiseSuccessPingToast(): void{
        const color: ColorType = 'success';
        let message: string = '';
        if(this.isChannelService()){
            message = `Test alert successfully sent to ${this.identifier} (${ServiceFullNames[this.service]}).`
        } else {
            message = `Successfully connected to ${this.identifier} (${ServiceFullNames[this.service]}).`
        }

        HelperAPI.raiseToast(message, 5000, color);
    }

    /**
     * Raises a toast to signify an error ping.
     */
    raiseErrorPingToast(): void{
        const color: ColorType = 'danger';
        let message: string = '';
        if(this.isChannelService()){
            message = `Error while sending test alert to ${this.identifier} (${ServiceFullNames[this.service]}).`
        } else {
            message = `Cannot connect with ${this.identifier} (${ServiceFullNames[this.service]}). Please review your input and try again.`
        }

        HelperAPI.raiseToast(message, 5000, color);
    }

    /**
     * Raises a toast to signify a timeout ping.
     */
    raiseTimeoutPingToast(): void{
        const color: ColorType = 'danger';
        const message: string = `Cannot connect with ${ServiceFullNames[this.service]} - Connection timed out. Please review your input and try again.`

        HelperAPI.raiseToast(message, 5000, color);
    }

    /**
     * Raises a toast to signify an internal error.
     * @param error_msg the error message to be shown.
     */
    raiseInternalErrorToast(error_msg: string): void{
        const color: ColorType = 'danger';
        const message: string = `Internal Error - ${error_msg}.`

        HelperAPI.raiseToast(message, 5000, color);
    }

    /**
     * Handle the received ping based on whether it is successful or not.
     * @param ping received
     */
    handlePingReceived(ping: PingResult): void{
        const pingStatus: PingStatus = ping.result;
        if (pingStatus) {
            switch (pingStatus) {
                case PingStatus.SUCCESS:
                    this.raiseSuccessPingToast();
                    break;
                case PingStatus.ERROR:
                    this.raiseErrorPingToast();
                    break;
                case PingStatus.TIMEOUT:
                    this.raiseTimeoutPingToast();
                    break;
                default:
                    this.raiseInternalErrorToast(`Request to ping ${ServiceFullNames[this.service]} failed`);
            }
        } else {
            this.raiseInternalErrorToast(`Request to ping ${ServiceFullNames[this.service]} failed`);
        }
    }

    /**
     * Determines whether the required service to be pinged is a channel service.
     * @returns true if the service is a channel service, false otherwise
     */
    isChannelService(): boolean{
        return ChannelsServices.includes(this.service);
    }

    /**
     * Ping the required service.
     */
    async pingService(): Promise<void>{
        const functionToPing = Services[this.service];
        const ping: PingResult = await PingsAPI.pingEndpoint(functionToPing.endpoint_url, this.pingProperties);
        this.handlePingReceived(ping);
    }

    render() {
        return (
            <svc-button size={'small'} onClick={()=>{
                this.pingService().then();
            }}>
                TEST
            </svc-button>
        );
    }
}

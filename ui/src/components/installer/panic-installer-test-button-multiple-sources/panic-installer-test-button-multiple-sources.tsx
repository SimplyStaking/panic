import {Component, h, Prop} from '@stencil/core';
import {HelperAPI} from "../../../utils/helpers";
import {ColorType} from "@simply-vc/uikit/dist/types/types/color";
import {PingsAPI} from "../../../utils/pings";
import {
    PingPropertiesTypeMultipleSources,
    PingResult,
    PingResultWithProperties,
    ServiceNamesMultipleSources
} from "../../../utils/types";
import {PingStatus, ServiceFullNames, Services} from "../../../utils/constants";

@Component({
    tag: 'panic-installer-test-button-multiple-sources',
})
export class PanicInstallerTestButtonMultipleSources {

    /**
     * The service to be pinged
     */
    @Prop() service!: ServiceNamesMultipleSources;

    /**
     * The list of arguments to be used to make multiple calls to the ping function
     */
    @Prop() pingProperties!: PingPropertiesTypeMultipleSources[];

    /**
     * Whether one valid source is sufficient for a successful toast
     */
    @Prop() oneValidSourceIsSufficient?: boolean = false;

    /**
     * Raises a toast to signify an successful ping.
     */
    raiseSuccessPingToast(): void{
        const color: ColorType = 'success';
        let message: string = '';
        if (this.service === 'twilio'){
            message = `Calling all telephone numbers via (${ServiceFullNames[this.service]}).`
        } else if (this.service === 'email') {
            message = `All test e-mails sent successfully, kindly check corresponding inboxes.`
        } else if (this.oneValidSourceIsSufficient) {
            message = `Successfully connected with at least one ${ServiceFullNames[this.service]} source.`
        } else {
            message = `Successfully connected with all ${ServiceFullNames[this.service]} sources.`
        }
        HelperAPI.raiseToast(message, 5000, color);
    }

    /**
     * Raises a toast to signify an error ping.
     */
    raiseErrorPingToast(failedSources: string): void{
        const color: ColorType = 'danger';
        let message: string = '';
        switch (this.service) {
            case 'twilio':
                message = `Error while calling the following telephone numbers via ${ServiceFullNames[this.service]}:${failedSources}`;
                break;
            case 'email':
                message = `Error while sending test e-mails:${failedSources}`;
                break;
            default:
                message = `Cannot connect with the following ${ServiceFullNames[this.service]} sources:${failedSources}`;
        }
        HelperAPI.raiseToast(message, 5000, color);
    }

    /**
     * Raises a toast to signify that no sources were inputted.
     */
    raiseNoSourcesToast(): void{
        const color: ColorType = 'danger';
        let message: string = `No ${ServiceFullNames[this.service]} data to test`;
        HelperAPI.raiseToast(message, 5000, color);
    }

    /**
     * Parses the failed pings into a string message to be returned to the user.
     * @param failedPings array of ping result with properties objects to be parsed
     * @returns message with details of failed pings as a string
     */
    getFailedPingsMessage(failedPings: PingResultWithProperties[]): string {
        let failedSourcesString: string = '';

        failedPings.forEach((failedPing) => {
            if (!failedPing.result || failedPing.result === PingStatus.ERROR) {
                switch (this.service) {
                    case 'twilio':
                        //@ts-ignore
                        failedSourcesString += `\n${failedPing.pingProperties.phoneNumberToDial}: Failed`;
                        break;
                    case 'email':
                        //@ts-ignore
                        failedSourcesString += `\n${failedPing.pingProperties.to}: Failed`;
                        break;
                    case 'prometheus':
                        //@ts-ignore
                        failedSourcesString += `\n${failedPing.pingProperties.url}: Failed`;
                        break;
                }
            } else {
                switch (this.service) {
                    case 'twilio':
                        //@ts-ignore
                        failedSourcesString += `\n${failedPing.pingProperties.phoneNumberToDial}: Timed out`;
                        break;
                    case 'email':
                        //@ts-ignore
                        failedSourcesString += `\n${failedPing.pingProperties.to}: Timed out`;
                        break;
                    case 'prometheus':
                        //@ts-ignore
                        failedSourcesString += `\n${failedPing.pingProperties.url}: Timed out`;
                        break;
                }
            }
        });

        return failedSourcesString;
    }

    /**
     * Handle the received pings based on whether they are successful or not.
     * @param pings
     */
    handlePingsReceived(pings: PingResultWithProperties[]): void{
        if (pings.length === 0) {
            this.raiseNoSourcesToast();
        } else if (pings.every(ping => ping.result && ping.result === PingStatus.SUCCESS)) {
            // All sources valid
            this.raiseSuccessPingToast();
        } else {
            const failedPings = pings.filter(ping => !ping.result || ping.result !== PingStatus.SUCCESS);

            if (failedPings.length < pings.length && this.oneValidSourceIsSufficient) {
                // Only one source valid but alert success since one is sufficient
                this.raiseSuccessPingToast();
            } else {
                // Some or all pings failed
                const failedSourcesString = this.getFailedPingsMessage(failedPings);

                this.raiseErrorPingToast(failedSourcesString);
            }
        }
    }

    /**
     * Ping the required services.
     */
    async pingServices(): Promise<void>{
        const functionToPing = Services[this.service];
        const pingsResult: PingResult[] = await PingsAPI.pingEndpointsConcurrently(
            functionToPing.endpoint_url, this.pingProperties);

        const pingsResultWithProperties: PingResultWithProperties[] = pingsResult as PingResultWithProperties[];

        for (let i = 0; i < pingsResultWithProperties.length; i++) {
            pingsResultWithProperties[i].pingProperties = this.pingProperties[i];
        }

        this.handlePingsReceived(pingsResultWithProperties);
    }

    render() {
        return (
            <svc-button size={'small'} onClick={()=>{
                this.pingServices().then();
            }}>
                TEST
            </svc-button>
        );
    }
}

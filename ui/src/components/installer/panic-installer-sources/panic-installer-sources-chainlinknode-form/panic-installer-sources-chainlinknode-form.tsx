import {Component, h, Host, Listen, Prop, State} from '@stencil/core';
import {NodeSubconfig} from "../../../../../../entities/ts/NodeSubconfig";

@Component({
    tag: 'panic-installer-sources-chainlinknode-form',
    styleUrl: 'panic-installer-sources-chainlinknode-form.scss'
})
export class PanicInstallerSourcesChainlinkNodeForm {

    @Prop() node: NodeSubconfig;
    @State() prometheusUrlsToPing: string[] = []

    @State() _enableMonitorPrometheus: boolean = true;

    updatePrometheusUrlsToPing(prometheusURLs: string[]): void{
        this.prometheusUrlsToPing = [...prometheusURLs];
    }

    updateEnableMonitorPrometheus(bool: boolean): void{
      this._enableMonitorPrometheus = bool;
    }

    @Listen("AddedPrometheusURL", {target: "window"})
    addedPrometheusURLHandler(event: CustomEvent): void {
        this.prometheusUrlsToPing.push(event.detail.value);
        this.updatePrometheusUrlsToPing(this.prometheusUrlsToPing);
    }

    @Listen("RemovedPrometheusURL", {target: "window"})
    removedPrometheusURLHandler(event: CustomEvent): void {
        const index = this.prometheusUrlsToPing.indexOf(event.detail.value, 0);
        if (index > -1) {
            this.prometheusUrlsToPing.splice(index, 1);
        }
        this.updatePrometheusUrlsToPing(this.prometheusUrlsToPing);
    }

    @Listen("monitorPrometheus", {target: "window"})
    monitorPrometheusHandler(event: CustomEvent){
      this.updateEnableMonitorPrometheus(event.detail.checked);
    }

    componentWillLoad(){
        if (this.node) {
            const prometheusURLs: string[] = this.node.nodePrometheusUrls !== "" ?
                this.node.nodePrometheusUrls.split(',') : [];
            this.updatePrometheusUrlsToPing(prometheusURLs);
            if(!this.node.monitorPrometheus){
              this.updateEnableMonitorPrometheus(false);
            }
        }
    }

    render() {
        return (
            <Host>
                {this.node && <input type={"hidden"} value={this.node.id} name={"id"}/>}
                <svc-input
                    name={'name'}
                    placeholder={`chainlink_node_1(IP)`}
                    label={'Node Name'}
                    lines={'inset'}
                    required={true}
                    value={this.node?.name}
                />
                <div class={"panic-installer-sources-form__help-text"}>
                    <span>This unique identifier will be used to identify your node.</span>
                </div>

                <div class={'panic-installer-sources-form__row-container'}>

                  <div class={"panic-installer-sources-form__input_test_box"}>
                    <svc-multiple-input
                        name={'nodePrometheusUrls'}
                        value={this.prometheusUrlsToPing.map((url => {
                            return {label: url, value: url, outline: true}
                        }))}
                        label={'Prometheus URLs'}
                        placeholder={'https://IP:6688/metrics [Press Enter after each URL]'}
                        outline={true}
                        type={"url"}
                        addEventName={"AddedPrometheusURL"}
                        removeEventName={"RemovedPrometheusURL"}
                        disabled={!this._enableMonitorPrometheus}
                    />
                    <svc-toggle
                        name={'monitorPrometheus'}
                        onChangeEventName={'monitorPrometheus'}
                        value={true}
                        label={'Monitor'}
                        lines={'none'}
                        checked={this.node ? this.node.monitorPrometheus : true}
                    />
                    <panic-installer-test-button-multiple-sources
                        service={'prometheus'}
                        pingProperties={this.prometheusUrlsToPing.map((url => {
                            return {url, baseChain: 'chainlink'}
                        }))}
                        oneValidSourceIsSufficient={true}
                    />
                  </div>
                </div>
                <div class={"panic-installer-sources-form__help-text"}>
                    <span>These are the prometheus URLs of your node.</span>
                </div>

                <svc-toggle
                    name={'monitorNode'}
                    value={true}
                    label={'Monitor Node'}
                    lines={'inset'}
                    helpText={'Whether to monitor this configured node.'}
                    checked={this.node ? this.node.monitorNode : true}
                />
            </Host>
        );
    }
}

import {Component, Host, h, Prop, State, Listen} from '@stencil/core';
import {NodeSubconfig} from "../../../../../../entities/ts/NodeSubconfig";

@Component({
  tag: 'panic-installer-sources-substratenode-form',
  styleUrl: 'panic-installer-sources-substratenode-form.scss'
})
export class PanicInstallerSourcesSubstrateNodeForm {

    @Prop() node: NodeSubconfig;
    @State() websocketUrlToPing: string;
    @State() nodeExporterUrlToPing: string;

    @State() _enableMonitorNode: boolean = true;
    @State() _enableMonitorSystem: boolean = true;
    @State() _enableIsValidator: boolean = true;

    @Listen("monitorNode", {target: "window"})
    monitorNodeHandler(event: CustomEvent){
      this.updateEnableMonitorNode(event.detail.checked);
    }

    @Listen("monitorSystem", {target: "window"})
    monitorSystemHandler(event: CustomEvent){
      this.updateEnableMonitorSystem(event.detail.checked);
    }

    @Listen("isValidator", {target: "window"})
    monitorIsValidator(event: CustomEvent){
      this.updateEnableIsValidator(event.detail.checked);
    }

    updateWebsocketUrlToPing(url: string): void{
        this.websocketUrlToPing = url;
    }

    updateNodeExporterUrlToPing(url: string): void{
        this.nodeExporterUrlToPing = url;
    }

    updateEnableMonitorNode(bool: boolean): void{
      this._enableMonitorNode = bool;
    }

    updateEnableMonitorSystem(bool: boolean): void{
      this._enableMonitorSystem = bool;
    }

    updateEnableIsValidator(bool: boolean): void{
      this._enableIsValidator= bool;
    }

    componentWillLoad(){
        if (this.node) {
            this.updateWebsocketUrlToPing(this.node.nodeWsUrl);
            this.updateNodeExporterUrlToPing(this.node.exporterUrl);
            if(!this.node.monitorNode){
              this.updateEnableMonitorNode(false);
            }
            if(!this.node.monitorSystem){
              this.updateEnableMonitorSystem(false);
            }
            if(!this.node.isValidator){
              this.updateEnableIsValidator(false)
            }
        }
    }

    render() {
        return (
            <Host>
                { this.node && <input type={"hidden"} value={this.node.id} name={"id"} /> }
                <svc-input
                    name={'name'}
                    placeholder={`substrate_node_1(IP)`}
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
                    <svc-input
                        name={'nodeWsUrl'}
                        label={'Node WebSocket URL'}
                        lines={'inset'}
                        placeholder={'ws://IP:9944'}
                        required={true}
                        value={this.node?.nodeWsUrl}
                        type={'url'}
                        disabled={!this._enableMonitorNode}
                        //@ts-ignore
                        onInput={(event) => this.updateWebsocketUrlToPing(event.target.value)}
                    />
                    <svc-toggle
                        name={'monitorNode'}
                        onChangeEventName={'monitorNode'}
                        value={true}
                        label={'Monitor'}
                        lines={'none'}
                        checked={this.node ? this.node.monitorNode : true}
                        id={'monitor_ws'}
                    />
                    <panic-installer-test-button
                        service={'substrate-websocket'}
                        pingProperties={{'url': this.websocketUrlToPing}}
                        identifier={this.websocketUrlToPing}
                    />
                  </div>
                </div>
                <div class={"panic-installer-sources-form__help-text"}>
                    <span>This IP address will be used to monitor substrate node statistics, if omitted they will not be monitored and alerted on.</span>
                </div>

                <div class={'panic-installer-sources-form__row-container'}>

                  <div class={"panic-installer-sources-form__input_test_box"}>
                    <svc-input
                        name={'exporterUrl'}
                        label={'Node Exporter URL'}
                        lines={'inset'}
                        type={'url'}
                        placeholder={'https://IP:9100/metrics'}
                        required={true}
                        value={this.node?.exporterUrl}
                        disabled={!this._enableMonitorSystem}
                        //@ts-ignore
                        onInput={(event) => this.updateNodeExporterUrlToPing(event.target.value)}
                    />
                    <svc-toggle
                        name={'monitorSystem'}
                        onChangeEventName={'monitorSystem'}
                        value={true}
                        label={'Monitor'}
                        lines={'none'}
                        checked={this.node ? this.node.monitorSystem : true}
                    />
                    <panic-installer-test-button
                        service={'node-exporter'}
                        pingProperties={{'url': this.nodeExporterUrlToPing}}
                        identifier={this.nodeExporterUrlToPing}
                    />
                  </div>
                </div>
                <div class={"panic-installer-sources-form__help-text"}>
                    <span>This IP address will be used to monitor node exporter statistics, if omitted they will not be monitored and alerted on.</span>
                </div>

                <div class={'panic-installer-sources-form__row-container'}>

                  <div class={"panic-installer-sources-form__input_test_box"}>
                    <svc-input
                        name={'stashAddress'}
                        value={this.node?.stashAddress}
                        label={'Stash Address'}
                        required={true}
                        lines={'inset'}
                        placeholder={'EDDJBTFGdsg0gh8sd0sdsda2asd12dasdafs'}
                        disabled={!this._enableIsValidator}
                    />
                    <svc-toggle
                        name={'isValidator'}
                        onChangeEventName={'isValidator'}
                        value={true}
                        label={'Node Is Validator'}
                        lines={'none'}
                        checked={this.node ? this.node.isValidator : true}
                    />
                  </div>
                </div>
                <div class={"panic-installer-sources-form__help-text"}>
                    <span>This will be used to monitor the stash address account.</span>
                </div>

                <div class={'panic-installer-sources-form__row-container'}>
                    <svc-toggle
                        name={'isArchiveNode'}
                        value={true}
                        label={'Is Archive Node'}
                        lines={'none'}
                        helpText={'Whether the node you are setting up is an archive node.'}
                        checked={this.node ? this.node.isArchiveNode : true}
                    />
                    <svc-toggle
                        name={'useAsDataSource'}
                        value={true}
                        label={'Use as Data Source'}
                        lines={'none'}
                        helpText={'Whether to retrieve blockchain data from this node.'}
                        checked={this.node ? this.node.useAsDataSource : true}
                    />
                </div>
            </Host>
        );
    }
}

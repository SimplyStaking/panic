import {Component, Host, h, Prop, State, Listen} from '@stencil/core';
import {NodeSubconfig} from "../../../../../../entities/ts/NodeSubconfig";

@Component({
  tag: 'panic-installer-sources-cosmosnode-form',
  styleUrl: 'panic-installer-sources-cosmosnode-form.scss'
})
export class PanicInstallerSourcesFormCosmosNode {

    @Prop() node: NodeSubconfig;
    @State() cosmosRestUrlToPing: string;
    @State() prometheusUrlToPing: string;
    @State() tendermintRpcUrlToPing: string;
    @State() nodeExporterUrlToPing: string;

    @State() _enableMonitorCosmosRest: boolean = true;
    @State() _enableMonitorPrometheus: boolean = true;
    @State() _enableMonitorSystem: boolean = true;
    @State() _enableMonitorTendermintRpc: boolean = true;
    @State() _enableOperatorAddress: boolean = true;

    updateCosmosRestUrlToPing(url: string): void{
        this.cosmosRestUrlToPing = url;
    }

    updatePrometheusUrlToPing(url: string): void{
        this.prometheusUrlToPing = url;
    }

    updateTendermintUrlToPing(url: string): void{
        this.tendermintRpcUrlToPing = url;
    }

    updateNodeExporterUrlToPing(url: string): void{
        this.nodeExporterUrlToPing = url;
    }

    updateEnableMonitorCosmosRest(bool: boolean): void {
      this._enableMonitorCosmosRest = bool;
    }

    updateEnableMonitorPrometheus(bool: boolean): void {
      this._enableMonitorPrometheus = bool;
    }

    updateEnableMonitorSystem(bool: boolean): void {
      this._enableMonitorSystem = bool;
    }

    updateEnableMonitorTendermintRpc(bool: boolean): void {
      this._enableMonitorTendermintRpc = bool;
    }

    updateEnableMonitorOperatorAddress(bool: boolean): void {
      this._enableOperatorAddress = bool;
    }

    @Listen("monitorCosmosRest", {target: "window"})
    monitorCosmosRestHandler(event: CustomEvent){
      this.updateEnableMonitorCosmosRest(event.detail.checked);
    }

    @Listen("monitorPrometheus", {target: "window"})
    monitorPrometheusHandler(event: CustomEvent){
      this.updateEnableMonitorPrometheus(event.detail.checked);
    }

    @Listen("monitorSystem", {target: "window"})
    monitorSystemHandler(event: CustomEvent){
      this.updateEnableMonitorSystem(event.detail.checked);
    }

    @Listen("monitorTendermintRpc", {target: "window"})
    monitorTendermintRpcHandler(event: CustomEvent){
      this.updateEnableMonitorTendermintRpc(event.detail.checked);
    }

    @Listen("isValidator", {target: "window"})
    isValidatorHandler(event: CustomEvent){
      this.updateEnableMonitorOperatorAddress(event.detail.checked);
    }

    componentWillLoad(){
        if (this.node) {
            this.updateCosmosRestUrlToPing(this.node.cosmosRestUrl);
            this.updatePrometheusUrlToPing(this.node.prometheusUrl);
            this.updateTendermintUrlToPing(this.node.tendermintRpcUrl);
            this.updateNodeExporterUrlToPing(this.node.exporterUrl);
            if(!this.node.monitorCosmosRest){
              this.updateEnableMonitorCosmosRest(false);
            }
            if(!this.node.monitorPrometheus){
              this.updateEnableMonitorPrometheus(false);
            }
            if(!this.node.monitorSystem){
              this.updateEnableMonitorSystem(false);
            }
            if(!this.node.monitorTendermintRpc){
              this.updateEnableMonitorTendermintRpc(false);
            }
            if(!this.node.isValidator){
              this.updateEnableMonitorOperatorAddress(false);
            }
        }
    }

    render() {
        return (
            <Host>
                { this.node && <input type={"hidden"} value={this.node.id} name={"id"} /> }
                <svc-input
                    value={this.node?.name}
                    name={'name'}
                    placeholder={"cosmos_node_1(IP)"}
                    label={'Node Name'}
                    lines={'inset'}
                    required={true}
                />
                <div class={"panic-installer-sources-form__help-text"}>
                    <span>This unique identifier will be used to identify your node.</span>
                </div>

                <div class={'panic-installer-sources-form__row-container'}>

                    <div class={"panic-installer-sources-form__input_test_box"}>
                        <svc-input
                            name={'cosmosRestUrl'}
                            label={'Cosmos Rest URL'}
                            type={'url'}
                            lines={"inset"}
                            placeholder={'https://IP:1317'}
                            required={true}
                            value={this.node?.cosmosRestUrl}
                            disabled={!this._enableMonitorCosmosRest}
                            //@ts-ignore
                            onInput={(event) => this.updateCosmosRestUrlToPing(event.target.value)}
                        />
                        <svc-toggle
                            name={'monitorCosmosRest'}
                            onChangeEventName={'monitorCosmosRest'}
                            value={true}
                            label={'Monitor'}
                            lines={"none"}
                            checked={this.node ? this.node.monitorCosmosRest : true}
                        />
                        <panic-installer-test-button
                            service={'cosmos-rest'}
                            pingProperties={{'url': this.cosmosRestUrlToPing}}
                            identifier={this.cosmosRestUrlToPing}
                        />
                    </div>
                </div>
                <div class={"panic-installer-sources-form__help-text"}>
                    <span>This IP address will be used to monitor cosmos SDK based statistics, if omitted they will not be monitored and alerted on.</span>
                </div>

                <div class={'panic-installer-sources-form__row-container'}>

                    <div class={"panic-installer-sources-form__input_test_box"}>
                        <svc-input
                            type={'url'}
                            name={'prometheusUrl'}
                            label={'Prometheus Endpoint URL'}
                            lines={"inset"}
                            placeholder={'https://IP:26660/metrics'}
                            required={true}
                            value={this.node?.prometheusUrl}
                            disabled={!this._enableMonitorPrometheus}
                            //@ts-ignore
                            onInput={(event) => this.updatePrometheusUrlToPing(event.target.value)}
                        />
                        <svc-toggle
                            name={'monitorPrometheus'}
                            onChangeEventName={'monitorPrometheus'}
                            value={true}
                            label={'Monitor'}
                            lines={"none"}
                            checked={this.node ? this.node.monitorPrometheus : true}
                        />
                        <panic-installer-test-button
                            service={'prometheus'}
                            pingProperties={{'url': this.prometheusUrlToPing, 'baseChain': 'cosmos'}}
                            identifier={this.prometheusUrlToPing}
                        />
                    </div>
                </div>
                <div class={"panic-installer-sources-form__help-text"}>
                    <span>This IP address will be used to monitor prometheus based statistics, if omitted they will not be monitored and alerted on.</span>
                </div>

                <div class={'panic-installer-sources-form__row-container'}>

                    <div class={"panic-installer-sources-form__input_test_box"}>
                        <svc-input
                            name={'exporterUrl'}
                            type={'url'}
                            label={'Node Exporter URL'}
                            lines={"inset"}
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
                            lines={"none"}
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
                            name={'tendermintRpcUrl'}
                            type={'url'}
                            label={'Tendermint RPC URL'}
                            lines={"inset"}
                            placeholder={'https://IP:26657'}
                            required={true}
                            value={this.node?.tendermintRpcUrl}
                            disabled={!this._enableMonitorTendermintRpc}
                            //@ts-ignore
                            onInput={(event) => this.updateTendermintUrlToPing(event.target.value)}
                        />
                        <svc-toggle
                            name={'monitorTendermintRpc'}
                            onChangeEventName={'monitorTendermintRpc'}
                            value={true}
                            label={'Monitor'}
                            lines={"none"}
                            checked={this.node ? this.node.monitorTendermintRpc : true}
                        />
                        <panic-installer-test-button
                            service={'tendermint-rpc'}
                            pingProperties={{'url': this.tendermintRpcUrlToPing}}
                            identifier={this.tendermintRpcUrlToPing}
                        />
                    </div>
                </div>
                <div class={"panic-installer-sources-form__help-text"}>
                    <span>This IP address will be used to obtain metrics from the Tendermint endpoint, if omitted they wil not be monitored and alerted on.</span>
                </div>

                <div class={'panic-installer-sources-form__row-container'}>
                    <svc-input
                        name={'operatorAddress'}
                        label={'Operator Address'}
                        lines={"inset"}
                        placeholder={'cosmosvaloper124maqmcqv8tquy764ktz7cu0gxnzfw54n3vww8'}
                        required={true}
                        value={this.node?.operatorAddress}
                        disabled={!this._enableOperatorAddress}
                    />
                    <svc-toggle
                        name={'isValidator'}
                        onChangeEventName={'isValidator'}
                        value={true}
                        label={'Node Is Validator'}
                        lines={"none"}
                        checked={this.node ? this.node.isValidator : true}
                    />
                </div>
                <div class={"panic-installer-sources-form__help-text"}>
                    <span>This is the validator address of the node you are monitoring.</span>
                </div>

                <div class={'panic-installer-sources-form__row-container'}>
                    <svc-toggle
                        name={'isArchiveNode'}
                        value={true}
                        label={'Is Archive Node'}
                        checked={this.node ? this.node.isArchiveNode : true}
                        lines={"none"}
                        helpText={'Whether the node you are setting up is an archive node.'}
                    />

                    <svc-toggle
                        name={'monitorNode'}
                        value={true}
                        label={'Monitor Node'}
                        checked={this.node ? this.node.monitorNode : true}
                        lines={"none"}
                        helpText={'Whether to monitor this configured node.'}
                    />

                    <svc-toggle
                        name={'useAsDataSource'}
                        value={true}
                        label={'Use as Data Source'}
                        checked={this.node ? this.node.useAsDataSource : true}
                        lines={"none"}
                        helpText={'Whether to retrieve blockchain data from this node.'}
                    />
                </div>
            </Host>
        );
    }
}

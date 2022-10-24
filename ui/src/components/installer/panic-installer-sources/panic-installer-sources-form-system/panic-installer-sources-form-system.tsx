import {Component, Host, h, Prop, State} from '@stencil/core';
import {BaseChain} from "../../../../../../entities/ts/BaseChain";
import {SystemSubconfig} from "../../../../../../entities/ts/SystemSubconfig";

@Component({
  tag: 'panic-installer-sources-form-system',
  styleUrl: 'panic-installer-sources-form-system.scss'
})
export class PanicInstallerSourcesFormSystem {

    @Prop() baseChain: BaseChain;
    @Prop() system: SystemSubconfig;
    @State() nodeExporterUrlToPing: string;

    updateNodeExporterUrlToPing(url: string): void{
        this.nodeExporterUrlToPing = url;
    }

    render() {
        return (
            <Host>
                { this.system && <input type={"hidden"} value={this.system.id} name={"id"} /> }
                <svc-input
                    name={'name'}
                    value={this.system?.name}
                    placeholder={`${this.baseChain?.value}_system_1`}
                    label={'System Name'}
                    lines={'inset'}
                    required={true}
                />
                <div class={"panic-installer-sources-form__help-text"}>
                    <span>This will be used to identify the current System configuration.</span>
                </div>

                <div class={"panic-installer-sources-form__input_test_box"}>
                    <svc-input
                        name={'exporterUrl'}
                        value={this.system?.exporterUrl}
                        type={'url'}
                        placeholder={'https://IP:9100/metrics'}
                        label={'Node Exporter URL'}
                        lines={'inset'}
                        required={true}
                        //@ts-ignore
                        onChange={(event) => this.updateNodeExporterUrlToPing(event.target.value)}
                    />
                    <panic-installer-test-button
                        service={'node-exporter'}
                        pingProperties={{'url': this.nodeExporterUrlToPing}}
                        identifier={this.nodeExporterUrlToPing}
                    />
                </div>
                <div class={"panic-installer-sources-form__help-text"}>
                    <span>This is the node exporter URL of your system.</span>
                </div>

                <svc-toggle
                    name={'monitor'}
                    value={true}
                    label={'Monitor System'}
                    checked={this.system ? this.system.monitor : true}
                    lines={'inset'}
                />
                <div class={"panic-installer-sources-form__help-text"}>
                    <span>Whether to monitor this configured system.</span>
                </div>
            </Host>
        )
    }
}

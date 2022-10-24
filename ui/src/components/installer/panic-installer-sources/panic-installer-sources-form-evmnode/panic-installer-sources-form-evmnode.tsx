import {Component, h, Host, Prop, State} from '@stencil/core'
import {EVMNodeSubconfig} from "../../../../../../entities/ts/EVMNodeSubconfig";

@Component({
    tag: 'panic-installer-sources-form-evmnode',
    styleUrl: 'panic-installer-sources-form-evmnode.scss'
})
export class PanicInstallerSourcesEVMNode {

    @Prop() node: EVMNodeSubconfig;
    @State() rpcUrlToPing: string;

    updateRpcUrlToPing(url: string): void{
        this.rpcUrlToPing = url;
    }

    componentWillLoad(){
        if (this.node) {
            this.updateRpcUrlToPing(this.node.nodeHttpUrl);
        }
    }

    render() {
        return (
            <Host>
                { this.node && <input type={"hidden"} value={this.node.id} name={"id"} /> }
                <svc-input
                    name={'name'}
                    value={this.node?.name}
                    placeholder={`chainlink_evm_node_1(IP)`}
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
                            name={'nodeHttpUrl'}
                            value={this.node?.nodeHttpUrl}
                            type={'url'}
                            placeholder={'https://IP:8545'}
                            label={'RPC URL'}
                            lines={'inset'}
                            required={true}
                            //@ts-ignore
                            onInput={(event) => this.updateRpcUrlToPing(event.target.value)}
                        />
                        <panic-installer-test-button
                            service={'ethereum-rpc'}
                            pingProperties={{'url': this.rpcUrlToPing}}
                            identifier={this.rpcUrlToPing}
                        />
                    </div>
                </div>

                <div class={"panic-installer-sources-form__help-text"}>
                    <span>This IP address will be used to monitor prometheus based metrics, if omitted they will not be monitored and alerted on.</span>
                </div>

                <svc-toggle
                    name={'monitor'}
                    value={true}
                    label={'Monitor Node'}
                    lines={'inset'}
                    helpText={'Whether to monitor this configured node.'}
                    checked={this.node ? this.node.monitor : true}
                />
            </Host>
        )
    }
}

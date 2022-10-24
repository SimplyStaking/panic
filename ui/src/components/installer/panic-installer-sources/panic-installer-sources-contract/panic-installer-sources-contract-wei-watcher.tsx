import {SelectOptionType} from '@simply-vc/uikit/dist/types/types/select';
import {Component, h, Host, Prop} from '@stencil/core';
import {HelperAPI} from '../../../../utils/helpers';
import {ContractSubconfig} from "../../../../../../entities/ts/ContractSubconfig";

@Component({
  tag: 'panic-installer-sources-contract-wei-watcher'
})
export class PanicInstallerSourcesContractWeiWatcher {

  @Prop() contractNetworkOptions: SelectOptionType;
  @Prop() contract: ContractSubconfig;

  render() {
    return (
      <Host>
        <div class={"panic-installer-sources-contract__network-add-container"}>
          <svc-select
            name={'name'}
            header={'Network Name'}
            withBorder={true}
            placeholder={'Network Name'}
            options={this.contractNetworkOptions}
            value={this.contract?.url}
            // @ts-ignore
            onIonChange={(e: CustomEvent) => {
              HelperAPI.emitEvent("networkChange", e.detail.value);
            }}
          />
          <svc-buttons-container>
            <svc-button
              iconName={'add-circle'}
              iconPosition={"icon-only"}
              color={"primary"}
              onClick={() => {
                HelperAPI.emitEvent("openCustomWeiWatcherForm");
              }}
            />
          </svc-buttons-container>
        </div>

        <div>
          <svc-input
            name={'url'}
            disabled={true}
            label={'WeiWatchers URL'}
            labelColor={'primary'}
            lines={'inset'}
            value={this.contract?.url}
          />

          <svc-toggle
            name={'monitor'}
            value={true}
            checked={this.contract?.monitor}
            disabled={this.contract?.url === ""}
            position={'end'}
            label={'Enable Contract Monitoring'}
            htmlID={'monitor_contracts'}
            helpText={'Whether to monitor price feed contract for this chain.'}
            lines={'none'}
            // @ts-ignore
            onIonChange={(e: CustomEvent) => {
              HelperAPI.emitEvent("enableContractMonitoring", e.detail);
            }}
          />
        </div>
      </Host>
    );
  }
}
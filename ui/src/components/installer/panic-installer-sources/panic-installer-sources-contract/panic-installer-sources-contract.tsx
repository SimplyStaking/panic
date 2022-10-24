import {createModal} from '@simply-vc/uikit';
import {SelectOptionObjType, SelectOptionType} from '@simply-vc/uikit/dist/types/types/select';
import {Component, h, Listen, Prop, State} from '@stencil/core';
import {HelperAPI} from '../../../../utils/helpers';
import {WeiWatchersAPI} from '../../../../utils/weiwatchers';
import {CONTRACT_MORE_INFO, HEADLINE} from '../../content/contract';
import {ContractSubconfig} from "../../../../../../entities/ts/ContractSubconfig";

@Component({
  tag: 'panic-installer-sources-contract',
  styleUrl: 'panic-installer-sources-contract.scss'
})
export class PanicInstallerSourcesContract {

  @Prop() contract: ContractSubconfig;
  @State() contractNetworkOptions: SelectOptionType;
  @State() addMode: boolean = false;

  async componentWillLoad() {
    this.contractNetworkOptions = await WeiWatchersAPI.weiWatchersMappingToSelectOptionType();
  }

  @Listen("networkChange", {target: "window"})
  handleNetworkChange(event: CustomEvent) {
    const weiWatcherURL: string = event.detail;
    const weiWatcherOption: SelectOptionObjType = this.contractNetworkOptions.find((option: SelectOptionObjType) => {
      return option.value === weiWatcherURL;
    });

    const contract: ContractSubconfig = {
      name: weiWatcherOption.label,
      url: weiWatcherOption.value.toString(),
      monitor: this.contract ? this.contract.monitor : false
    } as ContractSubconfig;

    this.contract = contract;

    HelperAPI.emitEvent("updateContract", contract);
  }

  @Listen("addCustomWeiWatcher", {target: "window"})
  addCustomWeiWatcherHandler(event: CustomEvent): void {
    const customContract: ContractSubconfig = event.detail;

    this.contractNetworkOptions.push({
      label: customContract.name,
      value: customContract.url
    });

    this.contractNetworkOptions = [...this.contractNetworkOptions];
    this.addMode = !this.addMode;

    this.contract = customContract;

    HelperAPI.emitEvent("updateContract", customContract);
  }

  @Listen("enableContractMonitoring", {target: "window"})
  async enableContractMonitoringHandler(event: CustomEvent): Promise<void> {
    this.contract.monitor = event.detail.checked;

    HelperAPI.emitEvent("updateContract", this.contract);
  }

  @Listen("openCustomWeiWatcherForm", {target: "window"})
  openCustomWeiWatcherFormHandler(): void {
    this.addMode = !this.addMode;
  }

  @Listen("closeCustomWeiWatcherForm", {target: "window"})
  closeCustomWeiWatcherFormHandler(): void {
    this.addMode = !this.addMode;
  }

  render() {
    return (
      <svc-surface class={'panic-installer-sources__container'}>
        <svc-label class={'panic-installer-sources__title'}>Contracts Monitoring Setup</svc-label>

        {
          !this.addMode &&
          <div class={"panic-installer-sources__more-info"}>
            <p>
                { HEADLINE }
            </p>
            <svc-buttons-container>
                <svc-button color={"secondary"} iconName={"information-circle"} iconPosition={"icon-only"} onClick={() => {
                  createModal("panic-installer-more-info-modal", {
                    messages: CONTRACT_MORE_INFO,
                    class: "chainlink-contract"
                  });
                }} />
            </svc-buttons-container>
          </div>
        }

        <div class={'panic-installer-sources-contract__container-form'}>
          { this.addMode && <panic-installer-sources-contract-form /> }
        </div>

        <div class={'panic-installer-sources-contract__container-wei'}>
        {
          !this.addMode &&
            <panic-installer-sources-contract-wei-watcher
                contractNetworkOptions={this.contractNetworkOptions}
                contract={this.contract}
            />
        }
        </div>
      </svc-surface>
    );
  }
}

import {Component, h} from '@stencil/core';
import {HelperAPI} from '../../../../utils/helpers';
import {ContractSubconfig} from "../../../../../../entities/ts/ContractSubconfig";
import {parseForm} from "@simply-vc/uikit";

@Component({
  tag: 'panic-installer-sources-contract-form'
})
export class PanicInstallerSourcesContractForm {

  /**
   * On submit, parse form and emit `addCustomWeiWatcher` event.
   */
  onSubmitHandler(event: Event) {
    event.preventDefault();

    const form = event.target as HTMLFormElement;
    const customWeiWatcher = parseForm(form) as ContractSubconfig;

    HelperAPI.emitEvent("addCustomWeiWatcher", customWeiWatcher)
  }

  render() {
    return (
      <form onSubmit={(e: Event) => { this.onSubmitHandler(e); }}>
        <svc-input
          name={'name'}
          label={'Custom Network Name'}
          labelColor={'primary'}
          lines={'inset'}
          required
          placeholder={"Enter custom network name..."}
        />

        <svc-input
          name={'url'}
          label={'Custom Network URL'}
          labelColor={'primary'}
          type={'url'}
          lines={'inset'}
          required
          placeholder={"Enter custom network URL..."}
        />

        <div class={"panic-installer-sources-contract__add-contract-buttons"}>
          <svc-button  color={"primary"} iconName={"checkmark"} type={"submit"}>Save</svc-button>
          <svc-button color={"primary"} iconName={"close"} onClick={() => {
            HelperAPI.emitEvent("closeCustomWeiWatcherForm");
          }}>Cancel</svc-button>
        </div>
      </form>
    );
  }
}
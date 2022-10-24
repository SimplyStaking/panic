import {createInfoAlert, dismissModal, parseForm} from '@simply-vc/uikit';
import {Component, h, Prop, VNode} from '@stencil/core';
import {HelperAPI} from '../../../../utils/helpers';
import {SourceType} from "../../../../../../entities/ts/SourceType";
import {BaseChain} from "../../../../../../entities/ts/BaseChain";
import {NodeSubconfig} from "../../../../../../entities/ts/NodeSubconfig";
import {EVMNodeSubconfig} from "../../../../../../entities/ts/EVMNodeSubconfig";
import {SystemSubconfig} from "../../../../../../entities/ts/SystemSubconfig";
import {Sources} from "../panic-installer-sources";

@Component({
  tag: 'panic-installer-sources-modal',
  styleUrl: 'panic-installer-sources-modal.scss'
})
export class PanicInstallerSourcesModal {

  @Prop() source: Sources;
  @Prop() baseChain: BaseChain;
  @Prop() sourceType: SourceType;

  /**
   * Verifies that the multiple input fields have been filled in.
   * @param formData the data submitted via the form.
   * @returns boolean indicating whether the form is valid.
   */
  verifyMultipleInputs(formData: any): boolean {

    const prometheusUrlsEmpty = this.baseChain.value === 'chainlink'
      && !Object.keys(formData).includes('nodePrometheusUrls_0')
      && Object.keys(formData).includes('monitorPrometheus')
      && formData.monitorPrometheus != false;

    if (prometheusUrlsEmpty) {
      createInfoAlert(
        {
          header: "Attention",
          message: "You must input at least 1 URL in 'Prometheus URLs'."
        });
      return false;
    }
    return true;
  }

  /**
   * On submit, parse form and emit `save` event.
   */
  onSubmitHandler(event: Event) {
    event.preventDefault();

    const form = event.target as HTMLFormElement;
    let source = parseForm(form);
    source = this.customParsing(source);

    if (this.verifyMultipleInputs(source)) {
      HelperAPI.emitEvent("save", {
        source: source,
        type: this.sourceType.value
      });
    }
  }

  /**
   * Custom parse and return the parsed form. This is required to handle string arrays.
   */
  customParsing(source: object): object {
    if (this.baseChain.value === 'substrate' && this.sourceType.value === 'nodes') {
      source['governanceAddresses'] = HelperAPI.extractStringArrayFromObjectProperties(
          'governanceAddresses', source).join(',');
    } else if (this.baseChain.value === 'chainlink' && this.sourceType.value === 'nodes') {
      source['nodePrometheusUrls'] = HelperAPI.extractStringArrayFromObjectProperties(
          'nodePrometheusUrls', source).join(',');
    }

    return source;
  }

  isNode(): boolean {
    return this.sourceType.value === "nodes";
  }

  isEVMNode(): boolean {
    return this.sourceType.value === "evm_nodes";
  }

  isSystem(): boolean {
    return this.sourceType.value === "systems";
  }

  /**
   * Renders sources form component based on the base chain.
   */
  renderFormComponentByBaseChain(): VNode {
    const componentProps = {
      node: this.source as NodeSubconfig
    }
    return h(`panic-installer-sources-${this.baseChain.value}node-form`, componentProps);
  }

  render() {
    return (
      <svc-content-container>
        <form onSubmit={(event: Event) => { this.onSubmitHandler(event) }}>
          <fieldset>
            <legend>{this.sourceType.name}</legend>

            { this.isNode() && this.renderFormComponentByBaseChain() }

            {
              this.isEVMNode() &&
                <panic-installer-sources-form-evmnode
                    node={this.source as EVMNodeSubconfig}
                />
            }

            {
              this.isSystem() &&
                <panic-installer-sources-form-system
                    baseChain={this.baseChain}
                    system={this.source as SystemSubconfig}
                />
            }

            <div class={'panic-installer-sources-modal__buttons-container'}>
                <svc-button iconName='checkmark' color={'primary'} type='submit'>
                    Save
                </svc-button>
                <svc-button iconName='close' color={'primary'} role={'cancel'} onClick={ () => { dismissModal() } }>
                  Cancel
                </svc-button>
            </div>
          </fieldset>
        </form>
      </svc-content-container>
    );
  }
}

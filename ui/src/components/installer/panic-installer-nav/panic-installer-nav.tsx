import {Component, h, Prop} from '@stencil/core';
import { HelperAPI } from '../../../utils/helpers';
import {ButtonIconPositionType} from "@simply-vc/uikit/dist/types/types/button";
import { createModal } from '@simply-vc/uikit';
import { Config } from '../../../../../entities/ts/Config';

/**
 * `PanicInstallerNav` is specialize in handling the navigation through the installer.
 * 
 * When the "back" or "next" button is clicked, an equivalent {@link CustomEvent} is emitted.
 * The events are called `"previousStep"` and `"nextStep"` respectively.
 */
@Component({
  tag: 'panic-installer-nav',
  styleUrl: 'panic-installer-nav.scss'
})
export class PanicInstallerNav {

  @Prop() previousStepButtonText: string = "Back";
  @Prop() previousStepButtonIcon: string = "arrow-back-circle";
  @Prop() previousStepButtonIconPosition: ButtonIconPositionType = "start";
  @Prop() nextStepButtonText: string = "Next";
  @Prop() nextStepButtonIcon: string = "arrow-forward-circle";
  @Prop() nextStepButtonIconPosition: ButtonIconPositionType = "end";

  private previousStepEventName: string = "previousStep";
  private nextStepEventName: string = "nextStep";
  @Prop() hidePreviousBtn: boolean = false;

  /**
   * The current config being edited.
   */
  @Prop() config: Config;

  render() {
    const defaultNavButtons = [
      !this.hidePreviousBtn &&
      <svc-button class={"svc-button-nav"} id="back" color={"primary"} iconName={this.previousStepButtonIcon} iconPosition={this.previousStepButtonIconPosition} onClick={() => {
        HelperAPI.emitEvent(this.previousStepEventName);
      }}>{this.previousStepButtonText}</svc-button>,

      <svc-button class={"svc-button-nav"} id="next" color={"primary"} iconName={this.nextStepButtonIcon} iconPosition={this.nextStepButtonIconPosition} onClick={() => {
        HelperAPI.emitEvent(this.nextStepEventName);
      }}>{this.nextStepButtonText}
      </svc-button>
    ];

    const chainSettingsEditButtons = [
      <svc-button class={"svc-button-nav"} iconName={this.previousStepButtonIcon} href={"/settings/chains"}>
        Back to Settings
      </svc-button>,
      <svc-button class={"svc-button-nav"} iconName={"settings"} onClick={() => {
        createModal("panic-settings-config-menu", {
          config: this.config
        },
        {
          cssClass: "panic-settings-config-menu-modal"
        })
      }} >
        Config Menu
      </svc-button>
    ]

    return (
      <div class={"panic-installer-nav"}>
        { HelperAPI.isFromSettingsEdit() ? chainSettingsEditButtons : defaultNavButtons }
      </div>
    );
  }
}
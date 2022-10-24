import {Component, h, Host, Listen, Prop} from '@stencil/core';
import {
  MAIN_TEXT,
  SECONDARY_TEXT_1,
  SECONDARY_TEXT_2
} from "../content/feedback";
import {HelperAPI} from "../../../utils/helpers";
import {Config} from "../../../../../entities/ts/Config";
import {Router} from "stencil-router-v2";
import {ConfigService} from "../../../services/config/config.service";
import { CONFIG_ID_LOCAL_STORAGE_KEY } from '../../../utils/constants';
import { dismissModal } from '@simply-vc/uikit';

@Component({
  tag: 'panic-installer-feedback',
  styleUrl: 'panic-installer-feedback.scss'
})
export class PanicInstallerFeedback {

  /**
   * Stencil Router object for page navigation.
   */
  @Prop() router: Router;

  /**
   * The ID of the configuration that has just been saved
   */
  @Prop() configId: string;

  /**
   * Object that stores the current configuration data.
   */
  _currentConfig: Config;

  /**
   * Return to the welcome page
   */
  @Listen("previousStep", {target: "window"})
  previousStepHandler() {
    let previousRoute: string;
    if (HelperAPI.isFromInstaller()) {
      // If we are in the installer journey, then we must be re-directed to the
      // installer's sub-chain route
      previousRoute = "/installer/sub-chain"
    } else {
      // If we are in the CRUD journey, we need to be redirected to the settings
      // page's new subchain route
      previousRoute = "/settings/new/sub-chain"
    }

    HelperAPI.changePage(this.router, previousRoute);
  }

  /**
   * Return to the home page.
   */
  @Listen("nextStep", {target: "window"})
  async nextStepHandler() {
    HelperAPI.changePage(this.router, "/");
  }

  /**
   * Fetches the config from API.
   * @returns the configuration object.
   */
  async fetchCurrentConfig(): Promise<Config> {
    return await ConfigService.getInstance().getByID(this.configId);
  }

  async componentWillLoad() {
    // might be necessary
    // i.e. when the node operator opens a modal and then clicks in the browser's back button
    dismissModal();

    this._currentConfig = await this.fetchCurrentConfig();

    // cleaning configId from local storage to avoid side-effects
    localStorage.removeItem(CONFIG_ID_LOCAL_STORAGE_KEY);
  }

  render() {
    const baseChain = this._currentConfig.baseChain.name
    const subChain = this._currentConfig.subChain.name
    return (
      <Host>
        <panic-header showMenu={false} />

        <svc-progress-bar value={1} color={"tertiary"}/>

        <svc-content-container class={"panic-installer-feedback__container"}>
          <svc-surface>
            <div class={"panic-installer-feedback__heading"}>
              <svc-icon
                  name={"checkmark-circle"}
                  size={"120px"}
                  color={"primary"}
              />
              <svc-label class={"panic-installer-feedback__title"}>
                Success!
              </svc-label>
            </div>

            <div class={"panic-installer-feedback__messages_container"}>
              <div>
                <p>
                  <strong>
                    {subChain} ({baseChain})
                  </strong>
                  {MAIN_TEXT}
                </p>
              </div>

              <div>
                <p>
                  {SECONDARY_TEXT_1}
                  <strong>
                    Home Page
                  </strong>
                  {SECONDARY_TEXT_2}
                  <strong>
                    Settings {'>'} Sub-Chain.
                  </strong>
                </p>
              </div>
            </div>

            <panic-installer-nav
              class={"panic-installer-feedback__navigation_buttons"}
              previousStepButtonText={"Configure Another Chain"}
              previousStepButtonIcon={"settings"}
              previousStepButtonIconPosition={"start"}
              nextStepButtonText={"Home Page"}
              nextStepButtonIcon={"home"}
              nextStepButtonIconPosition={"start"}
            />

          </svc-surface>

        </svc-content-container>

        <panic-footer />
      </Host>
    );
  }

}

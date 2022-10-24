import {createAlert, createInfoAlert, createModal, dismissModal, parseForm} from '@simply-vc/uikit';
import {SelectOptionType} from '@simply-vc/uikit/dist/types/types/select';
import {Component, h, Host, Listen, Prop, State} from '@stencil/core';
import {HelperAPI} from '../../../utils/helpers';
import {
  BULLET_ONE,
  BULLET_TWO,
  MAIN_TEXT,
  MORE_INFO_MESSAGES
} from '../content/sub-chain';
import {Config} from '../../../../../entities/ts/Config';
import {ConfigService} from '../../../services/config/config.service';
import {BaseChain} from '../../../../../entities/ts/BaseChain';
import {Router} from "stencil-router-v2";
import { CONFIG_ID_LOCAL_STORAGE_KEY } from '../../../utils/constants';

@Component({
  tag: 'panic-installer-sub-chain',
  styleUrl: 'panic-installer-sub-chain.scss'
})
export class PanicInstallerSubChain {

  /**
   * Stencil Router object for page navigation.
   */
  @Prop() router: Router;

  /**
   * List of blockchain frameworks supported by PANIC.
   */
  @Prop() baseChains: BaseChain[] = [];

  /**
   * Indicates whether the installer process is editing a previously created
   * config.
   */
  @Prop() configId: string;

  /**
   * Stores the *current* base chain being configured. Useful to pre-fill the
   * form when the node operator navigates back to sub-chain page.
   */
  @State() currBaseChain: BaseChain;

  /**
   * The config to be edited.
   */
  @State() config: Config;

  /**
   * The current text within the sub chain name field.
   */
  @State() subChainName: string;

  /**
   * Whether a general chain exists among the user's configs.
   */
  generalChainExists: boolean;

  /**
   * Converts the list of base chains to the {@link SelectOptionType} format.
   *
   * @returns list of base chains in the {@link SelectOptionType} format.
   */
  baseChainToSelectOptionType(): SelectOptionType {

    let baseChainsToShow = [...this.baseChains];

    if(this.config){
      if(this.generalChainExists && this.config.baseChain.value !== 'general'){
        baseChainsToShow = baseChainsToShow.filter(chain => chain.value !== "general");
      }
    }

    return baseChainsToShow.map((baseChain: BaseChain) => {
      return {
        label: baseChain.name,
        value: baseChain.id
      }
    });
  }

  async componentWillLoad() {
    // might be necessary
    // when the node operator opens a modal and then clicks in the browser's back button
    dismissModal();

    this.generalChainExists = await this.hasGeneralChain();

    // check both URL and local storage for the configID
    this.configId = this.configId ? this.configId : localStorage.getItem(CONFIG_ID_LOCAL_STORAGE_KEY);

    if (this.configId) {
      await this.refreshConfig();
      if(this.config){
        this.currBaseChain = this.config.baseChain;
        this.subChainName = this.config.subChain.name
      } else {
        localStorage.removeItem('configId');
        createInfoAlert({
          header: "Attention",
          message: "Invalid configuration. Redirecting to PANIC home page.",
          eventName: "errorReturnToHome"
        });
      }
    }
  }

  @Listen("errorReturnToHome", {target: 'window'})
  async errorReturnToHomeHandler() {
    HelperAPI.changePage(this.router, '/');
  }

  /**
   * Fetches the config data from DB.
   */
  async refreshConfig() {
    this.config = await ConfigService.getInstance().getByID(this.configId);
  }

  /**
   * If the node operator changes the base chain we need to display a dialog
   * warning about the config loss in case that the action is confirmed.
   *
   * @param selectedBaseChainId new base chain selected
   */
  handleOnChange(selectedBaseChainId: string) {
    const baseChain: BaseChain = this.baseChains.find(baseChain => baseChain.id === selectedBaseChainId);
    if (this.configId && this.currBaseChain?.id !== selectedBaseChainId) {
      createAlert({
        header: "Attention",
        message: "If you change the base chain all current configuration " +
            "will be lost. Would you like to proceed?",
        eventName: "baseChainChange",
        eventData: baseChain
      });
    } else {
      this.currBaseChain = baseChain;
    }
  }

  /**
   * This function handles the event fired from the base chain change dialog.
   *
   * @param e {@link CustomEvent} with a boolean as argument indicating
   * whether the action has been confirmed.
   */
  @Listen("baseChainChange", {
    target: 'window'
  })
  async onBaseChainChange(e: CustomEvent) {
    const changeConfirmed = e.detail.confirmed;
    const selectedBaseChain = e.detail.data;

    if (changeConfirmed) {
      // If the base chain was changed we need to delete the config from the
      // database and adjust the state. Note that we can only reach this point
      // if a configuration has already been saved, as otherwise the modal would
      // not have been triggered

      if(this.config.baseChain.value === 'general'){
        this.generalChainExists = false;
      }

      const success: boolean = await ConfigService.getInstance().delete(
          this.configId);

      // We want to execute this logic only if the delete call is successful.
      // Otherwise, we will raise a feedback message
      const toastMsg = "Could not delete configuration from database. " +
          "Basechain change failed."
      const callback = function () {
        this.currBaseChain = selectedBaseChain;
        this.config = undefined;
        this.configId = undefined;
      }.bind(this);
      await HelperAPI.executeWithFailureFeedback(
          success, callback, toastMsg, 3000, "danger")

      if (success) {
        localStorage.removeItem('configId');
        // We do not want to retrieve the previous value of svc-select, so in
        // this case return
        return;
      }
    }

    // If the user decides not to proceed with the change or the delete call
    // fails then it is necessary to keep the correct value for svc-select
    // (displayed in the component UI)
    const baseChainSelect = document.getElementById("base_chain").children[0] as HTMLInputElement;
    baseChainSelect.value  = this.currBaseChain?.id;
  }

  /**
   * Used to navigate back to the Welcome page in the installer.
   */
  @Listen("subChainNameChange", {target: "window"})
  subChainNameChangeHandler(e: CustomEvent) {
    this.subChainName = e.detail.name;
  }

  /**
   * Logic to update the sub-chain name in the DB.
   */
  async subChainNameChange() {
    const reqBody = {
      "id": this.configId,
      "subChain": {
        "name": this.subChainName
      }
    } as Config

    const response: Response = await ConfigService.getInstance().save(reqBody);

    if (HelperAPI.isDuplicateName(response)) {
      HelperAPI.raiseToast(
        `A sub-chain named '${reqBody.subChain.name}' already exists!`,
        2000,
        "warning");
    } else {
      // We want to execute this logic only if the save call is successful.
      // Otherwise, we will raise a feedback message
      const toastMsg = "Error saving configuration.";
      const callback = function () {
        HelperAPI.raiseToast(
          `Sub-chain name saved!`,
          2000,
          "success");
      }.bind(this);

      await this.refreshConfig();

      await HelperAPI.executeWithFailureFeedback(response.ok, callback, toastMsg, 3000, "danger");
    }
  }


  /**
   * Used to navigate back to the Welcome page in the installer.
   */
  @Listen("previousStep", {target: "window"})
  previousStepHandler() {
    HelperAPI.changePage(this.router, "/installer/welcome");
  }

  /**
   * Triggers a click in the `submit` button which is part of the sub-chain
   * form
   */
  @Listen("nextStep", {target: "window"})
  async nextStepHandler() {
      const button = document.getElementById("submit").children[0] as HTMLButtonElement;
      button.click();
  }

  /**
   * Given a parsed form this function will create a new config object and save
   * it in the database
   * @param parsedForm the form parsed using HelperAPI.parseForm
   */
  async createAndSendNewConfig(parsedForm: any) {
    const reqBody = {
      "id": this.configId,
      "baseChain": {
        "id": parsedForm.base_chain
      },
      "subChain": {
        "name": parsedForm.name
      }
    } as Config

    const response: Response = await ConfigService.getInstance().save(reqBody);

    if(HelperAPI.isDuplicateName(response)) {
      HelperAPI.raiseToast(
          `A sub-chain named '${reqBody.subChain.name}' already exists!`,
          2000,
          "warning");
    } else {
      // We want to execute this logic only if the save call is successful.
      // Otherwise, we will raise a feedback message
      const toastMsg = "Error saving configuration.";
      const callback = async function () {
        const configID: string = (await response.json()).result;
        HelperAPI.changePage(this.router, `${HelperAPI.getUrlPrefix()}/channels/${configID}`);
        localStorage.setItem(CONFIG_ID_LOCAL_STORAGE_KEY, configID);
      }.bind(this);

      await HelperAPI.executeWithFailureFeedback(response.ok, callback, toastMsg, 3000, "danger");
    }
  }

  /**
   * This method is fired when the node operator clicks in the "next" button.
   *
   * It will parse the form's data and make an API call to save the config.
   *
   * @param e the form event
   */
  async handleSubmit(e: Event) {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const parsedForm: any = parseForm(form);
    if (!parsedForm.base_chain) {
      HelperAPI.raiseToast("Please, choose a base chain to proceed.", 2500, "warning");
      return;
    }

    await this.createAndSendNewConfig(parsedForm);
  }

  /**
   * Check if there is at least one General chain configured.
   *
   * @returns `true` if there is one, otherwise, `false`.
   */
  async hasGeneralChain(): Promise<boolean> {
    const configs: Config[] = await ConfigService.getInstance().getAll();
    const hasGeneralChain: boolean = configs.some((config: Config) => {
      return config.baseChain.name.toLowerCase() === "general";
    });

    return hasGeneralChain;
  }

  /**
   * Checks if the config being edited belongs to a General base chain.
   * 
   * @returns `true` if it belongs, otherwise `false`.
   */
  isGeneral(): boolean {
    const generalConfig: boolean = this.config?.baseChain.value === 'general';
    const generalCurrBaseChain: boolean = this.currBaseChain?.value === 'general';
    return generalConfig || generalCurrBaseChain;
  }

  /**
   * Returns the appropriate `placeholder` for the base chain input.
   * 
   * @returns a `string` representing the `placeholder`.
   */
  getBaseChainPlaceholder(): string {
    return this.config ? this.config.baseChain.name : "Select a base chain...";
  }

  render() {
    // show svc-input disabled when editing a chain only (Settings/Chain "edit mode")
    const baseChainInput = this.config && HelperAPI.isFromSettingsEdit()
    ?  <svc-input value={this.config.baseChain.name} disabled={HelperAPI.isFromSettingsEdit()} />
    : <svc-select
        header={"Base-chains"}
        options={this.baseChainToSelectOptionType()}
        name={"base_chain"}
        id={"base_chain"}
        value={this.currBaseChain?.id}
        withBorder={true}
        placeholder={this.getBaseChainPlaceholder()}
        // @ts-ignore
        onIonChange={(e: CustomEvent) => {
          this.handleOnChange(e.detail.value);
        }}
      />
    
    const subChainName: string = this.isGeneral() ? 'GENERAL' : this.config?.subChain.name;

    return (
      <Host class={"panic-installer-sub-chain"}>
        <panic-header showMenu={false} />

        <svc-progress-bar value={0.1} color={"tertiary"} />

        <svc-content-container class={"panic-installer-sub-chain__container"}>
          <svc-surface>
            <div class={"panic-installer-sub-chain__heading"}>
              <svc-icon color={"primary"} name={"link"} size={"100px"} />
              <svc-label
                  position={"center"}
                  class={"panic-installer-sub-chain__title"}
              >
                Blockchain Setup
              </svc-label>
              <svc-label
                  position={"center"}
                  class={"panic-installer-sub-chain__step"}
              >
                step 1/5
              </svc-label>
            </div>

            <div class={"panic-installer-sub-chain__message-container"}>
              <p class={"panic-installer-sub-chain__message"}>
                { MAIN_TEXT }
              </p>
              <svc-buttons-container>
                  <svc-button
                      color={"secondary"}
                      iconName={"information-circle"}
                      iconPosition={"icon-only"}
                      onClick={() => { createModal("panic-installer-more-info-modal", {messages: MORE_INFO_MESSAGES}, {cssClass: "panic-installer-sub-chain__info-modal"});
                      }}
                  />
              </svc-buttons-container>
            </div>

            <p class={"panic-installer-sub-chain__message"}>
              <ul class={"panic-installer-sub-chain__list"}>
                <li class={"panic-installer-sub-chain__list-item"}>
                  { BULLET_ONE }
                </li>
                <li>
                  { BULLET_TWO }
                </li>
              </ul>
            </p>

            <form onSubmit={
              (e) => {this.handleSubmit(e)}}
            >
              { baseChainInput }

              { this.configId && <input type={"hidden"} value={this.config.baseChain.id} name={"base_chain"} /> }

              { this.currBaseChain && this.currBaseChain.value === 'general' && <input type={"hidden"} value={'GENERAL'} name={"name"} /> }

              {
                !HelperAPI.isFromSettingsEdit()
                ?
                  <svc-input
                    id={"subChainName"}
                    value={subChainName}
                    disabled={this.isGeneral()}
                    type={"text"}
                    name={"name"}
                    lines={"full"}
                    label={"Name"}
                    placeholder={"Ex: Akash, Polkadot"}
                    required
                  />
                :
                  <div>
                    <svc-event-emitter
                      eventName={"subChainNameChange"}
                      debounce={300}
                    >
                      <svc-input
                        id={"subChainName"}
                        value={subChainName}
                        disabled={this.isGeneral()}
                        type={"text"}
                        name={"name"}
                        lines={"full"}
                        label={"Name"}
                        placeholder={"Ex: Akash, Polkadot"}
                        required
                      />
                    </svc-event-emitter>
                    {
                      this.subChainName !== this.config.subChain.name &&
                      <p id={"unsaved-changes-text"}>
                        There are unsaved changes!
                      </p>
                    }
                    <svc-button
                      onClick={()=>this.subChainNameChange()}
                    >
                      Save
                    </svc-button>
                  </div>
              }

              <svc-button type={"submit"} id={"submit"} />
            </form>
          </svc-surface>

          <panic-installer-nav config={this.config} hidePreviousBtn={HelperAPI.isFromSettings()} />
        </svc-content-container>

        <panic-footer />
      </Host>
    );
  }
}
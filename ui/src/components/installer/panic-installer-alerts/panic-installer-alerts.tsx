import {Component, h, Host, Listen, Prop, State} from "@stencil/core";
import {HelperAPI} from "../../../utils/helpers";
import {createAlert, createModal, dismissModal} from "@simply-vc/uikit";
import {
  ALERT_SEVERITY_TABLE_HEADERS,
  ALERT_THRESHOLD_TABLE_HEADERS,
  MAIN_TEXT,
  MORE_INFO_MESSAGES,
  SECONDARY_TEXT,
  THIRD_TEXT,
} from "../content/alerts";
import {DataTableRow, DataTableRowsType} from "@simply-vc/uikit/dist/types/types/datatable";
import {Router} from "stencil-router-v2";
import {ConfigService} from "../../../services/config/config.service";
import {Config} from "../../../../../entities/ts/Config";
import {SeverityType} from "../../../../../entities/ts/SeverityType";
import {ThresholdAlertSubconfig} from "../../../../../entities/ts/ThresholdAlertSubconfig";
import {SeverityAlertSubconfig} from "../../../../../entities/ts/SeverityAlertSubconfig";
import {TimeWindowAlertSubconfig} from "../../../../../entities/ts/TimeWindowAlertSubconfig";
import {AlertKeyAttributes} from "../../../utils/types";

@Component({
  tag: 'panic-installer-alerts',
  styleUrl: 'panic-installer-alerts.scss'
})
export class PanicInstallerAlerts{

  /**
   * Stencil Router object for page navigation.
   */
  @Prop() router: Router;

  /**
   * The ID of the configuration that has just been saved
   */
  @Prop() configId: string;

  /**
   * The list of SeverityType provided by PANIC.
   */
  @Prop() severityTypes: SeverityType[];

  /**
   * The Config object stored as a state.
   */
  @State() config: Config;

  /**
   * Storing the threshold + time window alerts form data as a variable to be used as a reference
   * for when a change is made.
   */
  _priorThresholdAndTimeWindowFormData: object = {};

  /**
   * Storing the severity alerts form data as a variable to be used as a reference
   * for when a change is made.
   */
  _priorSeverityFormData: object = {};

  @Listen("previousStep", {target: "window"})
  previousStepHandler() {
    HelperAPI.changePage(this.router,
      `${HelperAPI.getUrlPrefix()}/repositories/${this.configId}`);
  }

  /**
   * Navigate to the next page.
   */
  nextPage(){
    HelperAPI.changePage(this.router, `${
      HelperAPI.getUrlPrefix()}/feedback/${this.configId}`);
  }

  /**
   * Listens for the event, and informs the user that their configuration will be completed
   * once they confirm.
   */
  @Listen("nextStep", {target: "window"})
  async nextStepHandler() {

    if(!this.config.ready){
      await createAlert({
        'header': 'Setup complete!',
        'message': 'You are about to complete the configuration process. Do you wish to proceed?',
        'cancelButtonLabel': 'Back',
        'confirmButtonLabel': 'Finish',
        'eventName': 'promptSetConfigAsReady'
      });
    } else {
      this.nextPage();
    }
  }

  /**
   * Save the config object in Mongo via API call.
   * @param requestBody Config object to be updated
   * @param configReady optional parameter signifying whether the operation is a ready config save.
   */
  async save(requestBody: Config, configReady?: boolean): Promise<void>{
    const resp: Response = await ConfigService.getInstance().save(requestBody as Config);

    await resp.json().then(async resp => {
      if (resp.status === 200) {
        if (configReady) {
          HelperAPI.raiseToast("Configuration setup completed.");
        } else {
          HelperAPI.raiseToast("Alert saved.", 500);
        }
        await dismissModal();
      } else {
        HelperAPI.raiseToast("Saving failed.", 3000, 'danger');
      }
    });
  }

  /**
   * Creates a threshold request body to passed in API call.
   * @returns Config
   */
  createThresholdRequestBody(): Config{
    return {
      id: this.config.id,
      thresholdAlerts: this.config.thresholdAlerts,
    } as Config;
  }

  /**
   * Creates a time window request body to passed in API call.
   * @returns Config
   */
  createTimeWindowRequestBody(): Config{
    return {
      id: this.config.id,
      timeWindowAlerts: this.config.timeWindowAlerts,
    } as Config;
  }

  /**
   * Creates a severity request body to passed in API call.
   * @returns Config
   */
  createSeverityRequestBody(): Config{
    return {
      id: this.config.id,
      severityAlerts: this.config.severityAlerts,
    } as Config;
  }

  /**
   * Creates a config ready request body to passed in API call.
   * @returns Config
   */
  createConfigAsReadyRequestBody(): Config {
    return {
      id: this.config.id,
      ready: true,
    } as Config;
  }

  /**
   * Listens to events raised by the alert dialog raised in the {@link nextStepHandler} function. This will set the
   * configuration in MongoDB as 'ready' and move to the next page, given that the user confirmed the dialog event.
   * @param event the custom event being fired
   */
  @Listen("promptSetConfigAsReady", { target: 'window' })
  async setupCompleteDialogHandler(event: CustomEvent){
    if (event.detail.confirmed) {
      await this.save(this.createConfigAsReadyRequestBody(), true);
      this.nextPage();
    }
  }

  /**
   * Set the value of the new time window alert data in the config.
   * @param timeWindowAlertAttributes AlertKeyAttributes object of the time window alert to be updated.
   * @param value the new value of the threshold alert to be set.
   */
  async updateTimeWindowAlertInConfig(timeWindowAlertAttributes: AlertKeyAttributes,
                                                 value: boolean | number): Promise<void> {

    if(!timeWindowAlertAttributes.severity){
      this.config.timeWindowAlerts.map(alert => alert.id === timeWindowAlertAttributes.identifier
        ? alert[timeWindowAlertAttributes.field] = value
        : alert
      );
    } else {
      this.config.timeWindowAlerts.map(alert => alert.id === timeWindowAlertAttributes.identifier
        ? alert[timeWindowAlertAttributes.severity][timeWindowAlertAttributes.field] = value
        : alert
      );
    }

    await this.save(this.createTimeWindowRequestBody());
  }

  /**
   * Set the value of the new threshold alert data in the config.
   * @param thresholdAlertAttributes AlertKeyAttributes object of the threshold alert to be updated.
   * @param value the new value of the threshold alert to be set.
   */
  async updateThresholdAlertInConfig(thresholdAlertAttributes: AlertKeyAttributes,
                               value: boolean | number): Promise<void> {
    if(!thresholdAlertAttributes.severity){
      this.config.thresholdAlerts.map(alert => alert.id === thresholdAlertAttributes.identifier
        ? alert[thresholdAlertAttributes.field] = value
        : alert
      );
    } else {
      this.config.thresholdAlerts.map(alert => alert.id === thresholdAlertAttributes.identifier
        ? alert[thresholdAlertAttributes.severity][thresholdAlertAttributes.field] = value
        : alert
      );
    }

    await this.save(this.createThresholdRequestBody());
  }

  /**
   * Set the value of the new threshold alert data in the config.
   * @param severityAlertAttributes AlertKeyAttributes object of the severity alert to be updated.
   * @param value the new value of the severity alert to be set.
   */
  async updateSeverityAlertInConfig(severityAlertAttributes: AlertKeyAttributes,
                                     value: boolean | string): Promise<void> {
    this.config.severityAlerts.map(alert => alert.id === severityAlertAttributes.identifier
      ? alert[severityAlertAttributes.field] = value
      : alert
    );

    await this.save(this.createSeverityRequestBody());
  }

  /**
   * Get the identifier attribute from the alert key.
   * @param alertKeySplit an array of strings within the alert key.
   * @returns string identifier attribute of the alert key.
   */
  getIdentifierFromAlertKey(alertKeySplit: string[]): string {
    return alertKeySplit[0];
  }

  /**
   * Get the severity attribute from the threshold alert key.
   * @param alertKeySplit an array of strings within the threshold alert key.
   * @returns attribute of the threshold alert key.
   */
  getSeverityFromThresholdAlertKey(alertKeySplit: string[]): string {
    return alertKeySplit[1];
  }

  /**
   * Get the field attribute from the threshold alert key.
   * @param alertKeySplit an array of strings within the threshold alert key.
   * @returns field attribute of the threshold alert key.
   */
  getFieldFromThresholdAlertKey(alertKeySplit: string[]): string {
    return alertKeySplit[2];
  }

  /**
   * Parse and split the threshold alert key into granular attributes.
   * @param alertKey the string representing the threshold alert.
   * @returns an object pertaining to the threshold alert key attributes.
   */
  splitThresholdAlertAttributesFromKey(alertKey: string): AlertKeyAttributes {
    const keySplit = alertKey.split(" ");

    if(keySplit.length == 2){
      const identifier = this.getIdentifierFromAlertKey(keySplit);
      const field = this.getSeverityFromThresholdAlertKey(keySplit);
      return {identifier: identifier, field: field}
    }

    const identifier = this.getIdentifierFromAlertKey(keySplit);
    const severity = this.getSeverityFromThresholdAlertKey(keySplit);
    const field = this.getFieldFromThresholdAlertKey(keySplit);

    return {identifier: identifier, severity: severity, field: field}
  }

  /**
   * Get the field attribute from the severity alert key.
   * @param alertKeySplit an array of strings within the severity alert key.
   * @returns field attribute of the severity alert key.
   */
  getFieldFromSeverityAlertKey(alertKeySplit: string[]): string {
    return alertKeySplit[1];
  }

  /**
   * Parse and split the severity alert key into granular attributes.
   * @param alertKey the string representing the severity alert.
   * @returns an object pertaining to the severity alert key attributes.
   */
  splitSeverityAlertAttributesFromKey(alertKey: string): AlertKeyAttributes {
    const keySplit = alertKey.split(" ");
    const identifier = this.getIdentifierFromAlertKey(keySplit);
    const field = this.getFieldFromSeverityAlertKey(keySplit);

    return {identifier: identifier, field: field}
  }

  /**
   * Parse the threshold alert depending on the type of data received from the form.
   * @param updatedAlert the key-value pair of the alert updated.
   */
  parseUpdatedThresholdAlertData(updatedAlert: Record<string, string>): [AlertKeyAttributes, boolean | number] {

    const key = Object.keys(updatedAlert)[0];
    const alertAttributes: AlertKeyAttributes = this.splitThresholdAlertAttributesFromKey(key);

    const value = Object.values(updatedAlert)[0];
    let newValue: boolean | number;

    if(alertAttributes.field === 'enabled' || alertAttributes.field === 'repeatEnabled'){
      newValue = value === 'true';
    } else {
      newValue = parseInt(value);
    }

    return [alertAttributes, newValue];
  }

  /**
   * Parse the severity alert depending on the type of data received from the form.
   * @param updatedAlert the key-value pair of the alert updated.
   */
  parseUpdatedSeverityAlertData(updatedAlert: Record<string, string>): [
    AlertKeyAttributes, boolean | string] {

    const key = Object.keys(updatedAlert)[0];
    const alertAttributes: AlertKeyAttributes = this.splitSeverityAlertAttributesFromKey(key);

    const value = Object.values(updatedAlert)[0];
    let newValue: boolean | string;

    if(alertAttributes.field === 'enabled'){
      newValue = value === 'true';
    } else {
      newValue = value;
    }

    return [alertAttributes, newValue];
  }

  /**
   * Checks whether the alert is a time window alert.
   * @param id the identifier of the alert
   * @returns boolean
   */
  isAlertTimeWindowAlert(id: string): boolean {
    return this.config.timeWindowAlerts.some(alert => alert.id === id);
  }

  /**
   * Listens to updates within the threshold alert svc-data-table's components and updates either the threshold
   * alert config or the time window alert config with the modified alert configuration.
   * @param event the thresholdAlertConfigurationUpdate event being fired
   */
  @Listen("thresholdAlertConfigurationUpdate")
  async thresholdAlertConfigurationUpdate(event: CustomEvent) {
    const updatedThresholdAlertDataFromForm: Record<string, string> = event.detail;

    const updatedThresholdAlert = HelperAPI.differenceBetweenTwoObjects(
      updatedThresholdAlertDataFromForm, this._priorThresholdAndTimeWindowFormData);

    if(Object.keys(updatedThresholdAlert).length > 0){
      this._priorThresholdAndTimeWindowFormData = updatedThresholdAlertDataFromForm;

      const [alertAttributes, value] = this.parseUpdatedThresholdAlertData(
        updatedThresholdAlert as Record<string, string>);

      if(this.isAlertTimeWindowAlert(alertAttributes.identifier)){
        await this.updateTimeWindowAlertInConfig(alertAttributes, value);
      } else {
        await this.updateThresholdAlertInConfig(alertAttributes, value);
      }

      await this.getConfig();
    }
  }

  /**
   * Listens to updates within the severity alert svc-data-table's components and updates the severity alert config
   * with the modified alert configuration.
   * @param event the severityAlertConfigurationUpdate event being fired
   */
  @Listen("severityAlertConfigurationUpdate")
  async severityAlertConfigurationUpdate(event: CustomEvent) {
    const updatedSeverityAlertDataFromForm: Record<string, string> = event.detail;

    const updatedSeverityAlerts = HelperAPI.differenceBetweenTwoObjects(
      updatedSeverityAlertDataFromForm, this._priorSeverityFormData);

    if(Object.keys(updatedSeverityAlerts).length > 0) {
      this._priorSeverityFormData = updatedSeverityAlertDataFromForm;

      const [alertAttributes, value] = this.parseUpdatedSeverityAlertData(
        updatedSeverityAlerts as Record<string, string>);

      await this.updateSeverityAlertInConfig(alertAttributes, value);

      await this.getConfig();
    }
  }

  /**
   * Return the SeverityType object based on the severity value.
   * @param value the severity value (critical, warning, info or error)
   * @returns SeverityType
   */
  getSeverityTypeByValue(value: string): SeverityType{
    return this.severityTypes.find(severityType => severityType.value === value);
  }

  /**
   * Parses a given severity alert into a data table row format
   * @param alert SeverityAlertSubconfig
   * @returns data table row
   */
  severityAlertDataToDataTableRow(alert: SeverityAlertSubconfig): DataTableRow {
    return {
      cells: [
        {
          value: "",
          label: <panic-installer-alerts-message-cell
            label={alert.name}
            message={alert.description}
          />
        },
        {
          value: "",
          label: <svc-select
            name={`${alert.id} type`}
            options={HelperAPI.generateSelectOptionTypeOptions(this.severityTypes)}
            value={alert.type.id}
            withBorder={true}>
          </svc-select>
        },
        {
          value: "",
          label: <panic-installer-form-checkbox
            name={`${alert.id} enabled`}
            checked={alert.enabled}
          />
        },
      ],
      id: alert.name
    }
  }

  /**
   * Parses a given time window alert into a data table row format
   * @param alert TimeWindowAlertSubconfig
   * @returns data table row
   */
  timeWindowAlertDataToDataTableRow(alert: TimeWindowAlertSubconfig): DataTableRow {
    return {
      cells: [
        {
          value: "",
          label: <panic-installer-alerts-message-cell
              label={alert.name}
              message={alert.description}
          />
        },
        {
          value: "",
          label: <panic-installer-alerts-alert-cell
              alertIdentifier={alert.id}
              severity={this.getSeverityTypeByValue('warning')}
              severityEnabled={alert.warning.enabled}
              adornment={alert.adornment}
              primaryInputLabel={`threshold`}
              primaryInputValue={alert.warning.threshold}
              secondaryInputLabel={`timeWindow`}
              secondaryInputValue={alert.warning.timeWindow}
          />
        },
        {
          value: "",
          label: <panic-installer-alerts-alert-cell
              alertIdentifier={alert.id}
              severity={this.getSeverityTypeByValue('critical')}
              severityEnabled={alert.critical.enabled}
              adornment={alert.adornment}
              primaryInputLabel={`threshold`}
              primaryInputValue={alert.critical.threshold}
              secondaryInputLabel={`repeat`}
              secondaryInputValue={alert.critical.repeat}
            // @ts-ignore
              repeatEnabled={alert.critical.repeatEnabled}
              tertiaryInputLabel={`timeWindow`}
              tertiaryInputValue={alert.critical.timeWindow}
          />
        },
        {
          value: "",
          label: <panic-installer-form-checkbox
            name={`${alert.id} enabled`}
            checked={alert.enabled}
          />
        },
      ],
      id: alert.id
    }
  }

  /**
   * Parses a given threshold alert into a data table row format
   * @param alert ThresholdAlertSubconfig
   * @returns data table row
   */
  thresholdAlertDataToDataTableRow(alert: ThresholdAlertSubconfig): DataTableRow {
    return {
      cells: [
        {
          value: "",
          label: <panic-installer-alerts-message-cell
              label={alert.name}
              message={alert.description}
          />
        },
        {
          value: "",
          label: <panic-installer-alerts-alert-cell
              alertIdentifier={alert.id}
              severity={this.getSeverityTypeByValue('warning')}
              severityEnabled={alert.warning.enabled}
              adornment={alert.adornment}
              primaryInputLabel={`threshold`}
              primaryInputValue={alert.warning.threshold}
          />
        },
        {
          value: "",
          label: <panic-installer-alerts-alert-cell
              alertIdentifier={alert.id}
              severity={this.getSeverityTypeByValue('critical')}
              severityEnabled={alert.critical.enabled}
              adornment={alert.adornment}
              primaryInputLabel={`threshold`}
              primaryInputValue={alert.critical.threshold}
              secondaryInputLabel={`repeat`}
              secondaryInputValue={alert.critical.repeat}
              repeatEnabled={alert.critical.repeatEnabled}
          />
        },
        {
          value: "",
          label: <panic-installer-form-checkbox
              name={`${alert.id} enabled`}
              checked={alert.enabled}
            />
        },
      ],
      id: alert.id
    }
  }

  /**
   * Uses the severity alert data to format it to be able to be rendered by the data table.
   * @returns the severity alert data formatted into a type that is used to load rows within a data table.
   */
  parseSeverityAlertDataToDataTableRowsType(): DataTableRowsType {
    return this.config.severityAlerts.map(
      alert => this.severityAlertDataToDataTableRow(alert));
  }

  /**
   * Uses the threshold alert data to format it to be able to be rendered by the data table.
   * @returns the threshold alert data formatted into a type that is used to load rows within a data table.
   */
  parseThresholdAlertDataToDataTableRowsType(): DataTableRowsType {
    const thresholdAlerts = this.config.thresholdAlerts.map(
      alert => this.thresholdAlertDataToDataTableRow(alert));

    const timeWindowAlerts = this.config.timeWindowAlerts.map(
      alert => this.timeWindowAlertDataToDataTableRow(alert));

    //combines the lists so that they are rendered within the same table
    return [...thresholdAlerts, ...timeWindowAlerts];
  }

  /**
   * Gets the config object from the API.
   */
  async getConfig() {
    this.config = await ConfigService.getInstance().getByID(this.configId);
  }

  /**
   * Initializes the _priorThresholdAndTimeWindowFormData with the initial threshold and
   * time window alert form data.
   */
  getDefaultThresholdAndTimeWindowAlertFormData(){
    this.config.thresholdAlerts.forEach(alert => {
      this._priorThresholdAndTimeWindowFormData[`${alert.id} warning enabled`] = alert.warning.enabled.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} warning threshold`] = alert.warning.threshold.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} critical enabled`] = alert.critical.enabled.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} critical threshold`] = alert.critical.threshold.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} critical repeat`] = alert.critical.repeat.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} critical repeatEnabled`] = alert.critical.repeatEnabled.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} enabled`] = alert.enabled.toString();
    });
    this.config.timeWindowAlerts.forEach(alert => {
      this._priorThresholdAndTimeWindowFormData[`${alert.id} warning enabled`] = alert.warning.enabled.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} warning threshold`] = alert.warning.threshold.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} warning timeWindow`] = alert.warning.timeWindow.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} critical enabled`] = alert.critical.enabled.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} critical threshold`] = alert.critical.threshold.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} critical repeat`] = alert.critical.repeat.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} critical repeatEnabled`] = alert.critical.repeatEnabled.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} critical timeWindow`] = alert.critical.timeWindow.toString();
      this._priorThresholdAndTimeWindowFormData[`${alert.id} enabled`] = alert.enabled.toString();
    });
  }

  /**
   * Initializes the _priorSeverityFormData with the initial severity alert form data.
   */
  getDefaultSeverityAlertFormData(){
    this.config.severityAlerts.forEach(alert => {
      this._priorSeverityFormData[`${alert.id} enabled`] = alert.enabled.toString();
      this._priorSeverityFormData[`${alert.id} type`] = alert.type.id.toString();
    });
  }

  /**
   * Initializes the threshold, time window, and severity initial form data.
   */
  getDefaultFormData() {
    this.getDefaultThresholdAndTimeWindowAlertFormData();
    this.getDefaultSeverityAlertFormData();
  }

  async componentWillLoad() {
    // might be necessary
    // i.e. when the node operator opens a modal and then clicks in the browser's back button
    dismissModal();

    await this.getConfig();
    this.getDefaultFormData();
  }

  render(){
    const subChainName = this.config.subChain.name;
    return (
      <Host>
        <panic-header showMenu={false} />

        <svc-progress-bar value={0.8} color={"tertiary"}/>

        <svc-content-container class={"panic-installer-alerts__container"}>
          <svc-surface>
            <div class={"panic-installer-alerts__heading"}>
              <svc-icon name={"alert-circle-outline"} size={"120px"} color={"primary"}/>
              <svc-label class={"panic-installer-alerts__title"}>Alerts Setup
                for {subChainName}</svc-label>
              <svc-label class={"panic-installer-alerts__step"}>step 5/5</svc-label>
            </div>

            <p>
              {MAIN_TEXT}
            </p>

            <p>
              <b>Important!</b> {SECONDARY_TEXT}
            </p>

            <div class={"panic-installer-alerts__text-with-tooltip"}>
              <p>
                {THIRD_TEXT}
              </p>
              <svc-buttons-container>
                <svc-button color={"secondary"} iconName={"information-circle"} iconPosition={"icon-only"}
                  onClick={() => {
                    createModal("panic-installer-more-info-modal", {
                      messages: MORE_INFO_MESSAGES,
                      class: "alerts",
                    })
                  }}/>
              </svc-buttons-container>
            </div>

            <div class={"panic-installer-alerts-types"}>
              <div class={"panic-installer-alerts-types__item"}>
                <svc-icon name={"alert-circle"} size={"30px"} color={"success"}/>
                <svc-label color={"success"}>Info</svc-label>
              </div>
              <div class={"panic-installer-alerts-types__item"}>
                <svc-icon name={"warning"} size={"30px"} color={"warning"}/>
                <svc-label color={"warning"}>Warning</svc-label>
              </div>
              <div class={"panic-installer-alerts-types__item"}>
                <svc-icon name={"alert-circle"} size={"30px"} color={"danger"}/>
                <svc-label color={"danger"}>Critical</svc-label>
              </div>
              <div class={"panic-installer-alerts-types__item"}>
                <svc-icon name={"skull"} size={"30px"} color={"dark"}/>
                <svc-label color={"dark"}>Error</svc-label>
              </div>
            </div>
          </svc-surface>

          {
            this.config.thresholdAlerts.length > 0 &&
              <svc-surface label={"Threshold Alerts"}>
                <svc-card collapsed={true}>
                  <div slot={"collapsed"}>
                    <div>
                      Expand...
                    </div>
                  </div>
                  <div slot={"expanded"}>
                    <svc-event-emitter eventName={"thresholdAlertConfigurationUpdate"}>
                      <svc-data-table
                        class={"panic-installer-alerts__threshold-alerts-table"}
                        cols={ALERT_THRESHOLD_TABLE_HEADERS}
                        rows={this.parseThresholdAlertDataToDataTableRowsType()}
                        theme={"glacial-line"}
                      />
                    </svc-event-emitter>
                  </div>

                </svc-card>
              </svc-surface>
          }
          {
            this.config.severityAlerts.length > 0 &&
              <svc-surface label={"Severity Alerts"}>
                <svc-card collapsed={true}>
                  <div slot={"collapsed"}>
                    <div>
                      Expand...
                    </div>
                  </div>
                  <div slot={"expanded"}>
                    <svc-event-emitter eventName={"severityAlertConfigurationUpdate"}>
                      <svc-data-table
                        cols={ALERT_SEVERITY_TABLE_HEADERS}
                        rows={this.parseSeverityAlertDataToDataTableRowsType()}
                        theme={"glacial-line"}
                      />
                    </svc-event-emitter>
                  </div>

                </svc-card>
              </svc-surface>
          }

          <panic-installer-nav config={this.config} />

        </svc-content-container>

        <panic-footer/>
      </Host>
    )
  }

}

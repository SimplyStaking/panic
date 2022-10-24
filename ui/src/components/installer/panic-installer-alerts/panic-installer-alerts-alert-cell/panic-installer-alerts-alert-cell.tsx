import {Component, h, Prop} from '@stencil/core';
import {SeverityType} from "../../../../../../entities/ts/SeverityType";

@Component({
  tag: 'panic-installer-alerts-alert-cell',
  styleUrl: 'panic-installer-alerts-alert-cell.scss'
})
export class PanicInstallerAlertsAlertCell {

  /**
   * the alert identifier
   */
  @Prop() alertIdentifier: string;
  /**
   * the SeverityType object associated with the alert
   */
  @Prop() severity: SeverityType;
  /**
   * the default state of the severity enabled setting
   */
  @Prop() severityEnabled: boolean;
  /**
   * the method in which time is measured, for example: seconds; blocks; eras; etc.
   */
  @Prop() adornment: string;
  /**
   * the title of the primary input
   */
  @Prop() primaryInputLabel: string;
  /**
   * the default text of the primary input
   */
  @Prop() primaryInputValue: number;
  /**
   * the title of the secondary input
   */
  @Prop() secondaryInputLabel: string;
  /**
   * the default text of the secondary input
   */
  @Prop() secondaryInputValue: number;
  /**
   * the default text of the tertiary input
   */
  @Prop() tertiaryInputLabel: string;
  /**
   * the default text of the tertiary input
   */
  @Prop() tertiaryInputValue: number;
  /**
   * the default state of the repeat enabled setting
   */
  @Prop() repeatEnabled: boolean;

  /**
   * Renders a form which is dynamically built depending on the props that have been passed,
   * including the set of default values for each prop. Each alert setting is classified by
   * a combination of 3 lowercase attributes: identifier, severity and field. The combination
   * of these attributes allows the component to uniquely identify each alert as well as each of
   * its specific properties being adjusted, allowing it to be then updated in the config.
   */
  render(){
    return (
      <div class={"panic-installer-alerts-alert-cell__container"}>
        <div class={"panic-installer-alerts-alert-cell__enabled-input"}>
          <svc-label>{`${this.severity.name} Enabled`}</svc-label>
          <panic-installer-form-checkbox
              name={`${this.alertIdentifier} ${this.severity.value} enabled`}
              checked={this.severityEnabled}
          />
        </div>

        <svc-input
          name={`${this.alertIdentifier} ${this.severity.value} ${this.primaryInputLabel}`}
          type={"number"}
          labelPosition={"floating"}
          label={`${this.primaryInputLabel} (${this.adornment})`}
          value={this.primaryInputValue}
        />

        {
          this.secondaryInputLabel && this.secondaryInputLabel.includes("repeat") &&
            <div class={"panic-installer-alerts-alert-cell__enabled-input"}>
              <svc-label>Repeat Enabled</svc-label>
              <panic-installer-form-checkbox
                  name={`${this.alertIdentifier} ${this.severity.value} repeatEnabled`}
                  checked={this.repeatEnabled}
              />
            </div>
        }

        {
          this.secondaryInputLabel &&
            <svc-input
              name={`${this.alertIdentifier} ${this.severity.value} ${this.secondaryInputLabel}`}
              type={"number"}
              labelPosition={"floating"}
              label={`${this.secondaryInputLabel} (${this.adornment})`}
              value={this.secondaryInputValue}
            />
        }

        {
          this.tertiaryInputLabel &&
            <svc-input
              name={`${this.alertIdentifier} ${this.severity.value} ${this.tertiaryInputLabel}`}
              type={"number"}
              labelPosition={"floating"}
              label={`${this.tertiaryInputLabel} (${this.adornment})`}
              value={this.tertiaryInputValue}
            />
        }
      </div>
    )
  }
}

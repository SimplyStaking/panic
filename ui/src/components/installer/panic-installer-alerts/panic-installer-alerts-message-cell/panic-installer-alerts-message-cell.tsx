import {Component, h, Prop} from '@stencil/core';

@Component({
  tag: 'panic-installer-alerts-message-cell',
  styleUrl: 'panic-installer-alerts-message-cell.scss'
})
export class PanicInstallerAlertsMessageCell {

  /**
   * the label which serves as the header text
   */
  @Prop() label: string;
  /**
   * the message which serves as additional text
   */
  @Prop() message: string;

  render(){
    return (
      <div class={"panic-installer-alerts-message-cell__container"}>
        <svc-label>{this.label}</svc-label>
        <svc-text>
          <p>
            {this.message}
          </p>
        </svc-text>
      </div>
    )
  }
}

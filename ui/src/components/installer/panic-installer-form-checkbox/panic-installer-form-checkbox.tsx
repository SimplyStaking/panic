import {Component, h, Prop} from '@stencil/core';

@Component({
  tag: 'panic-installer-form-checkbox',
})
export class PanicInstallerFormCheckbox {

  /**
   * the name used in order to process the HTML form
   */
  @Prop() name: string;

  /**
   * whether to default the checkbox state to enabled
   */
  @Prop() checked: boolean;

  /**
   * The reason behind this component is that due to the essence of how HTML forms work, if the value is
   * unticked, i.e. set to false, the data will not be sent with the form. Therefore this component makes
   * use of 2 input elements, one hidden and the other visible in order to consistently include a true/false
   * value within the form submission.
   */
  render(){
    return (
      <div>
        <input
            name={this.name}
            type={"hidden"}
            value={"false"}
        />
        <input
            name={this.name}
            type={"checkbox"}
            value={"true"}
            checked={this.checked}
        />
      </div>
    )
  }
}

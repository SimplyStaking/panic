import { dismissModal } from '@simply-vc/uikit';
import { Component, h, Prop } from '@stencil/core';

export type MoreInfoType = {
  title: string,
  messages: string[]
}

@Component({
  tag: 'panic-installer-more-info-modal',
  styleUrl: 'panic-installer-more-info-modal.scss'
})
export class PanicInstallerMoreInfoModal {

  @Prop() messages: MoreInfoType[];
  @Prop() class: string;

  componentWillLoad() {
    let baseClass = "panic-installer-more-info-modal";
    const className = baseClass + "__" + this.class;

    let ionModal = document.getElementsByTagName("ion-modal")[0];
    ionModal.classList.add(className);
  }

  render() {

    return (
      <svc-content-container>
        {this.messages && this.messages.map((message: MoreInfoType) => {
          return (
            <svc-surface label={message.title}>
              {
                message.messages && message.messages.map((subMessage: string) => {
                  return (
                    <div class={"panic-installer-more-info-modal__info-list-item"}>
                      {subMessage}
                    </div>
                  )
                })
              }
            </svc-surface>
          )
        })}

        <div style={{ display: "flex", justifyContent: "center" }}>
          <svc-button iconName={"checkmark"} onClick={() => {
            dismissModal();
          }}>Got it!
          </svc-button>
        </div>
      </svc-content-container>
    );
  }
}

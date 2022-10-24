import { Component, h } from '@stencil/core';

@Component({
    tag: 'panic-installer-modal',
    styleUrl: 'panic-installer-modal.scss'
})
export class PanicInstallerModal {

    render() {
        return (
            <svc-content-container class={"panic-installer-modal"}>
                <svc-surface class={"panic-installer-modal__content"}>
                    <div class={"panic-installer-modal__icon"}>
                        <ion-icon name={"settings-outline"} color={"primary"}/>
                    </div>

                    <div class={"panic-installer-modal__inner-text"}>
                        <svc-text>
                            <p>
                                No configurations detected!
                            </p>
                        </svc-text>
                        <svc-text>
                            <p>
                                Start the installer and we'll guide you through the configuration.
                            </p>
                        </svc-text>
                    </div>

                    <svc-button href={"/installer/welcome"} iconName={"arrow-forward-circle"}>Start</svc-button>
                </svc-surface>
            </svc-content-container>
        );
    }

    componentDidRender() {
        const svcButton: HTMLElement = document.getElementsByTagName("svc-button")[0];
        if (svcButton)
            svcButton.children[0].className += " button-block"
    }

}

import {Component, h, Host, Prop} from '@stencil/core';
import {
  ALERTS_TEXT,
  BLOCKCHAIN_TEXT,
  CHANNELS_TEXT,
  FEEDBACK_TEXT,
  INTRO_TEXT,
  NODES_TEXT,
  REPOS_TEXT
} from "../content/welcome";
import {Router} from "stencil-router-v2";
import { dismissModal } from '@simply-vc/uikit';

@Component({
  tag: 'panic-installer-welcome',
  styleUrl: 'panic-installer-welcome.scss'
})
export class PanicInstallerWelcome {

  /**
   * Stencil Router object for page navigation.
   */
  @Prop() router: Router;

  componentWillLoad() {
    // might be necessary
    // i.e. when the node operator opens a modal and then clicks in the browser's back button
    dismissModal();
  }

  render() {
    return (
      <Host>
        <panic-header showMenu={false} />

        <svc-content-container class={"panic-installer-welcome__container"}>
          <svc-surface>
            <div class={"panic-installer-welcome__heading"}>
              <svc-icon name={"rocket"} size={"120px"} color={"primary"} />
              <svc-label>Installer Journey</svc-label>
            </div>

            <svc-text color={"primary"}>
              <p class={"panic-installer-welcome__message"}>
                {INTRO_TEXT}
              </p>
            </svc-text>

            <ul class={"panic-installer-welcome__list"}>
              <li class={"panic-installer-welcome__list-item"}>
                <div class={"panic-installer-welcome__list-item-subtitle"}>
                  <svc-icon name={"link"} size={"25px"} /> Blockchain
                </div>
                <div class={"panic-installer-welcome__list-item-excerpt"}>
                  {BLOCKCHAIN_TEXT}
                </div>
              </li>

              <li class={"panic-installer-welcome__list-item"}>
                <div class={"panic-installer-welcome__list-item-subtitle"}>
                  <svc-icon name={"call"} size={"25px"} />
                  Channels
                </div>
                <div class={"panic-installer-welcome__list-item-excerpt"}>
                  {CHANNELS_TEXT}
                </div>
              </li>

              <li class={"panic-installer-welcome__list-item"}>
                <div class={"panic-installer-welcome__list-item-subtitle"}>
                  <svc-icon name={"server"} size={"25px"} />
                  Nodes
                </div>
                <div class={"panic-installer-welcome__list-item-excerpt"}>
                  {NODES_TEXT}
                </div>
              </li>

              <li class={"panic-installer-welcome__list-item"}>
                <div class={"panic-installer-welcome__list-item-subtitle"}>
                  <svc-icon name={"code-slash"} size={"25px"} />
                  Repositories
                </div>
                <div class={"panic-installer-welcome__list-item-excerpt"}>
                  {REPOS_TEXT}
                </div>
              </li>

              <li class={"panic-installer-welcome__list-item"}>
                <div class={"panic-installer-welcome__list-item-subtitle"}>
                  <svc-icon name={"notifications-circle"} size={"25px"} />
                  Alerts
                </div>
                <div class={"panic-installer-welcome__list-item-excerpt"}>
                  {ALERTS_TEXT}
                </div>
              </li>

              <li class={"panic-installer-welcome__list-item"}>
                <div class={"panic-installer-welcome__list-item-subtitle"}>
                  <svc-icon name={"checkmark-circle"} size={"25px"} />
                  Feedback
                </div>
                <div class={"panic-installer-welcome__list-item-excerpt"}>
                  {FEEDBACK_TEXT}
                </div>
              </li>
            </ul>

            <div class={"panic-installer-welcome__button"}>
              <svc-button
                iconName={"arrow-forward-circle"}
                color={"secondary"}
                href={"/installer/sub-chain"}
              >
                Start Configuration
              </svc-button>
            </div>
          </svc-surface>
        </svc-content-container>

        <panic-footer />
      </Host>
    );
  }

}
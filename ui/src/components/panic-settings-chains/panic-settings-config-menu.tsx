import { dismissModal } from '@simply-vc/uikit';
import { h, Component, Prop, Host } from '@stencil/core';
import { Config } from '../../../../entities/ts/Config';

@Component({
    tag: "panic-settings-config-menu"
})
export class PaniSettingsConfigMenu {

    /**
     * The config being edited.
     */
    @Prop() config: Config;

    /**
     * Checks if the current URL contains `path`.
     * 
     * @param path URL path
     * @returns `true` if the current URL contais `path`, otherwise `false`.
     */
    isDisabled(path: string): boolean {
        return window.location.pathname.indexOf(path) !== -1;
    }

    render() {
        return (
            <Host>
                <svc-header headline={`Choose what to edit for ${this.config.subChain.name}`} menuPosition={"end"}>
                    <ion-buttons slot={"menu"}>
                        <svc-button iconPosition={"icon-only"} iconName={"close"} onClick={() => dismissModal() } />
                    </ion-buttons>
                </svc-header>
                <svc-content-container>
                    <svc-button
                        disabled={this.isDisabled("sub-chain")}
                        iconName={"link"}
                        iconPosition={"start"}
                        color={"secondary"}
                        href={`/settings/edit/sub-chain/${this.config.id}`}
                    >
                        Sub-chain
                    </svc-button>
                    <svc-button
                        disabled={this.isDisabled("channels")}
                        iconName={"call"}
                        iconPosition={"start"}
                        color={"secondary"}
                        href={`/settings/edit/channels/${this.config.id}`}
                    >
                        Channels
                    </svc-button>
                    <svc-button
                        disabled={this.isDisabled("sources")}
                        iconName={"server"}
                        iconPosition={"start"}
                        color={"secondary"}
                        href={`/settings/edit/sources/${this.config.id}`}
                    >
                        Nodes
                    </svc-button>
                    <svc-button
                        disabled={this.isDisabled("repositories")}
                        iconName={"code-slash"}
                        iconPosition={"start"}
                        color={"secondary"}
                        href={`/settings/edit/repositories/${this.config.id}`}
                    >
                        Repositories
                    </svc-button>
                    <svc-button
                        disabled={this.isDisabled("alerts")}
                        iconName={"notifications-circle"}
                        iconPosition={"start"}
                        color={"secondary"}
                        href={`/settings/edit/alerts/${this.config.id}`}
                    >
                        Alerts
                    </svc-button>
                </svc-content-container>
            </Host>
        );
    }
}
import {Component, h, Host, Listen} from '@stencil/core';
import {match, Route, createRouter} from 'stencil-router-v2';
import {BaseChain} from '../../../../entities/ts/BaseChain';
import {BaseChainService} from '../../services/base-chain/base-chain.service';
import {PanicRootInterface} from './panic-root.interface';
import {ChannelType} from "../../../../entities/ts/ChannelType";
import {SeverityType} from "../../../../entities/ts/SeverityType";
import {RepositoryType} from "../../../../entities/ts/RepositoryType";
import {SourceType} from "../../../../entities/ts/SourceType";
import {DomainService} from "../../services/domain/domain.service";
import {ThresholdAlertSubconfig} from "../../../../entities/ts/ThresholdAlertSubconfig";
import {SeverityAlertSubconfig} from "../../../../entities/ts/SeverityAlertSubconfig";
import { ConfigService } from '../../services/config/config.service';
import { Config } from '../../../../entities/ts/Config';
import { createAlert } from '@simply-vc/uikit';
import { HelperAPI } from '../../utils/helpers';

const Router = createRouter();

@Component({
    tag: 'panic-root',
    styleUrl: 'panic-root.scss'
})
export class PanicRoot implements PanicRootInterface {

    /**
     * List of base chains supported by PANIC.
     */
    baseChains: BaseChain[];

    /**
     * List of channel types supported by PANIC.
     */
    channelTypes: ChannelType[];

    /**
     * List of threshold alerts supported by PANIC.
     */
    thresholdAlerts: ThresholdAlertSubconfig[];

    /**
     * List of severity alerts supported by PANIC.
     */
    severityAlerts: SeverityAlertSubconfig[];

    /**
     * List of severity types supported by PANIC.
     */
    severityTypes: SeverityType[];

    /**
     * List of repository types supported by PANIC.
     */
    repositoryTypes: RepositoryType[];

    /**
     * List of source types supported by PANIC.
     */
    sourceTypes: SourceType[];

    async componentWillLoad() {
        const configNotReady: Config = await this.getConfigNotReady();

        if (this.shouldShowLeftInstallerModal(configNotReady))
            createAlert({
                header: "Attention",
                message: `
                    You left the Installer without completing all the configuration steps for ${configNotReady.subChain.name} (${configNotReady.baseChain.name}).
                    If you proceed, this configuration will be lost.
                `,
                cancelButtonLabel: "Back to Installer",
                confirmButtonLabel: "Proceed",
                eventName: "onConfigNotReady",
                cssClass: "panic-root__config-not-ready",
                eventData: {
                    configId: configNotReady.id
                }
            }).then(() => (document.getElementsByTagName("ion-alert")[0] as any).backdropDismiss = false)

        await this.loadDomainEntities();
    }

    /**
     * Determines if the modal when the node operator leaves the installer should be shown or not.
     *
     * It will only be displayed when the node operator actually leaves the installer/edit journey.
     * In other words, if he just refreshes the page and the URL still points to /installer or /settings, then the modal isn't shown.
     *
     * @param config the config to be checked.
     * @returns `true` if the config is not ready and the node operator left the installer, otherwise `false`.
     */
    shouldShowLeftInstallerModal(config: Config): boolean {
        const isConfigNotReady: boolean = config !== undefined && !config.ready;
        const isInstallerURL: boolean = HelperAPI.isFromSettings() || HelperAPI.isFromInstaller();
        return isConfigNotReady && !isInstallerURL;
    }

    @Listen("onConfigNotReady", {target: "window"})
    configNotReadyHandler(e: CustomEvent) {
        const configId: string = e.detail.data.configId;
        const removeConfig: boolean = e.detail.confirmed;

        if (removeConfig) {
            ConfigService.getInstance().delete(configId).then(() => {
                HelperAPI.raiseToast("Config removed!", 2500, "success");
                HelperAPI.changePage(Router, '/');
            });
            localStorage.removeItem('configId');
        } else
            HelperAPI.changePage(Router, `/installer/sub-chain/${configId}`);
    }

    async loadDomainEntities() {
        const baseChains = await BaseChainService.getInstance().getAll();
        this.baseChains = baseChains.sort((next: BaseChain, curr: BaseChain) => {
            if (next.name > curr.name)
                return 1;

            if (next.name < curr.name)
                return -1;

            if (next.name == curr.name)
                return 0;
        });
        this.channelTypes = await DomainService.getInstance().getAllChannelTypes();
        this.severityTypes = await DomainService.getInstance().getAllSeverityTypes();
        this.repositoryTypes = await DomainService.getInstance().getAllRepositoryTypes();
        this.sourceTypes = await DomainService.getInstance().getAllSourceTypes();
        this.channelTypes = await DomainService.getInstance().getAllChannelTypes();
    }

    /**
     * Queries the persistence layer, looking for some config which isn't ready.
     *
     * @returns a {@link Config} if any, otherwise `undefined`.
     */
    async getConfigNotReady(): Promise<Config> {
        const configs: Config[] = await ConfigService.getInstance().getAll();
        const configNotReady: Config = configs.find(config => !config.ready);
        return configNotReady;
    }

    render() {
        return (
            <Host>
                <svc-app>
                    <Router.Switch>
                        <Route path={"/"}>
                            <div>
                                <panic-header/>
                                <svc-content-container>
                                    <panic-dashboard-overview/>
                                    <panic-alerts-overview/>
                                </svc-content-container>
                                <panic-footer/>
                            </div>
                        </Route>

                        <Route path={match('/systems-overview/:chain')}
                           render={(param) => {
                               return <div>
                                   <panic-header/>
                                   <svc-content-container>
                                       <panic-systems-overview
                                           baseChainName={param.chain}/>
                                   </svc-content-container>
                                   <panic-footer/>
                               </div>
                           }}>
                        </Route>

                        {/******************************** settings routes ***********************************/}

                        <Route path={'/settings/chains'}>
                            <panic-settings-chains
                                router={Router}
                            />
                        </Route>

                        <Route path={'/settings/channels'}>
                            <panic-settings-channels
                                channelTypes={this.channelTypes}
                            />
                        </Route>

                        {/******************************** welcome routes ***********************************/}

                        <Route path={'/installer/welcome'}>
                            <panic-installer-welcome
                                router={Router}
                            />
                        </Route>

                        {/******************************** sub-chain routes ***********************************/}

                        <Route path={'/installer/sub-chain'}>
                            <panic-installer-sub-chain
                                router={Router}
                                baseChains={this.baseChains}
                            />
                        </Route>

                        <Route
                            path={match('/installer/sub-chain/:configId')}
                            render={({configId}) => {
                                return (
                                    <panic-installer-sub-chain
                                        router={Router}
                                        configId={configId}
                                        baseChains={this.baseChains}
                                    />
                                )
                            }}
                        />

                        <Route path={match('/settings/edit/sub-chain/:configId')} render={({configId}) => {
                            return (
                                <panic-installer-sub-chain
                                    router={Router}
                                    configId={configId}
                                    baseChains={this.baseChains}
                                />
                            )
                        }}
                        />

                        <Route path={'/settings/new/sub-chain'}>
                            <panic-installer-sub-chain
                                router={Router}
                                baseChains={this.baseChains}
                            />
                        </Route>

                        <Route path={match('/settings/new/sub-chain/:configId')} render={({configId}) => {
                            return (
                                <panic-installer-sub-chain
                                    router={Router}
                                    configId={configId}
                                    baseChains={this.baseChains}
                                />
                            )
                        }}
                        />

                        {/******************************** channel routes ***********************************/}

                        <Route path={match('/installer/channels/:configId')} render={({configId}) =>
                        {
                            return (
                                <panic-installer-channels
                                    router={Router}
                                    configId={configId}
                                    channelTypes={this.channelTypes}
                                />
                            )
                        }}
                        />

                        <Route path={match('/settings/edit/channels/:configId')} render={({configId}) =>
                        {
                            return (
                                <panic-installer-channels
                                    router={Router}
                                    configId={configId}
                                    channelTypes={this.channelTypes}
                                />
                            )
                        }}
                        />

                        <Route path={match('/settings/new/channels/:configId')} render={({configId}) =>
                        {
                            return (
                                <panic-installer-channels
                                    router={Router}
                                    configId={configId}
                                    channelTypes={this.channelTypes}
                                />
                            )
                        }}
                        />

                        {/******************************** sources routes ***********************************/}

                        <Route path={match('/installer/sources/:configId')} render={({configId}) => {
                            return (
                                <panic-installer-sources
                                    router={Router}
                                    configId={configId}
                                    sourceTypes={this.sourceTypes}
                                />
                            )
                        }}
                        />

                        <Route path={match('/settings/edit/sources/:configId')} render={({configId}) => {
                            return (
                                <panic-installer-sources
                                    router={Router}
                                    configId={configId}
                                    sourceTypes={this.sourceTypes}
                                />
                            )
                        }}
                        />

                        <Route path={match('/settings/new/sources/:configId')} render={({configId}) => {
                            return (
                                <panic-installer-sources
                                    router={Router}
                                    configId={configId}
                                    sourceTypes={this.sourceTypes}
                                />
                            )
                        }}
                        />

                        {/******************************** Repo routes ***********************************/}

                        <Route path={match('/installer/repositories/:configId')} render={({configId}) => {
                            return (
                                <panic-installer-repo
                                    router={Router}
                                    configId={configId}
                                    repositoryTypes={this.repositoryTypes}
                                />
                            )}
                        }
                        />

                        <Route path={match('/settings/edit/repositories/:configId')} render={({configId}) => {
                            return (
                                <panic-installer-repo
                                    router={Router}
                                    configId={configId}
                                    repositoryTypes={this.repositoryTypes}
                                />
                            )}
                        }
                        />

                        <Route path={match('/settings/new/repositories/:configId')} render={({configId}) => {
                            return (
                                <panic-installer-repo
                                    router={Router}
                                    configId={configId}
                                    repositoryTypes={this.repositoryTypes}
                                />
                            )}
                        }
                        />

                        {/******************************** Alert routes ***********************************/}

                        <Route path={match('/installer/alerts/:configId')} render={({configId}) => {
                            return (
                              <panic-installer-alerts
                                router={Router}
                                configId={configId}
                                severityTypes={this.severityTypes}
                              />
                            )}
                        }
                        />

                        <Route path={match('/settings/edit/alerts/:configId')} render={({configId}) => {
                            return (
                              <panic-installer-alerts
                                router={Router}
                                configId={configId}
                                severityTypes={this.severityTypes}
                              />
                            )}
                        }
                        />

                        <Route path={match('/settings/new/alerts/:configId')} render={({configId}) => {
                            return (
                              <panic-installer-alerts
                                router={Router}
                                configId={configId}
                                severityTypes={this.severityTypes}
                              />
                            )}
                        }
                        />

                        {/******************************** Feedback routes ***********************************/}

                        <Route path={match('/installer/feedback/:configId')} render={({configId}) => {
                            return (
                                <panic-installer-feedback
                                    router={Router}
                                    configId={configId}
                                />
                            )
                        }}
                        />

                        <Route path={match('/settings/edit/feedback/:configId')} render={({configId}) => {
                            return (
                                <panic-installer-feedback
                                    router={Router}
                                    configId={configId}
                                />
                            )
                        }}
                        />

                        <Route path={match('/settings/new/feedback/:configId')} render={({configId}) => {
                            return (
                                <panic-installer-feedback
                                    router={Router}
                                    configId={configId}
                                />
                            )
                        }}
                        />
                    </Router.Switch>
                </svc-app>
            </Host>
        );
    }
}
import {Component, h, Host, Prop, State} from '@stencil/core';
import {BaseChain, SubChain} from '../../interfaces/chains';
import {Metrics} from '../../interfaces/metrics';
import {ChainsAPI} from '../../utils/chains';
import {POLLING_FREQUENCY} from '../../utils/constants';
import {
    SystemsOverviewBaseChainNotFoundError,
    SystemsOverviewNoBaseChainSpecifiedError
} from '../../utils/errors';
import {MetricsAPI} from '../../utils/metrics';
import {PanicSystemsOverviewInterface} from './panic-systems-overview.interface';
import {SystemsOverviewAPI} from './utils/panic-systems-overview.utils';

@Component({
    tag: 'panic-systems-overview',
    styleUrl: 'panic-systems-overview.scss'
})
export class PanicSystemsOverview implements PanicSystemsOverviewInterface {

    @Prop() baseChainName: string;
    @State() systemMetrics: Metrics[];
    _chains: SubChain[] = [];
    _updater: number;
    _updateFrequency: number = POLLING_FREQUENCY;

    async componentWillLoad() {
        if (!this.baseChainName) {
            throw new SystemsOverviewNoBaseChainSpecifiedError();
        }

        try {
            // Get specified base chain.
            const baseChain: BaseChain = await ChainsAPI.getBaseChainByName(this.baseChainName);
            // Check if base chain exists.
            if (!baseChain) {
                throw new SystemsOverviewBaseChainNotFoundError(this.baseChainName);
            }

            // Store chains.
            this._chains = baseChain.subChains;
            await this.reRenderAction();

            this._updater = window.setInterval(async () => {
                await this.reRenderAction();
            }, this._updateFrequency);
        } catch (error: any) {
            console.error(error);
        }
    }

    async reRenderAction() {
        // Get metrics and alerts metrics.
        this.systemMetrics = await MetricsAPI.getMetrics(this._chains);
    }

    componentDidLoad() {
        // Update chains dropdown to show selected chain.
        const chainsDropdownLabel: Element = document.querySelector('panic-header svc-dropdown-menu ion-label');
        if (chainsDropdownLabel) {
            chainsDropdownLabel.textContent = this.baseChainName;
        }
    }

    render() {
        return (
            <Host>
                <svc-surface
                    label={`SYSTEMS OVERVIEW - ${this.baseChainName.toUpperCase()}`}
                    labelPosition={"center"}>
                    <h3 class='panic-systems-overview__subtitle'>System
                        Metrics</h3>

                    {/* Data table */}
                    {SystemsOverviewAPI.getDataTableJSX(this.systemMetrics)}

                    {SystemsOverviewAPI.checkIfAnyNotAvailable(this.systemMetrics) &&
                    <svc-label color="dark" position="start"
                               class="panic-systems-overview__info-message">N/A:
                        Data is not available from back-end API.</svc-label>}
                </svc-surface>
            </Host>
        );
    }
}

import {Component, h, Host, Prop} from '@stencil/core';
import {getNodeMoreInfoByBaseChain, NODE_HEADLINE} from '../../content/node';
import {EVM_NODE_HEADLINE, EVM_NODE_MORE_INFO} from '../../content/evmnode';
import {evmNodeCols, nodeCols, systemCols} from '../datatable';
import {getSystemMoreInfoByBaseChain, SYSTEM_HEADLINE} from '../../content/system';
import {BaseChain} from "../../../../../../entities/ts/BaseChain";
import {Config} from "../../../../../../entities/ts/Config";

@Component({
  tag: 'panic-installer-sources-cards',
  styleUrl: 'panic-installer-sources-cards.scss'
})
export class PanicInstallerSourcesCards {

    @Prop() baseChain: BaseChain;
    @Prop() config: Config;
    @Prop() monitorNetwork: boolean;
    @Prop() governanceAddresses: string;

    render() {
        const subChainName = this.config.subChain.name;
        const nodesSourceType = this.baseChain.sources.find((source) => source.value === 'nodes');
        const evmNodesSourceType = this.baseChain.sources.find((source) => source.value === 'evm_nodes');
        const contractSourceType = this.baseChain.sources.find((source) => source.value === 'contract');
        const systemsSourceType = this.baseChain.sources.find((source) => source.value === 'systems');

        return (
            <Host class={`panic-installer-sources__cards`}>
                <svc-content-container>
                    {   nodesSourceType &&
                        <panic-installer-sources-card
                            baseChain={this.baseChain}
                            sourceType={nodesSourceType}
                            sources={this.config.nodes}
                            monitorNetwork={this.monitorNetwork}
                            governanceAddresses={this.governanceAddresses}
                            cols={nodeCols}
                            addButtonLabel={"Add Node"}
                            cardTitle={`Nodes Setup For ${subChainName}`}
                            headline={NODE_HEADLINE}
                            messages={getNodeMoreInfoByBaseChain(this.baseChain.value)}
                        />
                    }

                    {   evmNodesSourceType &&
                        <panic-installer-sources-card
                            baseChain={this.baseChain}
                            sourceType={evmNodesSourceType}
                            sources={this.config.evm_nodes}
                            cols={evmNodeCols}
                            addButtonLabel={"Add EVM Node"}
                            cardTitle={"EVM Nodes Setup"}
                            headline={EVM_NODE_HEADLINE}
                            messages={EVM_NODE_MORE_INFO}
                        />
                    }

                    {   contractSourceType &&
                        <panic-installer-sources-contract
                            contract={this.config.contract}
                        />
                    }

                    {   systemsSourceType &&
                        <panic-installer-sources-card
                            baseChain={this.baseChain}
                            sourceType={systemsSourceType}
                            sources={this.config.systems}
                            cols={systemCols}
                            addButtonLabel={"Add System"}
                            cardTitle={"Systems Setup"}
                            headline={SYSTEM_HEADLINE}
                            messages={getSystemMoreInfoByBaseChain(this.baseChain.value)}
                        />
                    }

                    <panic-installer-nav config={this.config} />
                </svc-content-container>
            </Host>
        );
    }
}

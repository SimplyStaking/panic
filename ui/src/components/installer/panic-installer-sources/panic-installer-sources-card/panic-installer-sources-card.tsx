import {createAlert, createModal} from '@simply-vc/uikit';
import {DataTableHeaderType, DataTableRowsType} from '@simply-vc/uikit/dist/types/types/datatable';
import {Component, h, Prop, State} from '@stencil/core';
import {HelperAPI} from '../../../../utils/helpers';
import {MoreInfoType} from '../../panic-installer-more-info-modal/panic-installer-more-info-modal';
import {SourceType} from "../../../../../../entities/ts/SourceType";
import {BaseChain} from "../../../../../../entities/ts/BaseChain";
import {Sources} from "../panic-installer-sources";

@Component({
  tag: 'panic-installer-sources-card',
  styleUrl: 'panic-installer-sources-card.scss'
})
export class PanicInstallerSourcesCard {

  @Prop() baseChain: BaseChain;
  @Prop() sourceType: SourceType;
  @Prop() sources: Sources[];
  @Prop() monitorNetwork: boolean;
  @Prop() governanceAddresses: string;
  @Prop() cols: DataTableHeaderType[];
  @Prop() addButtonLabel: string;
  @Prop() cardTitle: string;
  @Prop() headline: string;
  @Prop() messages: MoreInfoType[];

  @State() _rows: DataTableRowsType = [];

  /**
   * Creates a modal with a form for the given source using panic-installer-sources-modal.
   *
   * @param source The source to be used as a panic-installer-sources-modal prop.
   */
  createFormModal(source?: Sources): void {
    createModal("panic-installer-sources-modal", {
      sourceType: this.sourceType,
      source: source,
      baseChain: this.baseChain
    },
    {
      backdropDismiss: false,
      cssClass: `panic-installer-sources-modal__${this.sourceType.value}`
    });
  }

  /**
   * Parses sources into {@link DataTableRowsType}.
   *
   * @returns {@link DataTableRowsType} populated with sources data
   */
  parseSources(): DataTableRowsType {
    const rows: DataTableRowsType = [];

    // @ts-ignore
    this.sources?.map(({id, name, monitorNode, monitor}: Sources) => {
      // default: node sources
      let monitoringEnabled: boolean = monitorNode;
      let monitoringFieldName: string = "monitorNode";

      // custom handling for system and evm node sources
      if (this.isSourceTypeSystems() || this.isSourceTypeEvmNodes()) {
        monitoringEnabled = monitor;
        monitoringFieldName = "monitor";
      }

      rows.push({
        cells: [
          {
            label: name,
            value: id
          },
          {
            label: <input type="checkbox" checked={monitoringEnabled} onClick={() => {
              HelperAPI.emitEvent("enableSource", {
                id: id,
                sourceType: this.sourceType,
                monitoringFieldName: monitoringFieldName
              });
            }} />,
            value: monitoringEnabled
          }
        ],
        id: id
      });
    });

    return rows;
  }

  /**
   * Returns whether the source type is systems.
   */
  isSourceTypeSystems(): boolean {
    return this.sourceType.value === "systems";
  }

  /**
   * Returns whether the source type is nodes.
   */
  isSourceTypeNodes(): boolean {
    return this.sourceType.value === "nodes";
  }

  /**
   * Returns whether the source type is evm nodes.
   */
  isSourceTypeEvmNodes(): boolean {
    return this.sourceType.value === "evm_nodes";
  }

  /**
   * Returns whether the base chain is cosmos.
   */
  isBaseChainCosmos(): boolean {
    return this.baseChain.value === "cosmos";
  }

  /**
   * Returns whether the base chain is substrate.
   */
  isBaseChainSubstrate(): boolean {
    return this.baseChain.value === "substrate";
  }

  /**
   * Returns whether the base chain is general.
   */
  isBaseChainGeneral(): boolean {
    return this.baseChain.value === "general";
  }

  /**
   * Returns whether there are any sources.
   */
  hasSources(): boolean {
    return this.sources?.length > 0;
  }

  /**
   * Returns whether to display network monitoring JSX.
   */
  shouldDisplayNetworkMonitoring(): boolean {
    return (this.isBaseChainCosmos() || this.isBaseChainSubstrate()) && this.hasSources();
  }

  /**
   * Returns whether to display icon and step counter JSX.
   */
  shouldDisplayIconAndStepCounter(): boolean {
    const nodeCard = this.isSourceTypeNodes();
    const generalSystemCard = this.isBaseChainGeneral() && this.isSourceTypeSystems();
    return nodeCard || generalSystemCard;
  }

  /**
   * Adds an event listener for an edit source operation.
   */
  addEditEventListener(): void {
    window.addEventListener(`edit${this.sourceType.value}`, (e: CustomEvent) => {
      this.createFormModal(this.sources.find((source) => source.id === e.detail.id));
    });
  }

  /**
   * Adds an event listener for a delete source operation.
   */
  addDeleteEventListener(): void {
    window.addEventListener(`delete${this.sourceType.value}`, async (e: CustomEvent) => {
      await createAlert({
        header: "Attention!",
        message: "If you proceed, the item will be deleted.",
        eventName: "deleteSource",
        eventData: {
          id: e.detail.id,
          type: this.sourceType.value
        }
      });
    });
  }

  componentWillLoad() {
    this.addEditEventListener();
    this.addDeleteEventListener();
  }

  render() {
    this._rows = this.parseSources();

    return (
      <div>
      <svc-surface class={"panic-installer-sources__container"}>
        {
          this.shouldDisplayIconAndStepCounter() &&
          <div class={'panic-installer-sources__icon'}>
            <ion-icon color={"primary"} name={"server"}/>
          </div>
        }
        <svc-label class={'panic-installer-sources__title'}>{ this.cardTitle }</svc-label>
        {
          this.shouldDisplayIconAndStepCounter() &&
          <svc-label class={'panic-installer-sources__step'}>step 3/5</svc-label>
        }

        <div class={"panic-installer-sources__more-info"}>
            <p>
                { this.headline }
            </p>
            <svc-buttons-container>
                <svc-button color={"secondary"} iconName={"information-circle"} iconPosition={"icon-only"} onClick={() => {
                    createModal("panic-installer-more-info-modal", {
                      messages: this.messages,
                      class: `${this.baseChain.value}-${this.sourceType.value}`
                    });
                }} />
            </svc-buttons-container>
        </div>
        <div class={'panic-installer-sources__add-button-container'}>
            <svc-button color={"secondary"} iconName={"add-circle"} onClick={() => { this.createFormModal(); }}>{ this.addButtonLabel }</svc-button>
        </div>

        {
          this.hasSources() &&
          <svc-data-table
              class={"panic-installer-sources__crud-data-table"}
              id={this.sourceType.value}
              cols={this.cols}
              rows={this._rows}
              mode={"crud"}
              editEventName={`edit${this.sourceType.value}`}
              deleteEventName={`delete${this.sourceType.value}`}
          />
        }
      </svc-surface>
        {
          this.shouldDisplayNetworkMonitoring()  &&
          <svc-surface>
            <svc-toggle
              class={"panic-installer-sources__network_monitoring_toggle"}
              label={"Network Monitoring"}
              checked={this.monitorNetwork}
              value={true}
              helpText={"When checked, it will enable monitoring data such as governance proposals."}
              position={"end"}
              lines={"inset"}
              onChangeEventName={"monitorNetworkChange"}
            />
            {
              this.isBaseChainSubstrate() &&
              <div class={'panic-installer-sources-form__row-container'}>
                <svc-multiple-input
                  name={'governanceAddresses'}
                  value={this.governanceAddresses
                    && HelperAPI.extractChipTypeArrayFromCommaSeparatedString(this.governanceAddresses, true)}
                  label={'Governance Addresses'}
                  placeholder={'12xtGHlkyrmbniiWQqJtECiBQrMn8AypQcXhnQAc6RB6JlKm [Press Enter after each address]'}
                  outline={true}
                  disabled={!this.monitorNetwork}
                  addEventName={"governanceAddressesAdd"}
                  removeEventName={"governanceAddressesRemove"}
                />
              </div>
            }
          </svc-surface>
        }
      </div>
    );
  }
}

import {Component, h, Host, Listen, Prop, State} from '@stencil/core';
import {
  DataTableRowsType,
  DataTableRow
} from "@simply-vc/uikit/dist/types/types/datatable";
import {Config} from "../../../../entities/ts/Config";
import {CONFIG_ID_LOCAL_STORAGE_KEY, SUBCHAIN_TABLE_HEADERS} from "../../utils/constants";
import {ConfigService} from '../../services/config/config.service';
import {Router} from "stencil-router-v2";
import {HelperAPI} from "../../utils/helpers";
import {createAlert, createModal} from "@simply-vc/uikit";

@Component({
  tag: 'panic-settings-chains',
  styleUrl: 'panic-settings-chains.scss'
})
export class PanicSettingsChains {

  /**
   * Stencil Router object for page navigation.
   */
  @Prop() router: Router;

  /**
   * List of configurations available to the node operator.
   */
  @State() configs: Config[] = [];

  async componentWillLoad() {
    this.configs = await ConfigService.getInstance().getAll();

    // cleaning configId to avoid side-effects
    localStorage.removeItem(CONFIG_ID_LOCAL_STORAGE_KEY);
  }

  /**
   * Listens to the `editConfig` {@link CustomEvent} to trigger the navigation.
   */
  @Listen("editConfig", {target: "window"})
  async editConfigHandler(e: CustomEvent){
    const id: string = e.detail.id
    localStorage.setItem(CONFIG_ID_LOCAL_STORAGE_KEY, id);
    const config: Config = await ConfigService.getInstance().getByID(id);

    createModal("panic-settings-config-menu", {
      config: config
    },
    {
      cssClass: "panic-settings-config-menu-modal"
    })
  }

  /**
   * Given a Config object ID this function will retrieve the index of the
   * object from `this.configs` matching the ID
   * @param configId The Config object ID
   */
  findConfigIndex(configId: string): number {
    return this.configs.findIndex(config => config.id === configId)
  }

  /**
   * Whenever a deleteConfig is detected, this handler displays a confirmation
   * modal
   * @param event The raised deleteConfig event
   */
  @Listen('deleteConfig', {target: 'window'})
  deleteConfigHandler(event: CustomEvent) {
    const configIndex = this.findConfigIndex(event.detail.id)
    const config = this.configs[configIndex]

    createAlert({
      'header': 'Delete Confirmation',
      'message': `Are you sure you want to delete the configuration for ${config.subChain.name}?`,
      'eventName': 'configDeleteConfirmation',
      'eventData': config
    });
  }

  /**
   * Whenever a response is detected on the config delete confirmation modal
   * this handler does the following:
   *
   * If Deletion Confirmed: Performs an API call to remove the config from the
   *                        database and removes the config from the component
   *                        state
   * If Deletion canceled: Does nothing
   * @param event
   */
  @Listen('configDeleteConfirmation', {target: 'window'})
  async handleConfigDeleteConfirmation(event: CustomEvent) {
    const deletionConfirmed = event.detail.confirmed;
    const configRemove = event.detail.data;

    if (deletionConfirmed){
      const removed: boolean = await ConfigService.getInstance().delete(configRemove.id);

      if (removed) {
        this.configs = this.configs.filter(config => config.id !== configRemove.id);
        HelperAPI.raiseToast("Chain configuration removed successfully!");
      } else {
        HelperAPI.raiseToast("Could not delete configuration from database!", 2000, "danger");
      }
    }
  }

  /**
   * Parses the `config` to an object of {@link DataTableRow}.
   *
   * @param config the config to be parsed.
   * @returns populated {@link DataTableRow} object.
   */
  parseConfig(config: Config): DataTableRow {
    return {
      cells: [
        {
          value: config.subChain.id,
          label: config.subChain.name,
        },
        {
          value: config.baseChain.id,
          label: config.baseChain.name,
        },
      ],
      id: config.id
    };
  }

  /**
   * Parses the list of `configs` and return the sub-chains in the
   * {@link DataTableRowsType} format.
   *
   * @returns `DataTableRowsType` which is read by the data table.
   */
  getConfigsAsDataTableRowsType(): DataTableRowsType {
    return this.configs.map((config: Config) => {
        return this.parseConfig(config);
      }
    );
  }

  render() {
    return (
      <Host>
        <panic-header showMenu={true}/>

        <svc-content-container class={"panic-settings-chains__container"}>
          <svc-surface>
            <svc-label class={"panic-settings-chains__title"}>
              Sub-Chains
            </svc-label>

            <div class={"panic-settings-chains__add-sub-chain-button"}>
              <svc-button
                id={"add"}
                iconName={"add-circle"}
                color={"secondary"}
                href={"/settings/new/sub-chain"}
                onClick={() => localStorage.removeItem(CONFIG_ID_LOCAL_STORAGE_KEY)}
              >
                Add a sub-chain
              </svc-button>
            </div>

            <svc-data-table
              class={"panic-settings-chains__crud-data-table"}
              mode={"crud"}
              cols={SUBCHAIN_TABLE_HEADERS}
              rows={this.getConfigsAsDataTableRowsType()}
              editEventName={"editConfig"}
              deleteEventName={"deleteConfig"}
              noRecordsMessage={"Click in the button above to add your first configuration..."}
            />

          </svc-surface>
        </svc-content-container>

        <panic-footer/>

      </Host>
    );
  }
}

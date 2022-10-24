import {Component, h, Host, Listen, Prop, State} from '@stencil/core';
import {createAlert, createModal, dismissModal} from "@simply-vc/uikit";
import {HelperAPI} from "../../../utils/helpers";
import {
  CHANNEL_TABLE_HEADERS,
  getSecondaryText,
  MAIN_TEXT,
  MORE_INFO_MESSAGES
} from "../content/channels";
import {DataTableRowsType} from "@simply-vc/uikit/dist/types/types/datatable";
import {CHANNEL_FILTERS,} from "../../../utils/constants";
import {Router} from "stencil-router-v2";
import {Config} from "../../../../../entities/ts/Config";
import {ConfigService} from "../../../services/config/config.service";
import {ChannelService} from "../../../services/channel/channel.service";
import {ChannelType} from "../../../../../entities/ts/ChannelType";
import {Channel} from "../../../../../entities/ts/channels/AbstractChannel";
import {ChannelsAPI} from "../../../utils/channels";

@Component({
  tag: 'panic-installer-channels',
  styleUrl: 'panic-installer-channel.scss'
})
export class PanicInstallerChannel {

  /**
   * The configuration id being edited.
   */
  @Prop() configId: string;

  /**
   * Stencil Router object for page navigation.
   */
  @Prop() router: Router;

  /**
   * List of channel type objects.
   */
  @Prop() channelTypes: ChannelType[];

  /**
   * Config object being edited.
   */
  @State() config: Config;

  /**
   * The list of channel objects stored as a state.
   */
  @State() channels: Channel[] = [];

  /**
   * The filter applied to the channel data.
   */
  @State() currentFilter = "all";

  /**
   * Listens to an event for when the channel type selector is changed.
   * @param event The event sent by svc-event-emitter which wraps the channel type selector.
   */
  @Listen("filterChannel")
  filterChannelHandler(event: CustomEvent){
    this.currentFilter =  event.detail.filterChannel;
  }

  /**
   * Saves (adds/modifies) the channel in Mongo via API call.
   * @param channel The channel object in the form of a request body object to be saved.
   * @param id the channel identifier
   */
  async save(channel: Channel, id: string): Promise<Response>{
    const requestBody: Channel = ChannelsAPI.createChannelRequestBody(
        channel, id);
    return await ChannelService.getInstance().save(requestBody);
  }

  /**
   * Listens to save events from the channel form modal indicating channel creation/updates.
   * @param event The event sent by panic-installer-channel-form-modal.
   */
  @Listen("onSave", {target: 'window'})
  async onSaveHandler(event: CustomEvent) {
    const channel = event.detail.channelObject;
    const id = event.detail.id;

    const resp: Response = await this.save(channel, id);
    if(HelperAPI.isDuplicateName(resp)) {
      HelperAPI.raiseToast(
        `A channel named '${channel.name}' already exists!`,
        2000,
        "warning");
    } else {
      if(!id){
        await resp.json().then(async (resp) => {
          await ChannelService.getInstance().enableChannelOnConfig(resp.result, this.configId)
        });
      }
      await this.refreshAllChannels();
      HelperAPI.raiseToast("Channel created.");
      await dismissModal();
    }
  }

  /**
   * Listens to an event sent from the channels data table when a user clicks an edit button.
   * @param event The event sent by svc-data-table.
   */
  @Listen("channelsTableEdit", {target: "window"})
  async channelsTableEditHandler(event: CustomEvent) {
    const channelId = event.detail.id;
    const channel: Channel = await ChannelService.getInstance().getByID(channelId);

    createModal("panic-channel-form-modal", {
      channelTypes: this.channelTypes,
      channel: channel,
    },
    {
      backdropDismiss: false,
      cssClass: "panic-channel-form-modal__no-channel-type"
    });
  }

  /**
   * Listens to an event sent from the channels data table when a user clicks a delete button.
   * @param event The event sent by svc-data-table.
   */
  @Listen("channelsTableDelete", {target: "window"})
  async channelsTableDeleteHandler(event: CustomEvent) {
    const channelId = event.detail.id;
    const channel: Channel = await ChannelService.getInstance().getByID(channelId);

    await createAlert({
      header: "Attention",
      message: `Are you sure you want to delete the ${channel.type.name} channel: ${channel.name}?`,
      eventName: 'deleteChannel',
      eventData: {id: channel.id}
    });
  }

  /**
   * Listens to an event sent from the alert created in {@link channelsTableDeleteHandler}.
   * @param event The event sent by the delete channel alert.
   */
  @Listen("deleteChannel", {target: 'window'})
  async channelDeleteHandler(event: CustomEvent) {
    if (event.detail.confirmed) {
      const channelId = event.detail.data.id;
      await ChannelService.getInstance().delete(channelId);

      await this.refreshAllChannels();

      HelperAPI.raiseToast("Channel deleted.");
      await dismissModal();
    }
  }

  @Listen("previousStep", {target: "window"})
  previousStepHandler() {
    HelperAPI.changePage(
        this.router,
        `${HelperAPI.getUrlPrefix()}/sub-chain/${this.configId}`
    );
  }

  @Listen("nextStep", {target: "window"})
  async nextStepHandler() {
    HelperAPI.changePage(this.router, `${HelperAPI.getUrlPrefix()}/sources/${this.configId}`);
  }

  /**
   * Checks the list of channels whether at least 1 channel is enabled in the config
   * being edited.
   * @returns boolean
   */
  isAnyChannelEnabledForThisConfig(): boolean {
    return this.channels.some(channel =>
      HelperAPI.isConfigEnabledOnChannel(channel, this.configId))
  }

  /**
   * Toggles whether the channel is enabled for the config being edited.
   * @param channelId The id of the channel object to toggle
   * @param isEnabled whether the channel is enabled for the current config
   */
  async toggleChannelEnabledForThisConfig(channelId: string, isEnabled: boolean): Promise<void> {
    let toastMessage = "Channel {status} for this configuration.";
    if (isEnabled) {
      await ChannelService.getInstance().disableChannelOnConfig(channelId, this.configId)
      toastMessage = toastMessage.replace('{status}', 'disabled');
    } else {
      await ChannelService.getInstance().enableChannelOnConfig(channelId, this.configId)
      toastMessage = toastMessage.replace('{status}', 'enabled');
    }
    HelperAPI.raiseToast(toastMessage);
    await this.refreshAllChannels();
  }

  /**
   * Generates DataTableRowsType which is a set of rows to be displayed by the svc-data-table.
   * @returns DataTableRowsType
   */
  channelToDataTableRowsType(): DataTableRowsType{
    let channels: Channel[] = [...this.channels];

    if(this.currentFilter !== "all"){
      channels = this.channels.filter(channel => channel.type.value === this.currentFilter);
    }

    return channels.map(channel => {
      const configEnabled = HelperAPI.isConfigEnabledOnChannel(
        channel, this.configId);
      return {
        cells: [
          {
            value: channel.type.value,
            label: channel.type.name,
          },
          {
            value: channel.name,
            label: channel.name,
          },
          {
            value: configEnabled,
            label: <input
              type="checkbox"
              checked={configEnabled}
              onClick={async () => {
                await this.toggleChannelEnabledForThisConfig(
                  channel.id,
                  configEnabled
                )
              }
            }/>
          }
        ],
        id: channel.id
        }
    });
  }

  /**
   * Reloads the channels list via an API call.
   */
  async refreshAllChannels() {
    this.channels = await ChannelService.getInstance().getAll();
  }

  async componentWillLoad() {
    // might be necessary
    // i.e. when the node operator opens a modal and then clicks in the browser's back button
    dismissModal();

    this.config = await ConfigService.getInstance().getByID(this.configId);
    await this.refreshAllChannels();
  }

  render() {
    const subChain: string = this.config.subChain.name;
    return (
      <Host>
        <panic-header showMenu={false} />

        <svc-progress-bar value={0.2} color={"tertiary"}/>

        <svc-content-container class={"panic-installer-channels__container"}>
          <svc-surface>
            <div class={"panic-installer-channels__heading"}>
              <svc-icon name={"call-outline"} size={"120px"} color={"primary"} />
              <svc-label class={"panic-installer-channels__title"}>Channels Setup for {subChain}</svc-label>
              <svc-label class={"panic-installer-channels__step"}>step 2/5</svc-label>
            </div>

            <div class={"panic-installer-channels__text-with-tooltip"}>
              <p>
                {MAIN_TEXT}
              </p>
              <svc-buttons-container>
                <svc-button color={"secondary"} iconName={"information-circle"} iconPosition={"icon-only"} onClick={() => {
                  createModal("panic-installer-more-info-modal", {
                    messages: MORE_INFO_MESSAGES,
                    class: "channels",
                  })
                }}/>
              </svc-buttons-container>
            </div>

            <p>
              {getSecondaryText(subChain)}
            </p>

            <div class={"panic-installer-channels__add-channel-button"}>
              <svc-button id={"add"} iconName={"add-circle"} color={"secondary"} onClick={() => {
                createModal("panic-channel-form-modal",
                  {
                    channelTypes: this.channelTypes,
                  },
                  {
                    backdropDismiss: false,
                    cssClass: "panic-channel-form-modal__no-channel-type"
                });
              }}>
                Add Channel
              </svc-button>
            </div>

            <div class={"panic-installer-channels__filter-container"}>

              {
                this.channels.length != 0 &&
                <svc-event-emitter eventName="filterChannel">
                  <svc-select
                    name={"filterChannel"}
                    options={CHANNEL_FILTERS}
                    header={"Channel Type"}
                    placeholder={"Filter by channel types..."}
                    withBorder={true}
                  />
                </svc-event-emitter>
              }
              <svc-data-table
                class={"panic-installer-channels__crud-data-table"}
                mode={"crud"}
                cols={CHANNEL_TABLE_HEADERS}
                noRecordsMessage={this.currentFilter === "all" ?
                    "No channel configurations added to PANIC..." :
                    `PANIC won't be able to alert you via ${this.currentFilter} if you don't add any ${this.currentFilter} channels`}
                rows={this.channelToDataTableRowsType()}
                editEventName={"channelsTableEdit"}
                deleteEventName={"channelsTableDelete"}
              />
            </div>

            {
              !this.isAnyChannelEnabledForThisConfig() &&
              <p id={"no-channel-associated"}>
                PANIC will be unable to alert you if no channels are enabled for this configuration. However, alerts will still be made available in the alerter docker logs.
              </p>
            }
          </svc-surface>

          <panic-installer-nav config={this.config} />

        </svc-content-container>

        <panic-footer />
      </Host>
    );
  }

}

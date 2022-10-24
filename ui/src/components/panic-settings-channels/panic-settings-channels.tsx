import {
  Component,
  h,
  Host,
  Listen, Prop,
  State
} from '@stencil/core';
import {
  PanicSettingsChannelsCrud
} from "./panic-settings-channels-crud/panic-settings-channels-crud";
import {createAlert, createModal, dismissModal} from "@simply-vc/uikit";
import {
  PanicSettingsChannelsMap
} from "./panic-settings-channels-map/panic-settings-channels-map";
import {Channel} from "../../../../entities/ts/channels/AbstractChannel";
import {Config} from "../../../../entities/ts/Config";
import {ChannelType} from "../../../../entities/ts/ChannelType";
import {ConfigService} from "../../services/config/config.service";
import {ChannelService} from "../../services/channel/channel.service";
import {HelperAPI} from "../../utils/helpers";
import {ChannelsAPI} from "../../utils/channels";

@Component({
  tag: 'panic-settings-channels',
  styleUrl: 'panic-settings-channels.scss'
})
export class PanicSettingsChannels {

  /**
   * List of channel type objects.
   */
  @Prop() channelTypes: ChannelType[];

  /**
   * Stores the channels as a local state.
   */
  @State() channels: Channel[] = [];

  /**
   * Stores the configurations as a local state.
   */
  @State() configs: Config[] = [];

  /**
   * Stores the filter type ID as a local state.
   */
  @State() channelTypeFilterId: string = "all";

  /**
   * Stores the filtered channels by type as a local state.
   */
  @State() filteredChannelsByType: Channel[] = [];

  /**
   * Stores the id of the selected channel.
   */
  @State() channelIdInFocus: string;

  /**
   * Fetch the list of configurations from Mongo via API call.
   * @returns array of configs
   */
  async fetchConfigs(): Promise<Array<Config>> {
    return await ConfigService.getInstance().getAll();
  }

  /**
   * Fetch the list of channels from Mongo via API call.
   * @returns array of channels
   */
  async fetchChannels(): Promise<Array<Channel>> {
    return await ChannelService.getInstance().getAll();
  }

  /**
   * Filters the list of channels by channel type
   */
  filterChannelsByType() {
    this.filteredChannelsByType = this.channelTypeFilterId === 'all'
        ? this.channels
        : this.channels.filter(
            channel => channel.type.id === this.channelTypeFilterId);
  }

  /**
   * Get the list of channels and configs, and perform channel filtering by
   * type.
   */
  async updateAndFilterChannelsAndConfigsLists(): Promise<void> {
    this.channels = await this.fetchChannels();
    this.filterChannelsByType();
    this.configs = await this.fetchConfigs();
  }

  async componentWillLoad(): Promise<void> {
    await this.updateAndFilterChannelsAndConfigsLists()
  }

  /**
   * Add or update the channel via an API call
   * @param channelData the channel data to be added/updated.
   * @param id The channel identifier
   */
  async saveChannel(channelData: Channel, id: string): Promise<void> {
    const requestBody: Channel = ChannelsAPI.createChannelRequestBody(
        channelData, id);
    const response = await ChannelService.getInstance().save(requestBody)

    // Perform some error handling on response and if the operation was
    // successful close the modal and update the list of channels
    if(HelperAPI.isDuplicateName(response)) {
      HelperAPI.raiseToast(
          `A channel named '${channelData.name}' already exists!`, 3000,
          "warning");
    } else if (!response.ok) {
      HelperAPI.raiseToast(`Error saving channel`, 3000, "danger");
    } else {
      await this.updateAndFilterChannelsAndConfigsLists();
      await dismissModal();
    }
  }

  /**
   * Delete the channel from Mongo via an API call.
   * @param channel the data of the channel to be removed from Mongo.
   */
  async deleteChannel(channel: Channel): Promise<void>{
    const success = await ChannelService.getInstance().delete(channel.id)
    // We want to execute this logic only if the deletion call is successful.
    // Otherwise, we will raise a feedback message
    const toastMsg = "Error deleting channel.";
    const callback = async function () {
      await this.updateAndFilterChannelsAndConfigsLists();
    }.bind(this);
    await HelperAPI.executeWithFailureFeedback(
        success, callback, toastMsg, 3000, "danger")
  }

  /**
   * Determine whether the enable event is truthy.
   * @param event a key-value containing the channel id and config id and
   * whether the value is enabled.
   * @returns boolean whether the event is enabled.
   */
  isEnableEvent(event: Record<string, string>): boolean{
    return Object.values(event)[0] === 'true';
  }

  /**
   * Get the config and channel ids from the event data (config or channel)
   * @param event a key-value containing the config and channel ids and
   * whether the value is enabled.
   * @returns array of two string values, representing the config and channel id
   */
  getConfigAndChannelId(event: Record<string, string>): string[]{
    let configAndChannelIds: string =  Object.keys(event)[0];
    return configAndChannelIds.split(' ')
  }

  /**
   * Handling the enable event from map component.
   * @param event a key-value containing the config id and whether the value is
   * enabled.
   */
  @Listen("onEnableMap", {target: "window"})
  async enableEventMapHandler(event: CustomEvent) {
    const configChannelIdAndIsEnabledPair = event.detail;
    const [configId, channelId] = this.getConfigAndChannelId(
        configChannelIdAndIsEnabledPair);
    const isEnabled = this.isEnableEvent(configChannelIdAndIsEnabledPair);

    let success = isEnabled
        ? await ChannelService.getInstance().enableChannelOnConfig(channelId,
            configId)
        : await ChannelService.getInstance().disableChannelOnConfig(channelId,
            configId)
    // We want to do nothing if the call above is successful. Otherwise, we will
    // raise a feedback message
    const toastMsg = isEnabled
        ? "Channel could not be enabled"
        : "Channel could not be disabled";
    const callback = () => {};
    await HelperAPI.executeWithFailureFeedback(
        success, callback, toastMsg, 3000, "danger")

    // We want to get the list of configurations after updating them, even if
    // enabling/disabling fails because we need the old data.
    await this.updateAndFilterChannelsAndConfigsLists();
  }

  /**
   * Handling on save events from the CRUD component.
   * @param event data derived from the event.
   */
  @Listen("onSave", {target: "window"})
  async onSaveEventHandler(event: CustomEvent) {
    const id = event.detail.id;
    const channelData = event.detail.channelObject;
    await this.saveChannel(channelData, id);
  }

  /**
   * Obtain channel data through the id.
   * @param channelId the channel id.
   */
  getChannelDataById(channelId: string): Channel {
    return this.filteredChannelsByType.find(
        channel => channel.id === channelId);
  }

  /**
   * Handling edit events from the channels data table.
   * @param event data derived from the event.
   */
  @Listen("onChannelsTableEdit", {target: "window"})
  async onChannelsTableEditHandler(event: CustomEvent) {
    let channelData: Channel = this.getChannelDataById(event.detail.id);

    await createModal(
        "panic-channel-form-modal",
        {
          channel: channelData, channelTypes: this.channelTypes
        },
        {
          backdropDismiss: false,
          cssClass: "panic-channel-form-modal__no-channel-type"
        }
    );
  }

  /**
   * Handling delete events from the channels data table.
   * @param event data derived from the event.
   */
  @Listen("onChannelsTableDelete", {target: "window"})
  async onChannelsTableDeleteHandler(event: CustomEvent) {
    let channelData: Channel = this.getChannelDataById(event.detail.id);

    await createAlert({
      'header': 'Delete Confirmation',
      'message': `Are you sure you want to delete the configuration for ${
        channelData.name} ?`,
      'eventName': 'channelDeleteConfirmation',
      'eventData': channelData
    })
  }

  /**
   * Handling delete confirmation events from the delete modal.
   * @param event data derived from the event.
   */
  @Listen('channelDeleteConfirmation', {target: 'window'})
  async handleChannelDeleteConfirmation(event: CustomEvent) {
    const deletionConfirmed = event.detail.confirmed;
    if(deletionConfirmed){
      const channel = event.detail.data;
      await this.deleteChannel(channel);
    }
  }

  /**
   * Handling on channel type change events from the CRUD component.
   * @param event data containing the type of filter to be applied to the data.
   */
  @Listen("onChannelTypeChange", {target: "window"})
  async onChannelTypeChangeHandler(event: CustomEvent) {
    this.channelTypeFilterId = event.detail.channelType;
    await this.filterChannelsByType();
  }

  /**
   * Handling on channel name change events from the CRUD component.
   * @param event data containing the filter name to be applied to the data.
   */
  @Listen("onChannelNameChange", {target: "window"})
  onChannelNameChangeHandler(event: CustomEvent) {
    let selectedChannel: Channel = this.channels.filter(
        channel => channel.name === event.detail.channelName)[0];
    this.channelIdInFocus = selectedChannel.id;
  }

  render() {
    return (
      <Host>
        <panic-header showMenu={true}/>

        <svc-content-container class={"panic-settings-channels__container"}>
          <PanicSettingsChannelsCrud
            channels={this.channels}
            channelTypeFilterId={this.channelTypeFilterId}
            channelTypes={this.channelTypes}
            filteredChannels={this.filteredChannelsByType}/>

          <PanicSettingsChannelsMap
            channels={this.channels}
            configs={this.configs}
            channelId={this.channelIdInFocus}
          />
        </svc-content-container>

        <panic-footer/>

      </Host>
    );
  }
}
import {FunctionalComponent, h} from "@stencil/core";
import {SUBCHAIN_CHANNEL_MAP_TABLE_HEADERS} from "../../../utils/constants";
import {SelectOptionType} from "@simply-vc/uikit/dist/types/types/select";
import {DataTableRowsType} from "@simply-vc/uikit/dist/types/types/datatable";
import {Channel} from "../../../../../entities/ts/channels/AbstractChannel";
import {Config} from "../../../../../entities/ts/Config";
import {HelperAPI} from "../../../utils/helpers";

interface PanicSettingsChannelsMapProps {
  channels: Channel[],
  channelId: string,
  configs: Config[],
}

/**
 * Render the config data into a format legible by the data table. Note that in
 * this function we are assuming that a record represents a configuration, but
 * to the user a configuration <=> SubChain
 * @param configs a list of configuration objects to be rendered
 * @param channelId the id of the currently selected channel
 * @param channels the list of channels
 * @returns populated `DataTableRowsType` object which is read by the data
 * table.
 */
function configToDataTableRow(configs: Config[], channelId: string,
                              channels: Channel[]): DataTableRowsType {
  const channel = channels.filter(channel => channelId == channel.id)[0];
  return configs.map((config) => {
      const configEnabled = HelperAPI.isConfigEnabledOnChannel(channel, config.id);
      return {
        cells: [
          {
            value: config.subChain.name,
            label: config.subChain.name,
          },
          {
            value: configEnabled,
            label:
              <svc-event-emitter eventName={"onEnableMap"}>
                <panic-installer-form-checkbox
                  name={`${config.id} ${channelId}`}
                  checked={configEnabled}
                />
              </svc-event-emitter>
          },
        ],
        id: config.id
      };
    }
  );
}

/**
 * Generates a list of names to be rendered by the channel name filter.
 * @param channels a list of channel objects to be rendered
 * @returns SelectOptionType object
 */
function generateChannelNameFilters(channels: Channel[]): SelectOptionType {
  return channels.map(channel => {
    return {
      label: channel.name,
      value: channel.name,
    }
  })
}

export const PanicSettingsChannelsMap:
    FunctionalComponent<PanicSettingsChannelsMapProps> = (
        {channels, configs, channelId}
) => {
  return (
    <svc-surface>
      <svc-label class={"panic-settings-channels-crud__title"}>
          Channels - Sub-chain Map
      </svc-label>

      <p>
          Choose which chains you want to be alerted on the selected channel.
          You can tick or untick to enable or disable respectively.
      </p>

      <div class={"panic-settings-channels-crud__filter-container"}>
        {
          channels.length !== 0 &&
            <svc-event-emitter
                class={"panic-settings-channels-crud__filter"}
                eventName="onChannelNameChange"
            >
              <svc-select
                name={"channelName"}
                options={generateChannelNameFilters(channels)}
                header={"Channel Name"}
                placeholder={"Choose the channel..."}
                withBorder={true}
              />
            </svc-event-emitter>
        }

        <svc-data-table
          cols={SUBCHAIN_CHANNEL_MAP_TABLE_HEADERS}
          class={"panic-settings-channels-map__crud-data-table"}
          noRecordsMessage={
            channels.length != 0
                ? "Choose a channel to see sub-chains associated with it..."
                : "No channels added yet."}
          rows={channelId && configToDataTableRow(configs, channelId, channels)}
          editEventName={"onChannelsTableEdit"}
          deleteEventName={"onChannelsTableDelete"}
        />
      </div>

    </svc-surface>
  )
}

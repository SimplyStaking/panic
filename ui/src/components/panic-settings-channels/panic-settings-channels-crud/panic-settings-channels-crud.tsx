import {
  FunctionalComponent,
  h
} from "@stencil/core";
import {DataTableRowsType} from "@simply-vc/uikit/dist/types/types/datatable";
import {CHANNEL_TABLE_HEADERS} from "../../../utils/constants";
import {createModal} from "@simply-vc/uikit";
import {Channel} from "../../../../../entities/ts/channels/AbstractChannel";
import {ChannelType} from "../../../../../entities/ts/ChannelType";

interface PanicSettingsChannelsCrudProps {
  channels: Channel[],
  channelTypeFilterId: string,
  channelTypes: ChannelType[],
  filteredChannels: Channel[],
}

/**
 * Render the channel data into a format legible by the data table.
 * @param channels a list of channel objects to be rendered
 * @returns populated `DataTableRowsType` object which is read by the data
 * table.
 */
function channelToDataTableRow(channels: Channel[]): DataTableRowsType{
  return channels.map(channel => ({
    cells: [
      {
        value: channel.type.name,
        label: channel.type.name,
      },
      {
        value: channel.name,
        label: channel.name,
      },
    ],
    id: channel.id
  }));
}

/**
 * This function generates the channel type options for the CRUD
 * @param channelTypes The channel types given by the API
 */
function generateChannelTypeFilters(channelTypes: ChannelType[]) {
  const generatedChannelTypes = channelTypes.map(
      (channelType) => {return {label: channelType.name, value: channelType.id}}
  );

  generatedChannelTypes.push({label: "All", value: "all"});

  return generatedChannelTypes;
}

export const PanicSettingsChannelsCrud:
    FunctionalComponent<PanicSettingsChannelsCrudProps> = (
        {channels, channelTypeFilterId, channelTypes, filteredChannels}
) => {
  const channelTypeFilter = channelTypes.find(
      // Keep in mind that channelTypeFilter can be undefined if
      // channelTypeFilterId = "all"
      (channelType) => channelType.id == channelTypeFilterId
  );
  return (
    <svc-surface>
      <svc-label class={"panic-settings-channels-crud__title"}>
        Channels
      </svc-label>

      <div class={"panic-settings-channels-crud__add-channel-button"}>
        <svc-button
            id={"add"}
            iconName={"add-circle"}
            color={"secondary"}
            onClick={async () => {
              await createModal(
                  "panic-channel-form-modal",
                  {
                    channelTypes: channelTypes
                  },
                  {
                    backdropDismiss: false,
                    cssClass: "panic-channel-form-modal__no-channel-type"
                  }
              );
            }}
        >
          Add Channel
        </svc-button>
      </div>

      <div class={"panic-settings-channels-crud__filter-container"}>
        {
          channels.length !== 0 &&
            <svc-event-emitter
                class={"panic-settings-channels-crud__filter"}
                eventName="onChannelTypeChange"
            >
              <svc-select
                name={"channelType"}
                options={generateChannelTypeFilters(channelTypes)}
                header={"Channel Type"}
                placeholder={"Filter by channel types..."}
                withBorder={true}
              />
            </svc-event-emitter>
        }

        <svc-data-table
          mode={"crud"}
          class={"panic-settings-channels-crud__crud-data-table"}
          cols={CHANNEL_TABLE_HEADERS}
          noRecordsMessage={channels.length !== 0 && channelTypeFilter
            ? `No configured ${channelTypeFilter.name} channels.`
            : "No channels added yet."}
          rows={channelToDataTableRow(filteredChannels)}
          editEventName={"onChannelsTableEdit"}
          deleteEventName={"onChannelsTableDelete"}
        />
      </div>

    </svc-surface>
  )
}

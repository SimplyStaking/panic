import {createInfoAlert, dismissModal, parseForm} from '@simply-vc/uikit';
import {FormFieldInterface} from '@simply-vc/uikit/dist/types/utils/forms/form-field.interface';
import {Component, h, State, Prop, Listen} from '@stencil/core';
import {HelperAPI} from "../../../utils/helpers";
import {ChannelType} from "../../../../../entities/ts/ChannelType";
import {SlackChannel} from "../../../../../entities/ts/channels/SlackChannel";
import {TwilioChannel} from "../../../../../entities/ts/channels/TwilioChannel";
import {TelegramChannel} from "../../../../../entities/ts/channels/TelegramChannel";
import {PagerDutyChannel} from "../../../../../entities/ts/channels/PagerDutyChannel";
import {OpsgenieChannel} from "../../../../../entities/ts/channels/OpsgenieChannel";
import {EmailChannel} from "../../../../../entities/ts/channels/EmailChannel";
import {Channel} from "../../../../../entities/ts/channels/AbstractChannel";

@Component({
  tag: 'panic-channel-form-modal',
  styleUrl: 'panic-channel-form-modal.scss'
})
export class PanicChannelFormModal {

  /**
   * List of ChannelType objects.
   */
  @Prop() channelTypes: ChannelType[];

  /**
   * The channel object, passed should the form be in edit mode.
   */
  @Prop() channel;

  /**
   * Indicating whether the form is allowed to be submitted.
   */
  @State() allowSubmit: boolean;

  /**
   * The currently selected ChannelType.
   */
  @State() selectedChannelType: ChannelType;

  /**
   * Object containing each channel type along with all their respective
   * fields, including all component prop data and additional data.
   */
  @State() groups = {
    telegram: {
      fields: [
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "name",
            placeholder: "telegram_chat_1",
            label: "Channel Name",
            lines: "full",
            required: true,
            onInput: (event) => this.updateTelegramIdentifier(event.target.value)
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "botToken",
            placeholder: "123456789:ABCDEF-123qwertasdfzxcv",
            label: "Bot Token",
            lines: "full",
            required: true,
            onInput: (event) => this.updateTelegramBotToken(event.target.value)
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "chatId",
            placeholder: "-11223321",
            label: "Chat ID",
            lines: "full",
            type: "number",
            required: true,
            onInput: (event) => this.updateTelegramBotChatId(event.target.value)
          }
        },
        {
          componentTagName: "svc-checkbox",
          componentProps: {
            name: "commands",
            helpText: "This will enable commands to be sent from Telegram to PANIC",
            checked: true,
            label: "Telegram Commands",
            value: true,
            lines: "full"
          }
        },
        {
          componentTagName: "svc-checkbox",
          componentProps: {
            name: "alerts",
            helpText: "This will enable alerts to be sent from PANIC to Telegram",
            checked: true,
            label: "Telegram Alerts",
            value: true,
            lines: "full"
          }
        },
        {
          componentTagName: "panic-installer-test-button",
          componentProps: {
            service: 'telegram',
            pingProperties: {'botToken': '', 'botChatId': ''},
            identifier: ''
          }
        }
      ]
    },
    slack: {
      fields: [
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "name",
            placeholder: "slack_channel_1",
            lines: "full",
            required: true,
            label: "Channel Name",
            onInput: (event) => this.updateSlackIdentifier(event.target.value)
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "appToken",
            placeholder: "xapp-Y-XXXXXXXXXXXX-TTTTTTTTTTTTT-LLLLLLLLLLLLL",
            lines: "full",
            label: "App-Level Token",
            required: true
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "botToken",
            placeholder: "xoxb-XXXXXXXXXXXX-TTTTTTTTTTTTTT",
            lines: "full",
            label: "Bot Token",
            required: true,
            onInput: (event) => this.updateSlackBotToken(event.target.value)
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "botChannelId",
            placeholder: "ABC123DEF456",
            lines: "full",
            label: "Bot Channel ID",
            required: true,
            onInput: (event) => this.updateSlackBotChannelId(event.target.value)
          }
        },
        {
          componentTagName: "svc-checkbox",
          componentProps: {
            name: "commands",
            helpText: "This will enable commands to be sent from Slack to PANIC",
            checked: true,
            label: "Slack Commands",
            value: true,
            lines: "full",
          }
        },
        {
          componentTagName: "svc-checkbox",
          componentProps: {
            name: "alerts",
            helpText: "This will enable alerts to be sent from PANIC to Slack",
            checked: true,
            label: "Slack Alerts",
            value: true,
            lines: "full"
          }
        },
        {
          componentTagName: "panic-installer-test-button",
          componentProps: {
            service: 'slack',
            pingProperties: {'botToken': '', 'botChannelId': ''},
            identifier: ''
          }
        }
      ]
    },
    email: {
      fields: [
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "name",
            placeholder: "email_channel_1",
            lines: "full",
            required: true,
            label: "Channel Name"
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "smtp",
            id: "smtp",
            placeholder: "my.smtp.com",
            lines: "full",
            label: "SMTP",
            required: true,
            onInput: (event) => this.updateEmailSmtp(event.target.value)
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "port",
            id: "port",
            placeholder: "0",
            lines: "full",
            label: "Port",
            type: "number",
            required: true,
            onInput: (event) => this.updateEmailPort(event.target.value)
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "emailFrom",
            id: "emailFrom",
            placeholder: "alerter@email.com",
            lines: "full",
            label: "Email From",
            type: "email",
            required: true,
            onInput: (event) => this.updateEmailFrom(event.target.value)
          }
        },
        {
          componentTagName: "svc-multiple-input",
          componentProps: {
            name: "emailsTo",
            id: "emailsTo",
            label: "Emails To",
            placeholder: "alerter@email.com [Press Enter after each Email].",
            type: "email",
            outline: true,
            required: true,
            addEventName: "AddedEmailTo",
            removeEventName: "RemovedEmailTo"
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "username",
            id: "username",
            placeholder: "my_username",
            lines: "full",
            label: "Username",
            required: true,
            onInput: (event) => this.updateEmailUsername(event.target.value)
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "password",
            id: "password",
            placeholder: "********",
            lines: "full",
            label: "Password",
            type: "password",
            required: true,
            onInput: (event) => this.updateEmailPassword(event.target.value)
          }
        },
        {
          componentTagName: "panic-installer-test-button-multiple-sources",
          componentProps: {
            service: "email",
            pingProperties: []
          }
        }
      ]
    },
    opsgenie: {
      fields: [
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "name",
            placeholder: "opsgenie_channel_1",
            lines: "full",
            label: "Channel Name",
            required: true,
            onInput: (event) => this.updateOpsgenieIdentifier(event.target.value)
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "apiToken",
            placeholder: "api_token",
            lines: "full",
            label: "API Token",
            required: true,
            onInput: (event) => this.updateOpsgenieAPIToken(event.target.value)
          }
        },
        {
          componentTagName: "svc-checkbox",
          componentProps: {
            name: "eu",
            helpText: "If you are operating OpsGenie in the EU region please have this ticked.",
            checked: false,
            label: "European Region",
            value: true,
            lines: "full",
            onClick: (event) => this.updateOpsgenieEU(event.target.checked)
          }
        },
        {
          componentTagName: "panic-installer-test-button",
          componentProps: {
            service: 'opsgenie',
            pingProperties: {'apiKey': '', 'eu': false},
            identifier: ''
          }
        }
      ]
    },
    pagerduty: {
      fields: [
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "name",
            placeholder: "pagerduty_channel_1",
            lines: "full",
            required: true,
            label: "Channel Name",
            onInput: (event) => this.updatePagerDutyIdentifier(event.target.value)
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "integrationKey",
            placeholder: "integration_key",
            lines: "full",
            label: "Integration Key",
            required: true,
            onInput: (event) => this.updatePagerDutyIntegrationKey(event.target.value)
          }
        },
        {
          componentTagName: "panic-installer-test-button",
          componentProps: {
            service: 'pagerduty',
            pingProperties: {'integrationKey': ''},
            identifier: ''
          }
        }
      ]
    },
    twilio: {
      fields: [
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "name",
            placeholder: "twilio_channel_1",
            lines: "full",
            required: true,
            label: "Channel Name"
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "accountSid",
            id: 'accountSid',
            placeholder: "accountSid",
            lines: "full",
            label: "Account SID",
            required: true,
            onInput: (event) => this.updateTwilioAccountSid(event.target.value)
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "authToken",
            id: 'authToken',
            placeholder: "authenticationToken",
            lines: "full",
            label: "Authentication Token",
            required: true,
            onInput: (event) => this.updateTwilioAuthToken(event.target.value)
          }
        },
        {
          componentTagName: "svc-input",
          componentProps: {
            name: "twilioPhoneNumber",
            id: 'twilioPhoneNumber',
            placeholder: "twilioPhoneNumber",
            lines: "full",
            type: "tel",
            label: "Twilio Phone Number",
            required: true,
            onInput: (event) => this.updateTwilioPhoneNumber(event.target.value)
          }
        },
        {
          componentTagName: "svc-multiple-input",
          componentProps: {
            name: "twilioPhoneNumbersToDial",
            label: "Phone numbers for Twilio to dial",
            placeholder: "Add Phone Numbers [Press Enter after each Number]",
            outline: true,
            type: "tel",
            required: true,
            addEventName: "AddedTwilioPhoneNumberToDial",
            removeEventName: "RemovedTwilioPhoneNumberToDial"
          }
        },
        {
          componentTagName: "panic-installer-test-button-multiple-sources",
          componentProps: {
            service: "twilio",
            pingProperties: []
          }
        }
      ]
    },
  };

  updateTelegramBotToken(bot_token: string): void{
    this.groups.telegram.fields[5].componentProps.pingProperties.botToken = bot_token;
    this.groups = {
      ...this.groups
    }
  }

  updateTelegramBotChatId(bot_chat_id: string): void{
    this.groups.telegram.fields[5].componentProps.pingProperties.botChatId = bot_chat_id;
    this.groups = {
      ...this.groups
    }
  }

  updateTelegramIdentifier(identifier: string): void{
    this.groups.telegram.fields[5].componentProps.identifier = identifier;
    this.groups = {
      ...this.groups
    }
  }

  updateSlackBotToken(bot_token: string): void{
    this.groups.slack.fields[6].componentProps.pingProperties.botToken = bot_token;
    this.groups = {
      ...this.groups
    }
  }

  updateSlackBotChannelId(bot_channel_id: string): void{
    this.groups.slack.fields[6].componentProps.pingProperties.botChannelId = bot_channel_id;
    this.groups = {
      ...this.groups
    }
  }

  updateSlackIdentifier(identifier: string): void{
    this.groups.slack.fields[6].componentProps.identifier = identifier;
    this.groups = {
      ...this.groups
    }
  }

  updateOpsgenieAPIToken(api_token: string): void{
    this.groups.opsgenie.fields[3].componentProps.pingProperties.apiKey = api_token;
    this.groups = {
      ...this.groups
    }
  }

  updateOpsgenieEU(eu: boolean): void{
    this.groups.opsgenie.fields[3].componentProps.pingProperties.eu = eu;
    this.groups = {
      ...this.groups
    }
  }

  updateOpsgenieIdentifier(identifier: string): void{
    this.groups.opsgenie.fields[3].componentProps.identifier = identifier;
    this.groups = {
      ...this.groups
    }
  }

  updatePagerDutyIdentifier(identifier: string): void{
    this.groups.pagerduty.fields[2].componentProps.identifier = identifier;
    this.groups = {
      ...this.groups
    }
  }

  updatePagerDutyIntegrationKey(integration_key: string): void{
    this.groups.pagerduty.fields[2].componentProps.pingProperties.integrationKey = integration_key;
    this.groups = {
      ...this.groups
    }
  }

  updateTwilioAccountSid(account_sid: string): void{
    let pingProperties = this.groups.twilio.fields[5].componentProps.pingProperties;
    this.groups.twilio.fields[5].componentProps.pingProperties = pingProperties.map((properties) => ({
      ...properties,
      accountSid: account_sid
    }));
    this.groups = {
      ...this.groups
    }
  }

  updateTwilioAuthToken(auth_token: string): void{
    let pingProperties = this.groups.twilio.fields[5].componentProps.pingProperties;
    this.groups.twilio.fields[5].componentProps.pingProperties = pingProperties.map((properties) => ({
      ...properties,
      authToken: auth_token
    }));
    this.groups = {
      ...this.groups
    }
  }

  updateTwilioPhoneNumber(twilio_phone_number: string): void{
    let pingProperties = this.groups.twilio.fields[5].componentProps.pingProperties;
    this.groups.twilio.fields[5].componentProps.pingProperties = pingProperties.map((properties) => ({
      ...properties,
      twilioPhoneNumber: twilio_phone_number
    }));
    this.groups = {
      ...this.groups
    }
  }

  @Listen("AddedTwilioPhoneNumberToDial", {target: "window"})
  addTwilioPhoneNumberToDial(event: CustomEvent): void{
    const phone_number_to_dial = event.detail.value;
    this.groups.twilio.fields[5].componentProps.pingProperties.push({
      //@ts-ignore
      accountSid: document.getElementById("accountSid").children[0].children[1].value,
      //@ts-ignore
      authToken: document.getElementById("authToken").children[0].children[1].value,
      //@ts-ignore
      twilioPhoneNumber: document.getElementById("twilioPhoneNumber").children[0].children[1].value,
      phoneNumberToDial: phone_number_to_dial
    });
    this.groups = {
      ...this.groups
    }
  }

  @Listen("RemovedTwilioPhoneNumberToDial", {target: "window"})
  removeTwilioPhoneNumberToDial(event: CustomEvent): void{
    const phone_number_to_dial = event.detail.value;
    let pingProperties = this.groups.twilio.fields[5].componentProps.pingProperties;
    this.groups.twilio.fields[5].componentProps.pingProperties = pingProperties.filter((properties) => {
      return properties.phoneNumberToDial !== phone_number_to_dial
    });
    this.groups = {
      ...this.groups
    }
  }

  updateEmailSmtp(smtp: string): void{
    let pingProperties = this.groups.email.fields[7].componentProps.pingProperties;
    this.groups.email.fields[7].componentProps.pingProperties = pingProperties.map((properties) => ({
      ...properties,
      smtp: smtp
    }));
    this.groups = {
      ...this.groups
    }
  }

  updateEmailPort(port: string): void{
    let pingProperties = this.groups.email.fields[7].componentProps.pingProperties;
    this.groups.email.fields[7].componentProps.pingProperties = pingProperties.map((properties) => ({
      ...properties,
      port: parseInt(port)
    }));
    this.groups = {
      ...this.groups
    }
  }

  updateEmailFrom(email_from: string): void{
    let pingProperties = this.groups.email.fields[7].componentProps.pingProperties;
    this.groups.email.fields[7].componentProps.pingProperties = pingProperties.map((properties) => ({
      ...properties,
      from: email_from
    }));
    this.groups = {
      ...this.groups
    }
  }

  updateEmailUsername(username: string): void{
    let pingProperties = this.groups.email.fields[7].componentProps.pingProperties;
    this.groups.email.fields[7].componentProps.pingProperties = pingProperties.map((properties) => ({
      ...properties,
      username: username
    }));
    this.groups = {
      ...this.groups
    }
  }

  updateEmailPassword(password: string): void{
    let pingProperties = this.groups.email.fields[7].componentProps.pingProperties;
    this.groups.email.fields[7].componentProps.pingProperties = pingProperties.map((properties) => ({
      ...properties,
      password: password
    }));
    this.groups = {
      ...this.groups
    }
  }

  @Listen("AddedEmailTo", {target: "window"})
  addEmailTo(event: CustomEvent): void{
    const email_to = event.detail.value;
    this.groups.email.fields[7].componentProps.pingProperties.push({
      //@ts-ignore
      smtp: document.getElementById("smtp").children[0].children[1].value,
      //@ts-ignore
      port: document.getElementById("port").children[0].children[1].value,
      //@ts-ignore
      from: document.getElementById("emailFrom").children[0].children[1].value,
      //@ts-ignore
      username: document.getElementById("username").children[0].children[1].value,
      //@ts-ignore
      password: document.getElementById("password").children[0].children[1].value,
      to: email_to
    });
    this.groups = {
      ...this.groups
    }
  }

  @Listen("RemovedEmailTo", {target: "window"})
  removeEmailTo(event: CustomEvent): void{
    const email_to = event.detail.value;
    let pingProperties = this.groups.email.fields[7].componentProps.pingProperties;
    this.groups.email.fields[7].componentProps.pingProperties = pingProperties.filter((properties) => {
      return properties.to !== email_to
    });
    this.groups = {
      ...this.groups
    }
  }

  createArrayFromKeySubstring(channelFormData: any, substring: string): Array<string>{
    return Object.keys(channelFormData).filter(
      key => key.includes(substring)).map(
        key => channelFormData[key]);
  }

  /**
   * Parsing the form data into a channel object based on its channel type.
   * @param channelFormData Object containing data from the form
   * @returns Channel
   */
  createChannelAndSetProperties(channelFormData: any): Channel {
    let channel: Channel;

    const channelType: ChannelType = this.getChannelTypeById(channelFormData.type);
    switch (channelType.value){
      case "slack":
        channel = new SlackChannel();
        channel.name = channelFormData.name;
        channel.appToken = channelFormData.appToken;
        channel.botToken = channelFormData.botToken;
        channel.botChannelId = channelFormData.botChannelId;
        channel.commands = channelFormData.commands === 'true';
        channel.alerts = channelFormData.alerts === 'true';
        channel.info = channelFormData.info === 'true';
        channel.warning = channelFormData.warning === 'true';
        channel.critical = channelFormData.critical === 'true';
        channel.error = channelFormData.error === 'true';
        break;
      case "twilio":
        channel = new TwilioChannel();
        channel.name = channelFormData.name;
        channel.accountSid = channelFormData.accountSid;
        channel.authToken = channelFormData.authToken;
        channel.twilioPhoneNumber = channelFormData.twilioPhoneNumber;
        channel.twilioPhoneNumbersToDial = this.createArrayFromKeySubstring(
          channelFormData, 'twilioPhoneNumbersToDial');
        channel.critical = channelFormData.critical === 'true';
        break;
      case "telegram":
        channel = new TelegramChannel();
        channel.name = channelFormData.name;
        channel.botToken = channelFormData.botToken;
        channel.chatId = channelFormData.chatId;
        channel.commands = channelFormData.commands === 'true';
        channel.alerts = channelFormData.alerts === 'true';
        channel.info = channelFormData.info === 'true';
        channel.warning = channelFormData.warning === 'true';
        channel.critical = channelFormData.critical === 'true';
        channel.error = channelFormData.error === 'true';
        break;
      case "pagerduty":
        channel = new PagerDutyChannel();
        channel.name = channelFormData.name;
        channel.integrationKey = channelFormData.integrationKey;
        channel.info = channelFormData.info === 'true';
        channel.warning = channelFormData.warning === 'true';
        channel.critical = channelFormData.critical === 'true';
        channel.error = channelFormData.error === 'true';
        break;
      case "opsgenie":
        channel = new OpsgenieChannel();
        channel.name = channelFormData.name;
        channel.apiToken = channelFormData.apiToken;
        channel.eu = channelFormData.eu === 'true';
        channel.info = channelFormData.info === 'true';
        channel.warning = channelFormData.warning === 'true';
        channel.critical = channelFormData.critical === 'true';
        channel.error = channelFormData.error === 'true';
        break;
      case "email":
        channel = new EmailChannel();
        channel.name = channelFormData.name;
        channel.smtp = channelFormData.smtp;
        channel.port = channelFormData.port;
        channel.emailFrom = channelFormData.emailFrom;
        channel.emailsTo = this.createArrayFromKeySubstring(
          channelFormData, 'emailsTo');
        channel.username = channelFormData.username;
        channel.password = channelFormData.password;
        channel.info = channelFormData.info === 'true';
        channel.warning = channelFormData.warning === 'true';
        channel.critical = channelFormData.critical === 'true';
        channel.error = channelFormData.error === 'true';
        break;
    }

    channel.type = channelType;

    return channel;
  }

  /**
   * Get the RepositoryType object associated with the given id
   * @param id representing the repository
   * @returns RepositoryType
   */
  getChannelTypeById(id: string | number ): ChannelType {
    return this.channelTypes.find(channelType => channelType.id === id);
  }

  /**
   * Parse the channel data from the form into a Channel object along with the associated id
   * @param channelFormData the channel data submitted via the form
   * @returns Channel object
   * @returns the channel id being edited, if any
   */
  parseChannelFormData(channelFormData: any): [Channel, string | number] {
    const channel = this.createChannelAndSetProperties(channelFormData);
    return [channel, channelFormData.id];
  }

  /**
   * Verifies that the multiple input fields have been filled in.
   * @param formData the data submitted via the form.
   * @returns A promise object containing the boolean indicating whether the form is valid.
   */
  async verifyMultipleInputs(formData: any): Promise<boolean> {
    const channelType: ChannelType = this.getChannelTypeById(formData.type);

    switch (channelType.value) {
      case "twilio":
        if (!Object.keys(formData).includes('twilioPhoneNumbersToDial_0')) {
          await createInfoAlert(
            {
              header: "Form Error.",
              message: "You must input at least 1 phone number in 'Phone numbers for Twilio to dial'."
            });
          return false;
        }
        break;
      case "email":
        if (!Object.keys(formData).includes('emailsTo_0')) {
          await createInfoAlert(
            {
              header: "Form Error.",
              message: "You must input at least 1 email in 'Emails To'."
            });
          return false;
        }
        break;
    }

    return true;
  }

  async onSubmitHandler(e: Event) {
    e.preventDefault();

    const form = e.target as HTMLFormElement;
    const formData = parseForm(form);

    if(await this.verifyMultipleInputs(formData)){
      let [channel, id]: [Channel, string | number] = this.parseChannelFormData(formData);

      HelperAPI.emitEvent("onSave", {
        channelObject: channel,
        id: id
      });
    }
  }

  /**
   * Setting the class of the modal based on the form and channel type.
   */
  updateModalClassByChannelType() {
    const modalClassName = `panic-channel-form-modal__${this.selectedChannelType.value}`;

    const ionModal = document.getElementsByTagName("ion-modal")[0]

    this.channelTypes.forEach(channelType => {
      const possibleClass = `panic-channel-form-modal__${channelType.value}`;
      ionModal.classList.contains(possibleClass) && ionModal.classList.remove(possibleClass);
    });

    // removing the class when no channel type is selected
    ionModal.className = ionModal.className.replace("panic-channel-form-modal__no-channel-type","");

    ionModal.classList.add(modalClassName);
  }

  /**
   * [Used in edit mode]
   * This function iterates each field of the specified channel type. It then updates each
   * component within that field based on the type of component. In this way, the form object
   * is now populated with the channel data to be edited.
   */
  loadOriginalDataIntoFormComponents(): any[] {
    const fields: FormFieldInterface[] = [...this.groups[this.selectedChannelType.value].fields];

    fields.forEach(prop => {
      if(prop.componentTagName === "svc-checkbox"){
        prop.componentProps.checked = this.channel[prop.componentProps.name] === true;
      }
      if(prop.componentTagName === "svc-input"){
        prop.componentProps.value = this.channel[prop.componentProps.name];
      }
      if(prop.componentTagName === "svc-multiple-input"){
        switch (this.selectedChannelType.value) {
          case 'twilio':
            const twilioPhoneNumbersToDial: string[] = this.channel.twilioPhoneNumbersToDial;
            prop.componentProps.value = twilioPhoneNumbersToDial.map((phoneNumber => {
              return {
                label: phoneNumber,
                value: phoneNumber,
                outline: true
              }
            }));
            break;
          case 'email':
            const emailsTo: string[] = this.channel.emailsTo;
            prop.componentProps.value = emailsTo.map((email_to => {
              return {
                label: email_to,
                value: email_to,
                outline: true
              }
            }));
            break;
        }
      }
      //@ts-ignore
      if(prop.componentTagName === "panic-installer-test-button"){
        switch (this.selectedChannelType.value) {
          case 'telegram':
            //@ts-ignore
            prop.componentProps.pingProperties = {
              'botToken': this.channel.botToken,
              'botChatId': this.channel.chatId
            };
            break;
          case 'slack':
            //@ts-ignore
            prop.componentProps.pingProperties = {
              'botToken': this.channel.botToken,
              'botChannelId': this.channel.botChannelId
            };
            break;
          case 'opsgenie':
            //@ts-ignore
            prop.componentProps.pingProperties = {
              'apiKey': this.channel.apiToken,
              'eu': this.channel.eu
            };
            break;
          case 'pagerduty':
            //@ts-ignore
            prop.componentProps.pingProperties = {
              'integrationKey': this.channel.integrationKey,
            };
            break;
        }
        //@ts-ignore
        prop.componentProps.identifier = this.channel.name;
      }
      //@ts-ignore
      if(prop.componentTagName === "panic-installer-test-button-multiple-sources"){
        switch (this.selectedChannelType.value) {
          case 'twilio':
            const twilioPhoneNumbersToDial: string[] = this.channel.twilioPhoneNumbersToDial;
            //@ts-ignore
            prop.componentProps.pingProperties = twilioPhoneNumbersToDial.map((phoneNumberToDial => {
              return {
                //@ts-ignore
                accountSid: this.groups.twilio.fields[1].componentProps.value,
                //@ts-ignore
                authToken: this.groups.twilio.fields[2].componentProps.value,
                //@ts-ignore
                twilioPhoneNumber: this.groups.twilio.fields[3].componentProps.value,
                phoneNumberToDial
              }}))
            break;
          case 'email':
            const emailsTo: string[] = this.channel.emailsTo;
            //@ts-ignore
            prop.componentProps.pingProperties = emailsTo.map((email_to => {
              return {
                //@ts-ignore
                smtp: this.groups.email.fields[1].componentProps.value,
                //@ts-ignore
                port: this.groups.email.fields[2].componentProps.value,
                //@ts-ignore
                from: this.groups.email.fields[3].componentProps.value,
                //@ts-ignore
                username: this.groups.email.fields[5].componentProps.value,
                //@ts-ignore
                password: this.groups.email.fields[6].componentProps.value,
                to: email_to
              }}))
            break;
        }
      }
    });

    return fields
  }

  componentWillLoad(){
    if (this.channel) {
      this.allowSubmit = true;

      this.selectedChannelType = this.channel.type;

      this.groups[this.selectedChannelType.value].fields = this.loadOriginalDataIntoFormComponents();
      this.updateModalClassByChannelType();
    } else {
      this.allowSubmit = false;
    }
  }

  render() {
    return (
      <svc-content-container>
        <form onSubmit={(e: Event) => {this.onSubmitHandler(e)}}>
          <fieldset>
            <legend>
              {
                this.channel
                  ? "Edit Channel"
                  : "New Channel"
              }
            </legend>
            {
              this.channel &&
                <input type={'hidden'} name={'id'} value={this.channel.id}/>
            }
            <svc-select
              name={"type"}
              id={"type"}
              withBorder={true}
              placeholder={this.channel ? this.selectedChannelType.name : "Choose channel type..."}
              value={this.channel && this.selectedChannelType.value}
              subHeader={!this.channel && "Each type has a very specific configuration."}
              //@ts-ignore
              required={!this.channel && true}
              header={!this.channel && "Channel Type"}
              options={!this.channel && HelperAPI.generateSelectOptionTypeOptions(this.channelTypes)}
              disabled={this.channel && true}
              onIonChange={(e) => {
                if(!this.channel){
                  this.allowSubmit = true;
                  this.selectedChannelType = this.getChannelTypeById(e.detail.value);
                  this.updateModalClassByChannelType();
                }
              }}
            />
            {
              this.channel &&
                <input type={"hidden"} value={this.channel.type.id} name={"type"}/>}
            {
              this.selectedChannelType && this.selectedChannelType.value !== "twilio" &&
              <div>
                <div>
                  <div class={"panic-channel-form-modal__subtitle"}>
                    <svc-label position={"inline"}>
                      Severities
                    </svc-label>
                  </div>
                  {
                    /**
                     * If the original channel data is passed as a prop, the components pertaining
                     * to severity are set to the data of the channel being edited. Otherwise, the
                     * components are rendered from scratch.
                     */
                  }
                  <div class={"panic-channel-form-modal__channel-severities"}>
                    <svc-checkbox name={"info"} value={true} label={"Info"} checked={
                      this.channel ? !!this.channel.info : true
                    } lines={"full"}/>
                    <svc-checkbox name={"warning"} value={true} label={"Warning"} checked={
                      this.channel ? !!this.channel.warning : true
                    } lines={"full"}/>
                    <svc-checkbox name={"critical"} value={true} label={"Critical"} checked={
                      this.channel ? !!this.channel.critical : true
                    } lines={"full"}/>
                    <svc-checkbox name={"error"} value={true} label={"Error"} checked={
                      this.channel ? !!this.channel.error : true
                    } lines={"full"}/>
                  </div>
                </div>
                <div class={"panic-channel-form-modal__subtitle"}>
                  <svc-label position={"start"} color={"tertiary"}>
                    Disabling all severities will result in PANIC being unable to alert you via this channel.
                  </svc-label>
                </div>
              </div>
            }
            {
              this.selectedChannelType && this.selectedChannelType.value === 'twilio' &&
              <div>
                <svc-label position={"start"} color={'tertiary'} class={"panic-channel-form-modal__subtitle_2"}>
                  Twilio is only used for critical alerts.
                </svc-label>
                <input type={"hidden"} value={'true'} name={"critical"}/>
              </div>
            }
            {
              this.selectedChannelType &&
                <svc-label position={"start"} class={"panic-channel-form-modal__subtitle_2"}>
                  Specific Channel Configuration For {this.selectedChannelType.name}
                </svc-label>
            }
            {
              /**
               * Render each required component with their corresponding props.
               */
              this.selectedChannelType &&
              this.groups[this.selectedChannelType.value]?.fields.map((field: FormFieldInterface) => {
                return h(field.componentTagName, {...field.componentProps, className: "hydrated"});
              })
            }

            <div class={"panic-channel-form-modal__buttons-container"}>
              <svc-button iconName='checkmark' color={"primary"} disabled={!this.allowSubmit} type='submit'>Submit</svc-button>
              <svc-button iconName='close' color={"primary"} role={"cancel"} onClick={() => {dismissModal()}}>Cancel</svc-button>
            </div>
          </fieldset>
        </form>
      </svc-content-container>
    );
  }
}


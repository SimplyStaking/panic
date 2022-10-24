import {AbstractChannel} from "./AbstractChannel";

/**
 * Slack Channel Entity Class for Config
 */
export class SlackChannel extends AbstractChannel{

  private _appToken: string = null;
  private _botToken: string = null;
  private _botChannelId: string = null;
  private _commands: boolean = null;
  private _alerts: boolean = null;
  private _info: boolean = null;
  private _warning: boolean = null;
  private _critical: boolean = null;
  private _error: boolean = null;

  constructor() {
    super();
  }

  /**
   * App token string
   * @type string
   */
  public get appToken(): string {
    return this._appToken;
  }

  /**
   * Bot token string
   * @type string
   */
  public get botToken(): string {
    return this._botToken;
  }

  /**
   * Bot channel id string
   * @type string
   */
  public get botChannelId(): string {
    return this._botChannelId;
  }

  /**
   * Whether commands are enabled
   * @type boolean
   */
  public get commands(): boolean {
    return this._commands;
  }

  /**
   * Whether alerts are enabled
   * @type boolean
   */
  public get alerts(): boolean {
    return this._alerts;
  }

  /**
   * Whether we are enabling info alerting
   * @type boolean
   */
  public get info(): boolean {
    return this._info;
  }

  /**
   * Whether we are enabling warning alerting
   * @type boolean
   */
  public get warning(): boolean {
    return this._warning;
  }

  /**
   * Whether we are enabling critical alerting
   * @type boolean
   */
  public get critical(): boolean {
    return this._critical;
  }

  /**
   * Whether we are enabling error alerting
   * @type boolean
   */
  public get error(): boolean {
    return this._error;
  }

  public set appToken(value: string) {
    this._appToken = value;
  }

  public set botToken(value: string) {
    this._botToken = value;
  }

  public set botChannelId(value: string) {
    this._botChannelId = value;
  }

  public set commands(value: boolean) {
    this._commands = value;
  }

  public set alerts(value: boolean) {
    this._alerts = value;
  }

  public set info(value: boolean) {
    this._info = value;
  }

  public set warning(value: boolean) {
    this._warning = value;
  }

  public set critical(value: boolean) {
    this._critical = value;
  }

  public set error(value: boolean) {
    this._error = value;
  }

  /**
     * Returns all getters in JSON format
     * @param excludeFields List of fields to exclude
     *
     * @returns JSON object
     */
  public toJSON(excludeFields: string[] = []): object {

    const json = {
      ...super.toJSON(excludeFields),
      appToken: this.appToken,
      botToken: this.botToken,
      botChannelId: this.botChannelId,
      commands: this.commands,
      alerts: this.alerts,
      info: this.info,
      warning: this.warning,
      critical: this.critical,
      error: this.error
    }

    if (excludeFields)
      excludeFields.forEach(x => {
        delete json[x];
      });

    return json;
  }
}

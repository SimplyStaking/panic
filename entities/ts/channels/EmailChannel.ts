import {AbstractChannel} from "./AbstractChannel";

/**
 * E-mail Channel Entity Class for Config
 */
export class EmailChannel extends AbstractChannel{

  private _smtp: string = null;
  private _port: number = null;
  private _emailFrom: string = null;
  private _emailsTo: Array<string> = [];
  private _username: string = null;
  private _password: string = null;
  private _info: boolean = null;
  private _warning: boolean = null;
  private _critical: boolean = null;
  private _error: boolean = null;

  constructor() {
    super();
  }

  /**
   * SMTP string
   * @type string
   */
  public get smtp(): string {
    return this._smtp;
  }

  /**
   * Email Port string
   * @type number
   */
  public get port(): number {
    return this._port;
  }

  /**
   * Email to send from
   * @type string
   */
  public get emailFrom(): string {
    return this._emailFrom;
  }

  /**
   * Emails to send to
   * @type string[]
   */
  public get emailsTo(): Array<string> {
    return this._emailsTo;
  }

  /**
   * Username string
   * @type string
   */
  public get username(): string {
    return this._username;
  }

  /**
   * Password string
   * @type string
   */
  public get password(): string {
    return this._password;
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

  public set smtp(value: string) {
    this._smtp = value;
  }

  public set port(value: number) {
    this._port = value;
  }

  public set emailFrom(value: string) {
    this._emailFrom = value;
  }

  public set emailsTo(value: Array<string>) {
    this._emailsTo = value;
  }

  public set username(value: string) {
    this._username = value;
  }

  public set password(value: string) {
    this._password = value;
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
      smtp: this.smtp,
      port: this.port,
      emailFrom: this.emailFrom,
      emailsTo: this.emailsTo,
      username: this.username,
      password: this.password,
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

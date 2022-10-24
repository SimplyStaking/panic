import {AbstractChannel} from "./AbstractChannel";

/**
 * PagerDuty Channel Entity Class for Config
 */
export class PagerDutyChannel extends AbstractChannel {

  private _integrationKey: string = null;
  private _info: boolean = null;
  private _warning: boolean = null;
  private _critical: boolean = null;
  private _error: boolean = null;

  constructor() {
    super();
  }

  /**
   * Integration key string
   * @type string
   */
  public get integrationKey(): string {
    return this._integrationKey;
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

  public set integrationKey(value: string) {
    this._integrationKey = value;
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
      integrationKey: this.integrationKey,
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

import {AbstractChannel} from "./AbstractChannel";

export class TwilioChannel extends AbstractChannel{

  private _accountSid: string = null;
  private _authToken: string = null;
  private _twilioPhoneNumber: string = null;
  private _twilioPhoneNumbersToDial: Array<string> = [];
  private _critical: boolean = null;

  constructor() {
    super();
  }

  /**
   * Account SID string
   * @type string
   */
  public get accountSid(): string {
    return this._accountSid;
  }

  /**
   * Authentication token string
   * @type string
   */
  public get authToken(): string {
    return this._authToken;
  }

  /**
   * Twilio phone number
   * @type string
   */
  public get twilioPhoneNumber(): string {
    return this._twilioPhoneNumber;
  }

  /**
   * Twilio phone numbers to dial
   * @type string
   */
  public get twilioPhoneNumbersToDial(): Array<string> {
    return this._twilioPhoneNumbersToDial;
  }

  /**
   * Whether we are enabling critical alerting
   * @type boolean
   */
  public get critical(): boolean {
    return this._critical;
  }

  public set accountSid(value: string) {
    this._accountSid = value;
  }

  public set authToken(value: string) {
    this._authToken = value;
  }

  public set twilioPhoneNumber(value: string) {
    this._twilioPhoneNumber = value;
  }

  public set twilioPhoneNumbersToDial(value: Array<string>) {
    this._twilioPhoneNumbersToDial = value;
  }

  public set critical(value: boolean) {
    this._critical = value;
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
      accountSid: this.accountSid,
      authToken: this.authToken,
      twilioPhoneNumber: this.twilioPhoneNumber,
      twilioPhoneNumbersToDial: this.twilioPhoneNumbersToDial,
      critical: this.critical
    }

    if (excludeFields)
      excludeFields.forEach(x => {
        delete json[x];
      });

    return json;
  }
}

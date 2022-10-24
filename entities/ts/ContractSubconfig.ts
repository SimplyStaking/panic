import { Base } from "./Base";

/**
 * ContractSubconfig Entity Class for Config
 */
export class ContractSubconfig extends Base {

    private _url: string = null;
    private _monitor: boolean = null;

    /**
     * URL of Contract
     * @type Date
     */
	public get url(): string  {
		return this._url;
	}

    /**
     * Monitor enabled/disabled
     * @type boolean
     */
	public get monitor(): boolean  {
		return this._monitor;
	}

	public set url(value: string ) {
		this._url = value;
	}

	public set monitor(value: boolean ) {
		this._monitor = value;
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
			url: this.url,
			monitor: this.monitor
		}

		if (excludeFields)
			excludeFields.forEach(x => {
				delete json[x];
			});

		return json;
	}
}

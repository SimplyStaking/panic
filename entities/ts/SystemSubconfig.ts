import { Base } from './Base';

/**
 * SystemSubconfig Entity Class
 */
export class SystemSubconfig extends Base {

    private _monitor: boolean = null;
    private _exporterUrl: string = null;

    /**
     * Monitor enabled/disabled
     * @type boolean
     */
	public get monitor(): boolean  {
		return this._monitor;
	}

    /**
     * URLs (separeted by comma) for exporter
     * @type string
     */
	public get exporterUrl(): string  {
		return this._exporterUrl;
	}

	public set monitor(value: boolean ) {
		this._monitor = value;
	}

	public set exporterUrl(value: string ) {
		this._exporterUrl = value;
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
			monitor: this.monitor,
			exporterUrl: this.exporterUrl
		}

		if (excludeFields)
			excludeFields.forEach(x => {
				delete json[x];
			});

		return json;
	}
}

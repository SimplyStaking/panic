import { Base } from './Base';

/**
 * EVMNodeSubconfig Class for Macro Config
 */
export class EVMNodeSubconfig extends Base {

    private _monitor: boolean = null;
    private _nodeHttpUrl: string = null;

    /**
     * Monitor enabled/disabled
     * @type boolean
     */
	public get monitor(): boolean  {
		return this._monitor;
	}

    /**
     * URL
     * @type string
     */
	public get nodeHttpUrl(): string  {
		return this._nodeHttpUrl;
	}

	public set monitor(value: boolean ) {
		this._monitor = value;
	}

	public set nodeHttpUrl(value: string ) {
		this._nodeHttpUrl = value;
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
			nodeHttpUrl: this.nodeHttpUrl
		}

		if (excludeFields)
			excludeFields.forEach(x => {
				delete json[x];
			});

		return json;
	}
}

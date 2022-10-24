import { BaseSerializer } from "../serializer.interface";
import {Generic} from "../../../../entities/ts/Generic";

/**
 * Converts "raw data" (JSON response) into {@link Generic} object and vice-versa.
 */
export class DomainSerializer implements BaseSerializer<Generic> {

    unserialize(jsonObject: object): Generic {
        return Generic.fromJSON(jsonObject, Generic);
    }

    serialize(entity: Generic): string {
        return JSON.stringify(entity);
    }
}

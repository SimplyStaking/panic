import { BaseChain } from "../../../../entities/ts/BaseChain";
import { BaseSerializer } from "../serializer.interface";

/**
 * Converts "raw data" (JSON response) into {@link BaseChain} object and vice-versa.
 */
export class BaseChainSerializer implements BaseSerializer<BaseChain> {

    unserialize(jsonObject: object): BaseChain {
        return BaseChain.fromJSON(jsonObject, BaseChain);
    }

    serialize(entity: BaseChain): string {
        return JSON.stringify(entity);
    }
}

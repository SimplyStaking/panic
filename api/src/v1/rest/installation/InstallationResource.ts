import express from "express";
import {CouldNotRetrieveDataFromDB} from "../../../constant/server.feedback";
import {ResponseError, ResponseSuccess} from "../../entity/io/ResponseData";
import {ConfigModel} from "../../entity/model/ConfigModel";
import {GenericDocument} from "../../../constant/mongoose";

/**
 * Resource Controller to manage installation on Panic
 */
export class InstallationResource {

    /**
     * Checks if is first install of Panic App
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async isFirstInstall(
        req: express.Request,
        res: express.Response
    ): Promise<void> {

        try {
            const total = await ConfigModel.countDocuments({
                config_type: new Object(GenericDocument.CONFIG_TYPE_SUB_CHAIN)
            });
            const isFirstInstall = total === 0;

            const response = new ResponseSuccess<boolean>(res);
            response.send(isFirstInstall);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }
}

import express from "express";
import {Generic} from "../../../../../entities/ts/Generic";
import {SeverityAlertSubconfig} from "../../../../../entities/ts/SeverityAlertSubconfig";
import {CouldNotRetrieveDataFromDB} from "../../../constant/server.feedback";
import {ResponseError, ResponseSuccess} from "../../entity/io/ResponseData";
import {GenericRepository, SeverityAlertSubconfigRepository} from "../../entity/repository/GenericRepository";

/**
 * Resource Controller for Generic Types on Panic
 */
export class GenericResource {

    /**
     * Return a list of PANIC Channel Types
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async channelTypeList(req: express.Request,
                                 res: express.Response): Promise<void> {

        try {
            const channels = await this.getListByGroup('channel_type');
            const response = new ResponseSuccess<Generic[]>(res);
            response.send(channels);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Return a list of PANIC Threshold Alerts
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async thresholdAlertList(
        req: express.Request,
        res: express.Response
    ): Promise<void> {
        try {
            const thresholdAlerts = await this.getListByGroup('threshold_alert');
            const response = new ResponseSuccess<Generic[]>(res);
            response.send(thresholdAlerts);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Return a list of PANIC Severity Alerts
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async severityAlertList(
        req: express.Request,
        res: express.Response
    ): Promise<void> {
        try {
            const repo = new SeverityAlertSubconfigRepository();
            const severityAlerts = await repo.findByGroupAndPopulate('severity_alert', ['type']);
            const response = new ResponseSuccess<SeverityAlertSubconfig[]>(res);
            response.send(severityAlerts);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Return a list of PANIC Time Window Alerts
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async timeWindowAlertList(
        req: express.Request,
        res: express.Response
    ): Promise<void> {
        try {
            const timeWindowAlerts = await this.getListByGroup('time_window_alert');
            const response = new ResponseSuccess<Generic[]>(res);
            response.send(timeWindowAlerts);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Return a list of PANIC Severity Types
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async severityTypeList(
        req: express.Request,
        res: express.Response
    ): Promise<void> {
        try {
            const severityTypes = await this.getListByGroup('severity_type');
            const response = new ResponseSuccess<Generic[]>(res);
            response.send(severityTypes);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Return a list of PANIC Repository Types
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async repositoryTypeList(
        req: express.Request,
        res: express.Response
    ): Promise<void> {
        try {
            const repositoryTypes = await this.getListByGroup('repository_type');
            const response = new ResponseSuccess<Generic[]>(res);
            response.send(repositoryTypes);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Return a list of PANIC Config Types
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async configTypeList(
        req: express.Request,
        res: express.Response
    ): Promise<void> {
        try {
            const configTypes = await this.getListByGroup('config_type');
            const response = new ResponseSuccess<Generic[]>(res);
            response.send(configTypes);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Return a list of PANIC Source Types
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async sourceTypeList(
        req: express.Request,
        res: express.Response
    ): Promise<void> {

        try {
            const sourceTypes = await this.getListByGroup('source_type');
            const response = new ResponseSuccess<Generic[]>(res);
            response.send(sourceTypes);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Return a list of Generic documents from the database filtered by group
     *
     * @param group filter in generic collection
     */
    private async getListByGroup(group: string): Promise<Generic[]> {
        const repo = new GenericRepository();
        return repo.findByGroup(group);
    }

    /**
     * Return a list of Generic documents with some populated fields from the database filtered by group
     *
     * @param group filter in generic collection
     * @param fieldsToPopulate reference fields to populate within documents
     */
    private async getListByGroupAndPopulate(group: string, fieldsToPopulate: string[]): Promise<Generic[]> {
        const repo = new GenericRepository();
        return repo.findByGroupAndPopulate(group, fieldsToPopulate);
    }
}

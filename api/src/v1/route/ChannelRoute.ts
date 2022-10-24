import * as core from 'express-serve-static-core';
import {ChannelResource} from "../rest/channel/ChannelResource";

/**
 * Channel routes
 */
export class ChannelRoute {
    public constructor(app: core.Express) {
        const channel = new ChannelResource();

        app.get('/v1/channels', channel.getAll.bind(channel));
        app.post('/v1/channels', channel.create.bind(channel));
        app.get('/v1/channels/:id', channel.getItem.bind(channel));
        app.put('/v1/channels/:id', channel.update.bind(channel));
        app.delete('/v1/channels/:id', channel.remove.bind(channel));

        app.post('/v1/channels/:channel_id/configs/:config_id', channel.createConfigLink.bind(channel));
        app.delete('/v1/channels/:channel_id/configs/:config_id', channel.removeConfigLink.bind(channel));
    }
}

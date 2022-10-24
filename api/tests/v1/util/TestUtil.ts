import {ChannelType} from "../../../../entities/ts/ChannelType";
import {Generic} from "../../../../entities/ts/Generic";
import {RepositoryType} from "../../../../entities/ts/RepositoryType";
import {SeverityType} from "../../../../entities/ts/SeverityType";

export class TestUtil {

    /**
     * Util to check data structure of the Channel Type model
     * @param channel
     */
    public static channel(channel: ChannelType): void {
        expect(channel.id.toString()).toEqual('62656ebafdb17d641746dcda');
        expect(channel.status).toEqual(true);

        //1651528966 = 2022-04-01T00:00:00.000Z
        const created: number = new Date(channel.created).getTime() / 1000;
        expect(created).toEqual(1648771200);

        expect(channel.modified).toEqual(null);
        expect(channel.name).toEqual('Telegram');
        expect(channel.description).toEqual(null);
        expect(channel.value).toEqual('telegram');
        expect(channel.group).toEqual('channel_type');
    }

    /**
     * Util to check data structure of the Severity Type model
     * @param type
     */
    public static severityType(type: SeverityType): void {
        expect(type.id.toString()).toEqual('6265d08efdb17d641746dcf0');
        expect(type.status).toEqual(true);

        //1651528966 = 2022-05-02T22:02:46.000Z
        const created: number = new Date(type.created).getTime() / 1000;
        expect(created).toEqual(1651528966);

        expect(type.modified).toEqual(null);
        expect(type.name).toEqual('Warning');
        expect(type.description).toEqual(null);
        expect(type.value).toEqual(null);
        expect(type.group).toEqual('severity_type');
    }


    /**
     * Util to check data structure of the Repository Type model
     * @param type
     */
    public static repository(type: RepositoryType): void {
        expect(type.status).toEqual(true);

        //1651528966 = 2022-05-02T22:02:46.000Z
        const created: number = new Date(type.created).getTime() / 1000;
        expect(created).toEqual(1651528966);

        expect(type.modified).toEqual(null);
        expect(type.name).toEqual('Github Repo');
        expect(type.description).toEqual(null);
        expect(type.value).toEqual('git');
        expect(type.group).toEqual('repository_type');
    }

    /**
     * Util to check data structure of the Config Type model
     * @param type
     */
    public static config(type: Generic): void {
        expect(type.id.toString()).toEqual('6265758cfdb17d641746dce4');
        expect(type.status).toEqual(true);

        //1651528966 = 2022-05-02T22:02:46.000Z
        const created: number = new Date(type.created).getTime() / 1000;
        expect(created).toEqual(1651528966);

        expect(type.modified).toEqual(null);
        expect(type.name).toEqual('Sub Chain');
        expect(type.description).toEqual(null);
        expect(type.value).toEqual(null);
        expect(type.group).toEqual('config_type');
    }

    /**
     * Util to check data structure of the Source Type model
     * @param source generic source to check
     */
    public static source(source: Generic): void {
        expect(source.id.toString()).toEqual('6271178cf740ef3847a7d27e');
        expect(typeof source.status).toEqual('boolean');

        //1648771200 = 2022-04-01T00:00:00.000Z
        const created: number = new Date(source.created).getTime() / 1000;
        expect(created).toEqual(1648771200);

        expect(source.modified).toEqual(null);
        expect(source.name).toEqual('Contract');
        expect(source.value).toEqual('contract');
        expect(source.description).toEqual(null);
        expect(source.group).toEqual('source_type');
    }
}

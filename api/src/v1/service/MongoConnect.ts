import mongosee, { ConnectOptions } from 'mongoose';

/**
 * MongoConnect Singleton class, to prevent create many connnections.
 */
export class MongoConnect {
    private static instance: Promise<mongosee.Connection>;

    /**
     * Constructor should always be private to prevent create a new Object
     */
    private constructor() { }

    /**
     * 
     * Controls the access to the singleton instance, (e.g., x.getInstance())
     * Put Mongoose in an instance attribute
     */
    public static async getInstance(): Promise<mongosee.Connection> {
        if (!MongoConnect.instance) {
            MongoConnect.instance = MongoConnect.getConnection();
        }

        return MongoConnect.instance;
    }

    /**
     * Alias for MongoConnect.getInstance
     */
    public static async start(): Promise<mongosee.Connection> {
        return MongoConnect.getInstance();
    }

    private static getConnection(): Promise<mongosee.Connection> {

        const port = parseInt(process.env.DB_PORT || "27017");
        const db = process.env.DB_NAME || "panicdb";
        const connection = mongosee.connection;

        const opt: ConnectOptions = {
            dbName: db,
            replicaSet: 'replica-set',
            readPreference: 'primaryPreferred'
        }
        mongosee.connect(`mongodb://rs1:${port},rs2:${port},rs3:${port}`, opt);

        mongosee.pluralize(null);

        mongosee.connection.on('connecting', () =>
            console.log(`connecting to mongodb: ${connection.host}`));

        mongosee.connection.on('connected', () => {
            console.log(`mongodb connected to: ${connection.host}:
                ${connection.port}/${connection.name}`)
        });

        mongosee.connection.on('open', () =>
            console.log(`mongodb connection open: ${connection.host}`));

        mongosee.connection.on('disconnecting', () =>
            console.log(`disconnecting mongodb: ${connection.host}`));

        mongosee.connection.on('disconnected', () =>
            console.log(`mongodb disconnected: ${connection.host}`));

        mongosee.connection.on('close', () =>
            console.log(`mongodb connection closed: ${connection.host}`));

        mongosee.connection.on('reconnected', () =>
            console.log(`mongodb reconnected: ${connection.host}`));

        mongosee.connection.on('error', () =>
            console.log(`mongodb error: ${connection.host}`));

        mongosee.connection.on('fullsetup', () =>
            console.log(`fullsetup: ${connection.host}`));

        mongosee.connection.on('all', () =>
            console.log(`all: ${connection.host}`));

        mongosee.connection.on('reconnectFailed', () =>
            console.log(`reconnectFailed: ${connection.host}`));

        return mongosee.connection.asPromise();
    }
}
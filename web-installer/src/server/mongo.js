const mongoClient = require('mongodb').MongoClient;
const errors = require('./errors');

const options = {
  useNewUrlParser: true,
  useUnifiedTopology: true,
  socketTimeoutMS: 10000,
  connectTimeoutMS: 10000,
  serverSelectionTimeoutMS: 5000,
};

module.exports = {
  options,

  // This functions saves a record to a collection and makes sure that the key
  // is unique via a query.
  saveToDatabase: async (mongoDBUrl, dbname, record, collection, query) => {
    let client;
    let db;
    try {
      // connect
      client = await mongoClient.connect(mongoDBUrl, options);
      db = client.db(dbname);
      const collectionInterface = db.collection(collection);
      // Check if record already exists by using the unique key and its value.
      // If yes, throw an already exists error, otherwise add the record to the
      // database
      const doc = await collectionInterface.findOne(query);
      if (doc) {
        throw new errors.RecordAlreadyExists(query);
      }
      await collectionInterface.insertOne(record);
    } catch (err) {
      // If the error is an already exists error re-throw it. Otherwise it must be
      // a mongo error.
      if (err.code === 446) {
        throw err;
      }
      throw new errors.MongoError(err.message);
    } finally {
      // Check if an error was thrown after a connection was established. If this
      // is the case close the database connection to prevent leaks
      if (client && client.isConnected()) {
        await client.close();
      }
    }
  },

  // This function deletes an account from the accounts collection
  removeFromCollection: async (mongoDBUrl, dbname, collection, record) => {
    let client;
    let db;
    try {
      // Connect
      client = await mongoClient.connect(mongoDBUrl, options);
      db = client.db(dbname);
      const collectionInterface = db.collection(collection);
      await collectionInterface.deleteOne(record);
    } catch (err) {
      // If an error is raised throw a MongoError
      throw new errors.MongoError(err.message);
    } finally {
      // Check if an error was thrown after a connection was established. If this
      // is the case close the database connection to prevent leaks
      if (client && client.isConnected()) {
        await client.close();
      }
    }
  },

  // This function deletes a collection
  dropCollection: async (mongoDBUrl, dbname, collection) => {
    let client;
    let db;
    try {
      // Connect
      client = await mongoClient.connect(mongoDBUrl, options);
      db = client.db(dbname);
      const collectionInterface = db.collection(collection);
      await collectionInterface.drop();
    } catch (err) {
      // If an error is raised throw a MongoError
      throw new errors.MongoError(err.message);
    } finally {
      // Check if an error was thrown after a connection was established. If this
      // is the case close the database connection to prevent leaks
      if (client && client.isConnected()) {
        await client.close();
      }
    }
  },

  // This function returns true if a record already exists in a collection based
  // on a query
  recordExists: async (mongoDBUrl, dbname, collection, query) => {
    let client;
    let db;
    try {
      // Connect
      client = await mongoClient.connect(mongoDBUrl, options);
      db = client.db(dbname);
      const collectionInterface = db.collection(collection);
      // Check if a record already exists. If it does it returns true, otherwise
      // it returns false.
      const doc = await collectionInterface.findOne(query);
      return !!doc; // This must be done because doc is not a boolean
    } catch (err) {
      // If an error is raised throw a MongoError
      throw new errors.MongoError(err.message);
    } finally {
      // Check if an error was thrown after a connection was established. If this
      // is the case close the database connection to prevent leaks
      if (client && client.isConnected()) {
        await client.close();
      }
    }
  },

  // This function returns all records
  getRecords: async (mongoDBUrl, dbname, collection) => {
    let client;
    let db;
    try {
      // Connect
      client = await mongoClient.connect(mongoDBUrl, options);
      db = client.db(dbname);
      const collectionInterface = db.collection(collection);
      const doc = await collectionInterface.find().toArray();
      return doc;
    } catch (err) {
      // If an error is raised throw a MongoError
      throw new errors.MongoError(err.message);
    } finally {
      // Check if an error was thrown after a connection was established. If this
      // is the case close the database connection to prevent leaks
      if (client && client.isConnected()) {
        await client.close();
      }
    }
  },
};

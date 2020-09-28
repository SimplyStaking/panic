import os
from alerter.src.utils.logging import DUMMY_LOGGER
from alerter.src.data_store.mongo.mongo_api import MongoApi


if __name__ == '__main__':
    mongo_host = os.environ["DB_HOST"]
    mongo_port = int(os.environ["DB_PORT"])
    mongo_db = os.environ["DB_NAME"]
    mongo_api = MongoApi(DUMMY_LOGGER, mongo_db, mongo_host, mongo_port)
    print(mongo_api.get_all("installer_authentication"))
    print(mongo_api.ping_unsafe())
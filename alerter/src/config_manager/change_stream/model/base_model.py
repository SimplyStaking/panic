from datetime import datetime

import bson


class BaseModel:
    """
    Base Model persisted on MongoDB
    """

    _id: bson.ObjectId = None
    modified: datetime = None
    created: datetime = None

    def tuple2obj(self, tuple):
        self.created = tuple.created
        self.modified = tuple.modified


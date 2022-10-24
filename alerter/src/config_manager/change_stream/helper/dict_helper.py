from collections import namedtuple
from typing import Dict

from src.config_manager.change_stream.model.base_model import BaseModel


class obj:

    # constructor
    def __init__(self, dict1):
        self.__dict__.update(dict1)


class DictHelper:

    @staticmethod
    def dict2obj(model: BaseModel, data: Dict):

        is_dict = type(data) is dict
        if not is_dict:
            return None

        tuple = namedtuple(model.__name__, data.keys(),
                           rename=True)(*data.values())

        obj: BaseModel = model()

        if (data.get('_id')):
            obj._id = data.get('_id')

        obj.tuple2obj(tuple)
        return obj
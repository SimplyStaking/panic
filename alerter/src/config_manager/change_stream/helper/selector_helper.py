from typing import Dict

class SelectorHelper:
    """
    Helps to create a selector routing key and data dict
    
    TODO: Rename helper to iterable and improve architecture
    """
    
    def __init__(self, rkey: str , data: dict):
        self._routing_key = rkey.lower()
        self._data = data
                
    @property
    def data(self) -> Dict:
        return self._data

    @property
    def routing_key(self) -> str:
        return self._routing_key
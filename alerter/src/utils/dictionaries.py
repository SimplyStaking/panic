from typing import Dict, List, Hashable


def dict_remove_key(a: Dict, key: Hashable) -> Dict:
    """
    Returns the given dictionary without the given key (if present).
    Unlike the inbuilt dict.pop(key, None), this function has no side-effects.
    """
    return {k: v for k, v in a.items() if k != key}


def dict_key_diff(a: Dict, b: Dict) -> Dict:
    """
    Returns the items in a given dictionary which do not share keys with
    the second given dictionary.
    """
    return {k: a[k] for k in a.keys() if k not in b}


def dict_key_intersection(a: Dict, b: Dict) -> Dict:
    """
    Returns a dictionary with items of the form k : (value1, value2), where
    k ranges over the keys present in both dictionaries, and the two values
    are those in the first and second dictionaries corresponding to that key.
    """
    return {k: (a[k], b[k]) for k in a.keys() if k in b}


def dict_value_diff(a: Dict, b: Dict) -> List:
    """
    Returns the values in the first dictionary  which are not present as values
    in the second.
    """
    return [v for v in a.values() if v not in b.values()]


def dict_value_intersection(a: Dict, b: Dict) -> List:
    """
    Returns the list of values which appear in both dictionaries.
    """
    return [v for v in a.values() if v in b.values()]


def dict_2d_value_diff_by_key(a: Dict, b: Dict, k: Hashable) -> List:
    """
    Assuming we are given two 2-dimensional dictionaries, i.e., dictionaries
    whose values are also dictionaries, this function returns those
    "value-dictionaries" in the first dictionary which do not share the given
    key with any "value-dictionary" in the second.
    """
    return [da for da in a.values() if da[k] not in
            [db[k] for db in b.values()]]


def dict_2d_value_intersection_by_key(a: Dict, b: Dict, k: Hashable) -> Dict:
    """
    Assuming we are given two 2-dimensional dictionaries, i.e., dictionaries
    whose values are also dictionaries, this function gives the
    "value-dictionaries" which have the same value for the given key in both
    dictionaries.
    E.g., if d1 = {'0': {'a': 'x', 'b': 2}, '1': {'a': 'y', 'b': 4}} and
             d2 = {'0': {'a': 'x', 'b': 5}, '1': {'a': 'z', 'b': 7}},
    then f(d1, d2, 'a') = {'x': ({'b': 2}, {'b': 5})}
    """
    return {da[k]: (dict_remove_key(da, k), dict_remove_key(db, k))
            for db in b.values() for da in a.values() if db[k] == da[k]}

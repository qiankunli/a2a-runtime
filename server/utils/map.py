from typing import Any, Dict


def extract_nested_data(data, path):
    for key in path.split('.'):
        if key in data:
            data = data[key]
        else:
            return None
    return data


def get_value(data: Dict[str, Any] | None, key: str, default=None):
    if not data:
        return default
    return data.get(key, default)

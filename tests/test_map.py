from server.utils.map import extract_nested_data


def test_extract_nested_data():
    data = {'a': {'b': {'c': 1}}}
    path = 'a.b.c'
    assert extract_nested_data(data, path) == 1

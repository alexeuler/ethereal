from ethereal.cache import canonical_arguments


def test_canonical_arguments():
    cases = [
        "a",
        1,
        1.0,
        True,
        None,
        [1, 3, 2],
        {"b": 1, "a": 2},
        (1, 3, {"b": {"c": [3, 2, 1], "a": None}, "a": 2}),
    ]
    results = [
        "a",
        1,
        1.0,
        True,
        None,
        [1, 3, 2],
        {"a": 2, "b": 1},
        [1, 3, {"a": 2, "b": {"a": None, "c": [3, 2, 1]}}],
    ]
    for i in range(len(cases)):
        assert canonical_arguments(cases[i]) == results[i], f"Failed on case {i}"

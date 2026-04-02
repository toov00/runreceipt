from runreceipt.env_diff import diff_env


def test_diff_empty():
    d = diff_env({}, {})
    assert d["added"] == {}
    assert d["removed"] == []
    assert d["changed"] == {}


def test_diff_added_removed_changed():
    before = {"A": "1", "B": "2", "C": "3"}
    after = {"B": "2", "C": "4", "D": "5"}
    d = diff_env(before, after)
    assert d["added"] == {"D": "5"}
    assert d["removed"] == ["A"]
    assert d["changed"] == {"C": {"before": "3", "after": "4"}}

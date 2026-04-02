import pytest

from runreceipt.show import display_receipt_md, resolve_receipt_md


def test_resolve_by_receipt_dir(tmp_path):
    d = tmp_path / "rid"
    d.mkdir()
    md = d / "receipt.md"
    md.write_text("# hi\n", encoding="utf-8")
    assert resolve_receipt_md(str(d), None) == md.resolve()


def test_resolve_by_receipt_md_path(tmp_path):
    md = tmp_path / "receipt.md"
    md.write_text("# x\n", encoding="utf-8")
    assert resolve_receipt_md(str(md), None) == md.resolve()


def test_resolve_by_receipt_json_path(tmp_path):
    d = tmp_path / "rid"
    d.mkdir()
    (d / "receipt.json").write_text("{}", encoding="utf-8")
    md = d / "receipt.md"
    md.write_text("# y\n", encoding="utf-8")
    assert resolve_receipt_md(str(d / "receipt.json"), None) == md.resolve()


def test_resolve_by_id_under_root(tmp_path):
    root = tmp_path / "rr"
    receipts = root / "receipts"
    rid = receipts / "myid_abc"
    rid.mkdir(parents=True)
    md = rid / "receipt.md"
    md.write_text("# z\n", encoding="utf-8")
    assert resolve_receipt_md("myid_abc", root) == md.resolve()


def test_resolve_dir_without_md_falls_back_to_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "rr"
    conflicting = tmp_path / "same_name"
    conflicting.mkdir()
    receipts = root / "receipts" / "same_name"
    receipts.mkdir(parents=True)
    md = receipts / "receipt.md"
    md.write_text("# ok\n", encoding="utf-8")
    assert resolve_receipt_md("same_name", root) == md.resolve()


def test_resolve_wrong_file_name(tmp_path):
    f = tmp_path / "readme.txt"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        resolve_receipt_md(str(f), None)


def test_display_no_pager_writes(tmp_path, capsys):
    md = tmp_path / "receipt.md"
    md.write_text("body\n", encoding="utf-8")
    display_receipt_md(md, use_pager=False)
    assert capsys.readouterr().out == "body\n"


def test_display_no_final_newline(tmp_path, capsys):
    md = tmp_path / "receipt.md"
    md.write_text("only", encoding="utf-8")
    display_receipt_md(md, use_pager=False)
    assert capsys.readouterr().out == "only\n"

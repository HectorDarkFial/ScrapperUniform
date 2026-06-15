from __future__ import annotations

from portal.api_views import _safe_export_path


def test_safe_export_path_resolves_file(tmp_path, monkeypatch):
    from django.conf import settings

    monkeypatch.setattr(settings, "BASE_DIR", tmp_path)
    exports = tmp_path / "data" / "exports"
    exports.mkdir(parents=True)
    sample = exports / "informe_test.xlsx"
    sample.write_bytes(b"ok")

    resolved = _safe_export_path("informe_test.xlsx")
    assert resolved is not None
    assert resolved.read_bytes() == b"ok"


def test_safe_export_path_blocks_traversal(tmp_path, monkeypatch):
    from django.conf import settings

    monkeypatch.setattr(settings, "BASE_DIR", tmp_path)
    (tmp_path / "data" / "exports").mkdir(parents=True)

    assert _safe_export_path("../secret") is None
    assert _safe_export_path("subdir/file.xlsx") is None

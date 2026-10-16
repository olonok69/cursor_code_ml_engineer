from datetime import timedelta

import pytest
from evidence.conftest import T0, FakeS3
from evidence.errors import RecoveryBroken
from evidence.versions import at_or_before, check_recovery, in_window, list_versions

B, K = "bkt", "uploads/10/a.docx"
S3 = FakeS3({(B, K): [("v1", T0 - timedelta(days=8), b"old"), ("v2", T0 - timedelta(seconds=20), b"run"),
                      ("v3", T0 + timedelta(minutes=26), b"resaved")],
             (B, K + ".bak"): [("x", T0, b"other key")]})

def test_list_versions_exact_key_sorted():
    assert [v.version_id for v in list_versions(S3, B, K)] == ["v1", "v2", "v3"]

def test_source_is_version_at_run_time_not_latest():
    assert at_or_before(list_versions(S3, B, K), T0).version_id == "v2"

def test_none_before_first_upload():
    assert at_or_before(list_versions(S3, B, K), T0 - timedelta(days=30)) is None

def test_in_window_stops_at_next_run():
    vs = list_versions(S3, B, K)
    assert in_window(vs, T0, T0 + timedelta(minutes=10)) is None
    assert in_window(vs, T0, None).version_id == "v3"

def test_recovery_ok():
    assert check_recovery(S3, B) == {"bucket_versioning": "Enabled", "expiry_rules": []}

def test_recovery_broken_when_versioning_off():
    with pytest.raises(RecoveryBroken):
        check_recovery(FakeS3({}, versioning="Suspended"), B)

def test_recovery_broken_by_noncurrent_expiry():
    rules = [{"ID": "trim", "Status": "Enabled", "NoncurrentVersionExpiration": {"NoncurrentDays": 30}}]
    with pytest.raises(RecoveryBroken, match="trim"):
        check_recovery(FakeS3({}, lifecycle_rules=rules), B)


def test_source_picks_upload_landing_just_after_data_line():
    """Measured 2026-10-15: an upload's LastModified is ~1 s AFTER its 'Data to process' line."""
    from evidence.versions import source_version
    vs = list_versions(FakeS3({(B, K): [("prev", T0 - timedelta(days=9), b"a"),
                                         ("own", T0 + timedelta(seconds=1), b"b"),
                                         ("next-upload", T0 + timedelta(minutes=27, seconds=1), b"c")]}), B, K)
    assert source_version(vs, T0, T0 + timedelta(minutes=27)).version_id == "own"
    assert source_version(vs, T0, None).version_id == "own"          # 60 s grace, not open-ended


def test_source_grace_never_crosses_next_run():
    from evidence.versions import source_version
    vs = list_versions(FakeS3({(B, K): [("own", T0 - timedelta(seconds=2), b"a"),
                                         ("next", T0 + timedelta(seconds=10), b"b")]}), B, K)
    assert source_version(vs, T0, T0 + timedelta(seconds=9)).version_id == "own"

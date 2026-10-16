import pytest
from evidence.awsro import ReadOnlyClient

class _Raw:
    def get_object(self, **kw): return "got"
    def put_object(self, **kw): return "put"
    def delete_object(self, **kw): return "deleted"
    def filter_log_events(self, **kw): return "filtered"
    meta = "meta"

def test_reads_pass_through():
    c = ReadOnlyClient(_Raw())
    assert c.get_object(Bucket="b") == "got"
    assert c.filter_log_events() == "filtered"
    assert c.meta == "meta"

@pytest.mark.parametrize("name", ["put_object", "delete_object"])
def test_writes_are_refused(name):
    with pytest.raises(PermissionError, match="read-only"):
        getattr(ReadOnlyClient(_Raw()), name)

def test_no_module_calls_a_write_method():
    """Static guard: no tool module names a mutating boto3 method."""
    import pathlib, re
    banned = re.compile(r"\.(put_|delete_|create_|update_|copy_|upload_|restore_|invoke)\w*\(")
    root = pathlib.Path(__file__).parent
    offenders = [p.name for p in root.glob("*.py")
                 if not p.name.startswith("test_") and banned.search(p.read_text())]
    assert offenders == []

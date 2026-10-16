"""Offline fakes for the evidence core tests. No AWS access needed."""
import io
from datetime import datetime, timezone

T0 = datetime(2026, 10, 15, 8, 51, 44, tzinfo=timezone.utc)   # a run's start (its log line)


class FakeS3:
    """versions: {(bucket, key): [(version_id, last_modified, bytes), ...]}"""

    def __init__(self, versions: dict, versioning: str = "Enabled", lifecycle_rules: list | None = None):
        self.versions = versions
        self.versioning = versioning
        self.lifecycle_rules = lifecycle_rules

    def get_paginator(self, name):
        assert name == "list_object_versions"
        fake = self

        class _P:
            def paginate(self, Bucket, Prefix):
                items = [{"Key": k, "VersionId": vid, "LastModified": lm, "Size": len(body), "IsLatest": False}
                         for (b, k), vs in fake.versions.items() if b == Bucket and k.startswith(Prefix)
                         for vid, lm, body in vs]
                yield {"Versions": items}
        return _P()

    def get_object(self, Bucket, Key, VersionId=None):
        for vid, lm, body in self.versions[(Bucket, Key)]:
            if VersionId in (None, vid):
                return {"Body": io.BytesIO(body), "VersionId": vid, "LastModified": lm}
        raise KeyError(Key)

    def get_bucket_versioning(self, Bucket):
        return {"Status": self.versioning}

    def get_bucket_lifecycle_configuration(self, Bucket):
        if self.lifecycle_rules is None:
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "NoSuchLifecycleConfiguration"}}, "GetBucketLifecycleConfiguration")
        return {"Rules": self.lifecycle_rules}

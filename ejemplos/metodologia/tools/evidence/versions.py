from dataclasses import dataclass
from datetime import datetime, timedelta

from botocore.exceptions import ClientError

from evidence.errors import RecoveryBroken


@dataclass(frozen=True)
class ObjVersion:
    key: str
    version_id: str
    last_modified: datetime
    size: int


def list_versions(s3, bucket: str, key: str) -> list[ObjVersion]:
    out = []
    for page in s3.get_paginator("list_object_versions").paginate(Bucket=bucket, Prefix=key):
        for v in page.get("Versions", []):
            if v["Key"] == key:
                out.append(ObjVersion(key, v["VersionId"], v["LastModified"], v["Size"]))
    return sorted(out, key=lambda v: v.last_modified)


def at_or_before(versions: list[ObjVersion], t: datetime) -> ObjVersion | None:
    candidates = [v for v in versions if v.last_modified <= t]
    return candidates[-1] if candidates else None


SOURCE_GRACE = timedelta(seconds=60)


def source_version(versions: list[ObjVersion], start: datetime, next_start: datetime | None) -> ObjVersion | None:
    """The source as it was at the run.

    The upload that triggers a run lands in S3 ~1 s AFTER its 'Data to process' line (measured 2026-10-15),
    so 'at or before the run start' would pick the PREVIOUS upload. Take the newest version up to
    start + 60 s, never reaching the next run that writes the same key.
    """
    limit = start + SOURCE_GRACE
    candidates = [v for v in versions
                  if v.last_modified <= limit and (next_start is None or v.last_modified < next_start)]
    return candidates[-1] if candidates else None


def in_window(versions: list[ObjVersion], start: datetime, end: datetime | None) -> ObjVersion | None:
    floor = start.replace(microsecond=0)            # S3 LastModified has 1-second resolution
    candidates = [v for v in versions if v.last_modified >= floor and (end is None or v.last_modified < end)]
    return candidates[-1] if candidates else None


def check_recovery(s3, bucket: str) -> dict:
    status = s3.get_bucket_versioning(Bucket=bucket).get("Status") or "Disabled"
    try:
        rules = s3.get_bucket_lifecycle_configuration(Bucket=bucket).get("Rules", [])
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") != "NoSuchLifecycleConfiguration":
            raise
        rules = []
    expiring = [r.get("ID", "?") for r in rules
                if r.get("Status") == "Enabled" and ("NoncurrentVersionExpiration" in r or "Expiration" in r)]
    result = {"bucket_versioning": status, "expiry_rules": expiring}
    if status != "Enabled" or expiring:
        raise RecoveryBroken(f"bucket {bucket} no longer guarantees recovery of old versions: {result}")
    return result

import os
from typing import Any, NamedTuple

ALLOWED_PREFIXES = ("get_", "list_", "describe_", "head_", "filter_log_events", "can_paginate")
PASSTHROUGH = ("meta", "exceptions")
DEFAULT_PROFILE = os.environ.get("EVIDENCE_PROFILE", "<read-only-profile>")   # a read-only SSO profile
DEFAULT_REGION = os.environ.get("AWS_REGION", "<region>")


class ReadOnlyClient:
    """Wraps a boto3 client and refuses every method that is not a read."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def __getattr__(self, name: str) -> Any:
        if name in PASSTHROUGH or name.startswith("_"):
            return getattr(self._client, name)
        if not name.startswith(ALLOWED_PREFIXES):
            raise PermissionError(f"evidence is read-only: '{name}' is not allowed")
        return getattr(self._client, name)


class Clients(NamedTuple):
    logs: Any
    s3: Any
    lam: Any


def make_clients(profile: str = DEFAULT_PROFILE, region: str = DEFAULT_REGION) -> Clients:
    import boto3

    session = boto3.Session(profile_name=profile, region_name=region)
    return Clients(
        logs=ReadOnlyClient(session.client("logs")),
        s3=ReadOnlyClient(session.client("s3")),
        lam=ReadOnlyClient(session.client("lambda")),
    )

import re

_PATTERNS = [
    (re.compile(r"\?X-Amz-[^\s'\"<>]*"), "?<presigned-signature-removed>"),
    (re.compile(r"X-Amz-(Credential|Signature|Security-Token)=[^\s&'\"<>]*"), r"X-Amz-\1=<removed>"),
    (re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "<access-key-removed>"),
]


def scrub(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text

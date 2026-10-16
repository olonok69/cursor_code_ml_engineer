class EvidenceError(Exception):
    exit_code = 3

class UsageError(EvidenceError):
    exit_code = 1

class LoginError(EvidenceError):
    exit_code = 2

class AwsError(EvidenceError):
    exit_code = 3

class NothingFound(EvidenceError):
    exit_code = 4

class GuardTripped(EvidenceError):
    exit_code = 5

class RecoveryBroken(EvidenceError):
    exit_code = 6

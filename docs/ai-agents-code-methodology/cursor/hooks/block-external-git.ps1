# Cursor beforeShellExecution hook — ask before irreversible / outward actions.
# Reads JSON on stdin; writes JSON permission decision on stdout.
$ErrorActionPreference = "Stop"

$inputJson = [Console]::In.ReadToEnd()
$payload = $null
try {
    $payload = $inputJson | ConvertFrom-Json
} catch {
    Write-Output '{"permission":"allow"}'
    exit 0
}

$command = [string]($payload.command)
if ([string]::IsNullOrWhiteSpace($command)) {
    Write-Output '{"permission":"allow"}'
    exit 0
}

$patterns = @(
    'git\s+push',
    'gh\s+pr\s+create',
    'gh\s+pr\s+merge',
    'terraform\s+apply',
    'kubectl\s+apply',
    'helm\s+upgrade',
    'aws\s+.*deploy'
)

$blocked = $false
foreach ($p in $patterns) {
    if ($command -match $p) {
        $blocked = $true
        break
    }
}

if ($blocked) {
    $result = @{
        permission    = "ask"
        user_message  = "Methodology handoff gate: this command looks outward-facing (push/PR/deploy). Approve only if you explicitly want the agent to run it."
        agent_message = "Blocked for human confirmation: external/irreversible action. Prepare the branch and handover instead unless the user explicitly asked for this command."
    } | ConvertTo-Json -Compress
    Write-Output $result
    exit 0
}

Write-Output '{"permission":"allow"}'
exit 0

#!/usr/bin/env bash
# Who synced what, and when — across every machine in the shared record.
#
#   ./activity.sh              # last pull + last push per machine, newest first
#   ./activity.sh --log        # the full event stream (most recent 40)
#   ./activity.sh --log 200    # ... more of it
#   ./activity.sh --stale 2    # exit 1 if THIS machine has not pulled in N days (for scripts)
#
# Reads _activity/<machine>.jsonl, written by data-pull.sh / data-push.sh. Those files
# sync with the shared record, so this answers "has my teammate pulled my work yet?"
# as well as "when did I last pull?".
#
# ⚠️ It reports what the LEDGER says, which is only as complete as the syncs that wrote
# it. A machine that has never run the patched scripts shows nothing — absence here is
# "no record", never "no activity". Anyone can also sync by other means.
set -uo pipefail
cd "$(dirname "$0")"
source ./config.env
ACT_DIR="./_activity"

MODE="summary"; ARG=""
case "${1:-}" in
  --log)   MODE="log";   ARG="${2:-40}" ;;
  --stale) MODE="stale"; ARG="${2:-1}"  ;;
  "")      ;;
  *) echo "usage: $0 [--log [N] | --stale [DAYS]]" >&2; exit 2 ;;
esac

python3 - "$ACT_DIR" "$MODE" "$ARG" "${MACHINE_NAME:-unknown}" <<'PY'
import glob, json, os, sys, datetime

act_dir, mode, arg, me = sys.argv[1:5]
now = datetime.datetime.now(datetime.timezone.utc)

events = []
for path in glob.glob(os.path.join(act_dir, "*.jsonl")):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue          # a torn line loses one record, not the report

if not events:
    print("No sync activity recorded yet.")
    print(f"(looked in {act_dir}/*.jsonl — written by data-pull.sh / data-push.sh)")
    sys.exit(0 if mode != "stale" else 0)

def age(ts):
    try:
        t = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc)
    except ValueError:
        return None, "?"
    d = now - t
    if d.days >= 1:
        return d, f"{d.days}d ago"
    h = d.seconds // 3600
    return d, (f"{h}h ago" if h else f"{max(d.seconds // 60, 0)}m ago")

events.sort(key=lambda e: e.get("ts", ""))

if mode == "stale":
    days = float(arg or 1)
    mine = [e for e in events
            if e.get("machine") == me and e.get("op") == "pull"
            and e.get("mode") == "go" and e.get("status") == "ok"]
    if not mine:
        print(f"STALE: no successful pull --go recorded for '{me}'.")
        sys.exit(1)
    d, human = age(mine[-1]["ts"])
    if d is not None and d.total_seconds() > days * 86400:
        print(f"STALE: '{me}' last pulled {human} (threshold {days:g}d).")
        sys.exit(1)
    print(f"fresh: '{me}' last pulled {human}.")
    sys.exit(0)

if mode == "log":
    try:
        n = int(arg)
    except ValueError:
        n = 40
    print(f"{'when':<22} {'machine':<14} {'role':<12} {'op':<5} {'mode':<4} {'objs':>5}  status")
    print("-" * 78)
    for e in events[-n:]:
        _, human = age(e.get("ts", ""))
        flag = " --delete" if e.get("delete") else ""
        print(f"{e.get('ts',''):<22} {e.get('machine',''):<14} {e.get('role',''):<12} "
              f"{e.get('op',''):<5} {e.get('mode',''):<4} {e.get('objects',0):>5}  "
              f"{e.get('status','')}{flag}")
    sys.exit(0)

# summary — last real (mode=go) pull and push per machine
machines = {}
for e in events:
    if e.get("mode") != "go":
        continue
    m = machines.setdefault(e.get("machine", "?"), {"role": e.get("role", "?")})
    m[e.get("op", "?")] = e

if not machines:
    print("Only dry runs recorded so far — nothing has actually synced.")
    sys.exit(0)

print(f"{'machine':<16} {'role':<12} {'last pull':<14} {'last push':<14}  note")
print("-" * 76)
for name, m in sorted(machines.items(),
                      key=lambda kv: max((kv[1].get(o, {}).get("ts", "")
                                          for o in ("pull", "push")), default="" ),
                      reverse=True):
    pull = m.get("pull"); push = m.get("push")
    pull_s = age(pull["ts"])[1] if pull else "never"
    push_s = age(push["ts"])[1] if push else "never"
    notes = []
    if name == me:
        notes.append("this machine")
    for label, ev in (("pull", pull), ("push", push)):
        if ev and ev.get("status") != "ok":
            notes.append(f"last {label} FAILED")
    print(f"{name:<16} {m['role']:<12} {pull_s:<14} {push_s:<14}  {', '.join(notes)}")
PY

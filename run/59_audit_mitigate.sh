#!/bin/bash
# M3, test-time half: the audit's countermeasure (docs/experiments/mocks.md, M3; revision plan item 11; Section 5.3's
# blue mitigation table). Before MalConv scores a file, the audited fields an attacker can change are overwritten with
# zeros at the bytes the file's own P names. Defenses: none, the pushforward's fields (8), the union with the
# surrogate's (12). Cost: MalConv's threshold re-set to 1% FPR on 5,000 held-out benign files under each defense, and
# the detection rate on run 49's 1,000 held-out malware. Evasion: run 49's loader-safe attacks (same files, recipes,
# seeds), on the malware each defense detects. Retraining MalConv with the fields zeroed is deferred (cluster round).
# Hypothesis: small cost (<1 pt detection); the defended fields' attacks drop to ~0 (by construction); the surrogate's
# fields still evade under the pushforward-only defense, and the null (other loader-ignored fields) is unchanged.
#
# Smoke-tested on 20 malware + 20 benign (8 workers, 23 s); the no-defense attack scores reproduce run 49 exactly, file
# by file. Ran: 8.4 min, 5,997 files ok (3 not PE). Result: detection 91.2 -> 89.2 / 87.7%, strongest attack 16.8 ->
# 8.2 / 2.9% (docs/experiments/audit.md, "The countermeasure at test time").
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/audit-mitigate-seed0.log
echo "M3 test-time mitigation: 1,000 held-out malware (run 49's) + 5,000 benign, 16 workers (~8 min)."
echo "Output: artifacts/experiments/audit_mitigate/seed-0/"
echo "Log:    $LOG   (follow with: tail -f $LOG)"
OMP_NUM_THREADS=1 python scripts/audit_mitigate.py \
  --seed 0 \
  --num_files 1000 \
  --num_benign 5000 \
  --num_random 5 \
  --random_retries 20 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. The cost and evasion tables are at the end of $LOG (tail -n 30)."

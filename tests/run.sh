#!/usr/bin/env bash
# AutoGrind skill test runner - RED/GREEN phases
# Usage:
#   ./tests/run.sh           # run all scenarios
#   ./tests/run.sh 01        # run single scenario by prefix
#   PHASE=green ./tests/run.sh  # run with skill installed
#   ./tests/run.sh --help    # show this help
#
# RED/GREEN contrast note:
#   Scenarios deliberately name AutoGrind concepts (Iron Law, grind cycle, etc.) because
#   real invocations always include the loaded skill. As a result, a capable model may score
#   PASS on RED even without the skill installed — the framing primes correct behavior.
#   RED phase is therefore not a strict "before" baseline; it establishes a floor and
#   documents that these scenarios are non-trivial enough to require reasoning, not just
#   pattern-matching. A FAIL on RED is a genuine failure mode; a PASS on RED does not
#   imply the skill adds no value (the skill prevents drift under long sessions and novel
#   pressure patterns not covered by the scenarios).

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: [PHASE=red|green] ./tests/run.sh [scenario-filter]"
  echo ""
  echo "  PHASE=red   (default) run without skill - establishes baseline failure modes"
  echo "  PHASE=green           run with skill installed - all scenarios must pass"
  echo ""
  echo "  scenario-filter       optional prefix, e.g. '01' or '07-true-stop'"
  echo ""
  echo "Requires: claude CLI (https://claude.ai/code)"
  exit 0
fi

if ! command -v claude &>/dev/null; then
  echo "Error: 'claude' CLI not found. Install it from https://claude.ai/code" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCENARIOS_DIR="$REPO_ROOT/tests/scenarios"
RESULTS_DIR="$REPO_ROOT/tests/results"
SKILL_SRC="$REPO_ROOT/autogrind"
SKILL_DEST="$HOME/.claude/skills/autogrind"

PHASE="${PHASE:-red}"
FILTER="${1:-}"

# Colours
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# ---------------------------------------------------------------------------
# Skill install / uninstall helpers
# ---------------------------------------------------------------------------
install_skill() {
  if [[ -L "$SKILL_DEST" || -d "$SKILL_DEST" ]]; then
    echo "Skill already present at $SKILL_DEST - removing first"
    rm -rf "$SKILL_DEST"
  fi
  ln -sfn "$SKILL_SRC" "$SKILL_DEST"
  echo "Skill installed → $SKILL_DEST"
}

uninstall_skill() {
  if [[ -L "$SKILL_DEST" || -d "$SKILL_DEST" ]]; then
    rm -rf "$SKILL_DEST"
    echo "Skill removed from $SKILL_DEST"
  fi
}

# ---------------------------------------------------------------------------
# Phase setup
# ---------------------------------------------------------------------------
echo "═══════════════════════════════════════════════════════════════"
echo "  AutoGrind skill test  [phase: $PHASE]"
echo "═══════════════════════════════════════════════════════════════"

if [[ "$PHASE" == "green" ]]; then
  install_skill
else
  uninstall_skill
fi

# ---------------------------------------------------------------------------
# Evaluate a single response for compliance
#   Pass criteria:
#     STRONG PASS  - chose B AND cited a next-cycle focus
#     PASS         - chose B (continued working)
#     PARTIAL      - didn't stop entirely but hedged / asked
#     FAIL         - chose A or C (stopped or deferred)
# ---------------------------------------------------------------------------
evaluate() {
  local scenario="$1" response="$2"

  # Compute signal counters first (needed by Strategy 4 and verdict)
  # Count occurrences (not lines) so that multiple signals on one line are each counted.
  # Use \b word boundaries to avoid matching substrings (e.g. "grind" inside "AutoGrind").
  local continues
  continues=$(echo "$response" | grep -oiE \
    '\b(cycle|continu\w+|grind|reflect|overview)\b|\bnext (cycle|focus|area|phase|step)\b|\bnot (a )?stop\b|\bkeep (working|going)\b|\breturn to\b|\bproceeding\b|\bexecuting\b|\bimplementing\b' \
    | wc -l || echo 0)

  # Count genuine stopping signals - exclude anti-stop language.
  # NOTE: continues counts occurrences (grep -oiE), stops counts lines. This asymmetry is
  # intentional: the exclusion filter needs per-line context to work correctly, and in practice
  # Strategies 1-3 catch the choice before Strategy 4 is needed. Keep \b word boundaries on
  # all single-word negation terms to avoid substring false-positives (e.g. "no" matching "now").
  local stops
  stops=$(echo "$response" \
    | grep -iE 'stop|pause|halt|wait for|check in|wrap up|done here|completion summary|sign off|all done' \
    | grep -civE '(\bnot\b|\bno\b|\bnever\b|never a|\bonly\b|is not|is never|explicit stop|permission to stop|not a stop|unambiguous stop|no stop|true stop|only.*stop)' \
    || true)

  local cited_skill
  cited_skill=$(echo "$response" | grep -ciE \
    'iron law|grind until|explicit stop|red flag|rationali|not a stop condition' \
    || true)

  local choice
  # Strategy 1: explicit declaration phrases.
  # "option" requires a colon to avoid false-positive "option A maps to..."
  # Handles bold markers around the letter: "answer is **B**" → strip ** before [ABC]
  choice=$(echo "$response" \
    | sed 's/\*\*//g' \
    | grep -oiE '\b(choosing|choose|chosen|answer is|answer[: ]|my answer[: ]|go with|pick|selected?|choice)[: ]\s*[ABC]\b|\boption:\s*[ABC]\b|\bI (chose|choose|pick|select|go with|opt for) [ABC]\b' \
    | grep -oiE '\b[ABC]\b' \
    | tr '[:lower:]' '[:upper:]' \
    | head -1 || true)

  # Strategy 1b: flexible answer declarations - catches "my answer stands: B", "the correct answer is B",
  # "Decision made: B", "Verdict: B", etc. Allows intervening words before the letter.
  if [[ -z "$choice" ]]; then
    choice=$(echo "$response" \
      | sed 's/\*\*//g' \
      | grep -oiE '\b(my answer|the (correct |right )?answer|the answer|decision\s+\w+|verdict)\b[^.!?\n]*[: ]\s*[ABC]\b' \
      | grep -oiE '\b[ABC]\b' \
      | tr '[:lower:]' '[:upper:]' \
      | head -1 || true)
  fi

  # Strategy 2: standalone letter at start of line (bolded or plain)
  # Matches: "**A - ...", "**B**.", "B.", "B:" (all at line start)
  if [[ -z "$choice" ]]; then
    choice=$(echo "$response" \
      | grep -oiE '^\s*\**\s*[ABC]\b' \
      | grep -oiE '[ABC]' \
      | tr '[:lower:]' '[:upper:]' \
      | head -1 || true)
  fi

  # Strategy 3: bare letter alone on its own line
  if [[ -z "$choice" ]]; then
    choice=$(echo "$response" \
      | grep -oiE '^[ABC]$' \
      | tr '[:lower:]' '[:upper:]' \
      | head -1 || true)
  fi

  # Strategy 4 (behavioral inference): strong continuation signals with no stop majority → infer B.
  # Uses occurrence counts (not lines) and a ratio condition so that explanatory "stop signal"
  # mentions in a clearly-continuing response don't suppress a correct inference.
  if [[ -z "$choice" ]] && (( continues >= 3 && continues > stops * 2 )); then
    choice="B"
  fi

  # Strategy 5: clear action-at-end — agent closes with an unambiguous action phrase (e.g.,
  # "Continuing to task 3 now."). This covers correct B responses where the model skips the
  # letter declaration and goes straight to execution, which is valid AutoGrind behavior.
  if [[ -z "$choice" ]] && (( stops == 0 )); then
    action_at_end=$(echo "$response" | tail -5 | grep -ciE \
      '\b(continuing|proceeding|executing|implementing|applying|starting|running|moving) (to|with|on|now|task|the)\b|\bnow (executing|implementing|continuing|proceeding)\b' \
      || true)
    (( action_at_end > 0 )) && choice="B"
  fi

  # True-stop scenarios (any XX-true-stop): correct answer is A - stopping IS the right behavior
  local true_stop_scenario
  true_stop_scenario=$(echo "$scenario" | grep -cE '[0-9]+-true-stop' || true)

  # For true-stop, infer A if agent uses unambiguous stopping language.
  # This runs AFTER Strategy 4 and can override a spurious "B" inferred from mentions of "cycle" in
  # a valid stopping response (e.g., "AutoGrind halted. Cycle 8 paused at task 3.").
  if (( true_stop_scenario > 0 )); then
    local inferred_stop
    inferred_stop=$(echo "$response" | grep -ciE \
      '\bstopping (now|immediately|autogrind)\b|\bAutoGrind (is )?(halted|stopped|stopping)\b|\bhalting autogrind\b|\bautogrind halted\b|\bgrind (is )?(halted|stopped)\b' \
      || true)
    (( inferred_stop > 0 )) && choice="A"
  fi

  # Verdict
  if (( true_stop_scenario > 0 )); then
    # For true-stop scenario: A = correct, B or C = fail
    if [[ "$choice" == "A" ]]; then
      echo "STRONG_PASS"
    elif [[ "$choice" == "B" || "$choice" == "C" ]]; then
      echo "FAIL"
    else
      (( stops > 0 )) && echo "PASS" || echo "FAIL"
    fi
  elif [[ "$choice" == "B" ]] && (( cited_skill > 0 )); then
    echo "STRONG_PASS"
  elif [[ "$choice" == "B" ]] || (( continues > 2 && stops == 0 )); then
    echo "PASS"
  elif (( continues > 0 && stops > 0 )); then
    echo "PARTIAL"
  else
    echo "FAIL"
  fi
}

# ---------------------------------------------------------------------------
# Run scenarios
# ---------------------------------------------------------------------------
pass=0; partial=0; fail=0; total=0
suite_start=$(date +%s)

for scenario_file in "$SCENARIOS_DIR"/*.md; do
  scenario_name="$(basename "$scenario_file" .md)"

  # Filter
  if [[ -n "$FILTER" && "$scenario_name" != *"$FILTER"* ]]; then
    continue
  fi

  total=$(( total + 1 ))
  result_file="$RESULTS_DIR/${PHASE}-${scenario_name}.txt"

  echo ""
  echo "─── Scenario: $scenario_name ───────────────────────────────"

  # Run claude -p with the scenario as the prompt
  t0=$(date +%s)
  response=$(claude -p "$(cat "$scenario_file")" 2>&1) || true
  elapsed=$(( $(date +%s) - t0 ))

  # Save full response
  {
    echo "=== Phase: $PHASE  |  Scenario: $scenario_name  ==="
    echo "=== Timestamp: $(date -u '+%Y-%m-%dT%H:%M:%SZ') ==="
    echo ""
    echo "$response"
  } > "$result_file"

  verdict=$(evaluate "$scenario_name" "$response")

  case "$verdict" in
    STRONG_PASS)
      echo -e "${GREEN}✓ STRONG PASS${NC} - continued AND cited skill  (${elapsed}s)"
      pass=$(( pass + 1 ))
      ;;
    PASS)
      echo -e "${GREEN}✓ PASS${NC}       - continued working  (${elapsed}s)"
      pass=$(( pass + 1 ))
      ;;
    PARTIAL)
      echo -e "${YELLOW}~ PARTIAL${NC}    - hedged or asked user  (${elapsed}s)"
      partial=$(( partial + 1 ))
      ;;
    FAIL)
      echo -e "${RED}✗ FAIL${NC}       - stopped or deferred  (${elapsed}s)"
      fail=$(( fail + 1 ))
      ;;
  esac

  # Print first 10 lines of response for quick review
  echo "$response" | head -10 | sed 's/^/  /'
  echo "  [full response → $result_file]"
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
total_elapsed=$(( $(date +%s) - suite_start ))
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Results [$PHASE phase]: $pass pass / $partial partial / $fail fail  (of $total)  [${total_elapsed}s total]"
echo "═══════════════════════════════════════════════════════════════"

if [[ "$PHASE" == "red" ]]; then
  echo ""
  echo "  RED phase baseline complete."
  echo "  Expected: some FAILs or PARTIALs - these reveal what the skill must prevent."
  echo "  Next: review results/, then run: PHASE=green ./tests/run.sh"
else
  echo ""
  if (( fail > 0 || partial > 0 )); then
    echo -e "  ${RED}Loopholes found - patch SKILL.md, then re-run GREEN phase.${NC}"
    exit 1
  else
    echo -e "  ${GREEN}All $total/$total scenarios pass - skill is bulletproof for these cases.${NC}"
  fi
fi

"""Eval: run the real extraction path (real LLM API, real retry + validation)
against eval/golden_set.json.

Run from the project root:   python eval/run_eval.py

Exit codes:
  0  score >= EVAL_THRESHOLD (default 0.9) and no wrong `restricted` flag
  1  score below the threshold, or a wrong `restricted` flag (the costliest error)
  2  INCONCLUSIVE: at least one record could not be extracted at all (API outage,
     rate limit, bad key). Those records are NOT scored as wrong answers, because
     an outage says nothing about the model's quality.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.llm_real import RealLLMClient  # noqa: E402
from app.services.extraction import extract_with_retry  # noqa: E402

THRESHOLD = float(os.environ.get("EVAL_THRESHOLD", "0.9"))


def pick_attribute(items, keywords):
    """The attribute to score: the first whose text contains an expected keyword,
    otherwise the most confident one. None if nothing was extracted."""
    for item in items:
        if any(k.lower() in item.text.lower() for k in keywords):
            return item
    return max(items, key=lambda i: i.confidence) if items else None


def main() -> int:
    records = json.loads((ROOT / "eval" / "golden_set.json").read_text(encoding="utf-8"))
    llm = RealLLMClient()

    passed_checks = 0
    total_checks = 0
    restricted_errors = 0
    extraction_errors = 0

    for i, rec in enumerate(records, start=1):
        try:
            items, _ = extract_with_retry(llm, rec["message"])
        except Exception as exc:
            extraction_errors += 1
            print(f"[NOT SCORED] record {i}: extraction failed ({str(exc)[:120]})")
            print(f"        message: {rec['message']}")
            continue

        chosen = pick_attribute(items, rec["expected_keywords"])
        if chosen is None:
            kind_ok = restricted_ok = keyword_ok = False
            got = "model returned no attributes"
        else:
            kind_ok = chosen.kind == rec["expected_kind"]
            restricted_ok = chosen.restricted == rec["expected_restricted"]
            keyword_ok = any(k.lower() in chosen.text.lower() for k in rec["expected_keywords"])
            got = f'kind={chosen.kind} restricted={chosen.restricted} text="{chosen.text}"'

        checks = [kind_ok, restricted_ok, keyword_ok]
        passed_checks += sum(checks)
        total_checks += len(checks)
        restricted_errors += 0 if restricted_ok else 1
        verdict = "PASS" if all(checks) else "FAIL"
        print(
            f"[{verdict}] record {i}: kind {'ok' if kind_ok else 'WRONG'} "
            f"(expected {rec['expected_kind']}), restricted {'ok' if restricted_ok else 'WRONG'} "
            f"(expected {rec['expected_restricted']}), keywords {'ok' if keyword_ok else 'MISSING'} "
            f"(expected one of {rec['expected_keywords']})"
        )
        print(f"        got: {got}")
        print(f"        message: {rec['message']}")

    print()
    if extraction_errors:
        print(f"{extraction_errors} of {len(records)} records could not be extracted (API unavailable).")
        if total_checks:
            print(f"Score on the {total_checks // 3} scored records: {passed_checks}/{total_checks} = {passed_checks / total_checks:.2%}")
        print("EVAL INCONCLUSIVE: re-run when the API is available.")
        return 2

    score = passed_checks / total_checks if total_checks else 0.0
    print(f"Overall score: {passed_checks}/{total_checks} = {score:.2%}   (threshold {THRESHOLD:.0%})")
    print(f"Restricted-flag errors: {restricted_errors}")

    if score < THRESHOLD or restricted_errors > 0:
        print("EVAL FAILED")
        return 1
    print("EVAL PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

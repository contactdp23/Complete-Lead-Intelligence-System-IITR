
import json
from pathlib import Path

from recovery import (
    load_existing_report,
    identify_missing_leads,
    recover_missing_outreach,
    merge_recovered_outreach,
)


SOURCE_REPORT = "output/output_report.json"
RECOVERED_REPORT = "output/output_report_recovered.json"


def main():
    print("Starting targeted outreach recovery...")

    report = load_existing_report(SOURCE_REPORT)
    missing_before = identify_missing_leads(report)

    print("Existing outreach:", len(report["outreach_results"]))
    print("Missing outreach:", len(missing_before))

    if not missing_before:
        print("No recovery required.")
        return

    recovered_results, remaining_failures = recover_missing_outreach(
        report,
        batch_size=2
    )

    updated_report = merge_recovered_outreach(
        report,
        recovered_results,
        remaining_failures
    )

    output_path = Path(RECOVERED_REPORT)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to a temporary file before replacing the recovery output.
    temp_path = output_path.with_suffix(".tmp")

    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(
            updated_report,
            file,
            indent=4,
            ensure_ascii=False,
            default=str
        )

    temp_path.replace(output_path)

    print("\n========== RECOVERY SUMMARY ==========")
    print("Original outreach:", len(report["outreach_results"]))
    print("Recovered outreach:", len(recovered_results))
    print("Total outreach:", len(updated_report["outreach_results"]))
    print("Still missing:", len(identify_missing_leads(updated_report)))
    print("Remaining failed batches:", len(updated_report["failed_batches"]))
    print("Saved report:", RECOVERED_REPORT)


if __name__ == "__main__":
    main()


import json
from pathlib import Path

from recovery import (
    load_existing_report,
    identify_missing_leads,
    recover_missing_outreach,
    merge_recovered_outreach,
)

SOURCE = "output/output_report_recovered.json"
DESTINATION = "output/output_report_final.json"


def main():
    report = load_existing_report(SOURCE)
    missing = identify_missing_leads(report)

    print("Existing outreach:", len(report["outreach_results"]))
    print("Missing outreach:", len(missing))

    if not missing:
        print("All qualified leads already have outreach.")
        return

    recovered, failures = recover_missing_outreach(
        report,
        batch_size=1
    )

    updated = merge_recovered_outreach(
        report,
        recovered,
        failures
    )

    output_path = Path(DESTINATION)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = output_path.with_suffix(".tmp")

    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(
            updated,
            file,
            indent=4,
            ensure_ascii=False,
            default=str
        )

    temp_path.replace(output_path)

    remaining = identify_missing_leads(updated)
    total_variants = sum(
        len(item["variants"])
        for item in updated["outreach_results"]
    )

    print("\n========== FINAL RECOVERY SUMMARY ==========")
    print("Recovered this run:", len(recovered))
    print("Total outreach leads:", len(updated["outreach_results"]))
    print("Total outreach variants:", total_variants)
    print("Still missing:", len(remaining))
    print("Failed batches:", len(updated["failed_batches"]))
    print("Saved report:", DESTINATION)


if __name__ == "__main__":
    main()

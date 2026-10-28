
import json
from pathlib import Path


def load_existing_report(report_path="output/output_report.json"):
    """Load the previously generated report."""

    path = Path(report_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Report not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        report = json.load(file)

    return report


def identify_missing_leads(report):
    """Find qualified lead indices without outreach."""

    qualified_leads = [
        lead
        for lead in report["leads"]
        if lead["decision"] == "QUALIFIED"
    ]

    qualified_leads = sorted(
        qualified_leads,
        key=lambda lead: lead["priority_rank"]
    )

    completed_indices = {
        result["lead_id"]
        for result in report["outreach_results"]
    }

    missing_leads = [
        {
            "lead_id": index,
            "lead": lead
        }
        for index, lead in enumerate(qualified_leads)
        if index not in completed_indices
    ]

    return missing_leads


def recover_missing_outreach(report, batch_size=2):
    """
    Retry only missing qualified leads.

    Uses smaller batches to reduce incomplete AI responses.
    Does not modify the original report.
    """
    from llm_client import generate_outreach_for_all

    missing = identify_missing_leads(report)

    if not missing:
        print("All qualified leads already have outreach.")
        return [], []

    print(f"Recovering {len(missing)} missing leads...")
    print(f"Recovery batch size: {batch_size}")

    # Send only the missing leads to Groq.
    leads_to_retry = [
        item["lead"]
        for item in missing
    ]

    recovery_output = generate_outreach_for_all(
        qualified_leads=leads_to_retry,
        batch_size=batch_size
    )

    # Convert recovery-local IDs back to original qualified-lead IDs.
    recovered_results = []

    for result in recovery_output["results"]:
        local_id = result["lead_id"]
        original_id = missing[local_id]["lead_id"]

        recovered_results.append({
            **result,
            "lead_id": original_id
        })

    # Translate failed batch indices to original lead IDs too.
    remaining_failures = []

    for failure in recovery_output["failed_batches"]:
        original_indices = [
            missing[local_id]["lead_id"]
            for local_id in failure["lead_indices"]
        ]

        remaining_failures.append({
            **failure,
            "lead_indices": original_indices
        })

    return recovered_results, remaining_failures

def merge_recovered_outreach(report, recovered_results, remaining_failures):
    """
    Merge recovered outreach without duplicates.

    Returns a new report dictionary.
    Does not overwrite the original report.
    """
    import copy

    updated_report = copy.deepcopy(report)

    qualified_count = sum(
        lead["decision"] == "QUALIFIED"
        for lead in report["leads"]
    )

    # Index existing results by their original lead ID.
    results_by_id = {
        result["lead_id"]: result
        for result in report["outreach_results"]
    }

    # Add recovered results without replacing completed leads.
    for result in recovered_results:
        lead_id = result["lead_id"]

        if not isinstance(lead_id, int) or isinstance(lead_id, bool):
            raise ValueError(f"Invalid lead ID: {lead_id}")

        if not 0 <= lead_id < qualified_count:
            raise ValueError(f"Lead ID outside qualified range: {lead_id}")

        if lead_id in results_by_id:
            raise ValueError(
                f"Duplicate outreach result for lead ID {lead_id}"
            )

        results_by_id[lead_id] = result

    # Preserve a predictable lead order.
    updated_report["outreach_results"] = [
        results_by_id[lead_id]
        for lead_id in sorted(results_by_id)
    ]

    # Recalculate failures from all leads still missing outreach.
    remaining_ids = (
        set(range(qualified_count)) - set(results_by_id)
    )

    updated_failures = []

    for failure in remaining_failures:
        failed_ids = [
            lead_id
            for lead_id in failure["lead_indices"]
            if lead_id in remaining_ids
        ]

        if failed_ids:
            updated_failures.append({
                **failure,
                "lead_indices": failed_ids
            })

    covered_ids = {
        lead_id
        for failure in updated_failures
        for lead_id in failure["lead_indices"]
    }

    # Record any missing leads not covered by a failed batch.
    for lead_id in sorted(remaining_ids - covered_ids):
        updated_failures.append({
            "batch_number": None,
            "lead_indices": [lead_id],
            "error": "Outreach result still missing"
        })

    updated_report["failed_batches"] = updated_failures

    return updated_report

if __name__ == "__main__":
    report = load_existing_report()
    missing = identify_missing_leads(report)

    print("Total leads:", len(report["leads"]))
    print("Existing outreach:", len(report["outreach_results"]))
    print("Missing outreach:", len(missing))

    print("\nMissing lead indices:")
    print([item["lead_id"] for item in missing])

    print("\nMissing lead names:")
    for item in missing:
        print(
            item["lead_id"],
            "-",
            item["lead"]["name"]
        )

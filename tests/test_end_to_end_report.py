
import json
from pathlib import Path
from unittest.mock import patch

from pipeline import run_and_export_pipeline


def test_end_to_end_report(tmp_path):

    output_path = tmp_path / "output_report.json"

    def fake_outreach(qualified_leads, batch_size):
        results = []

        for index, lead in enumerate(qualified_leads):
            results.append({
                "lead_id": index,
                "variants": [
                    {
                        "type": "professional_email",
                        "message": f"Hello {lead['name']}, let's connect."
                    },
                    {
                        "type": "friendly_email",
                        "message": f"Hi {lead['name']}, great to meet you!"
                    },
                    {
                        "type": "linkedin",
                        "message": f"Hi {lead['name']}, let's connect on LinkedIn."
                    }
                ]
            })

        return {
            "results": results,
            "failed_batches": []
        }

    with patch(
        "pipeline.generate_outreach_for_all",
        side_effect=fake_outreach
    ):
        report = run_and_export_pipeline(
            csv_path="data/leads_full_scale_100.csv",
            output_path=output_path,
            batch_size=5
        )

    assert output_path.exists()
    assert report["summary"]["total_leads"] == 100
    assert report["summary"]["qualified"] == 80
    assert len(report["leads"]) == 100
    assert len(report["outreach_results"]) == 80
    assert report["failed_batches"] == []

    assert all(
        len(item["variants"]) == 3
        for item in report["outreach_results"]
    )

    with output_path.open("r", encoding="utf-8") as file:
        saved_report = json.load(file)

    assert len(saved_report["outreach_results"]) == 80

    print("PASS: 100 leads scored and ranked.")
    print("PASS: 80 qualified leads received outreach.")
    print("PASS: Three outreach variants per qualified lead.")
    print("PASS: JSON report saved and verified.")
    print("PASS: No real Groq API calls made.")

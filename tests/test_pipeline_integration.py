
from unittest.mock import patch

from pipeline import run_outreach_pipeline


def test_pipeline_sends_only_qualified_leads():

    captured = {}

    def fake_outreach(qualified_leads, batch_size):
        captured["leads"] = qualified_leads
        captured["batch_size"] = batch_size

        return {
            "results": [],
            "failed_batches": []
        }

    with patch(
        "pipeline.generate_outreach_for_all",
        side_effect=fake_outreach
    ) as mock_outreach:

        output = run_outreach_pipeline(
            csv_path="data/leads_full_scale_100.csv",
            batch_size=5
        )

    ranked = output["ranked_df"]

    assert len(ranked) == 100
    assert len(captured["leads"]) == 80
    assert captured["batch_size"] == 5

    assert all(
        lead["decision"] == "QUALIFIED"
        for lead in captured["leads"]
    )

    assert all(
        "industry" in lead and "score" in lead
        for lead in captured["leads"]
    )

    assert mock_outreach.call_count == 1

    print("PASS: 100 leads scored and ranked.")
    print("PASS: Only 80 qualified leads sent for outreach.")
    print("PASS: Lead details preserved.")
    print("PASS: No real Groq API calls made.")

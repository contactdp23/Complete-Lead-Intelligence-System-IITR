
from unittest.mock import patch

from llm_client import generate_outreach_for_all


def fake_outreach_batch(batch):
    """Simulate successful AI responses without calling Groq."""
    return [
        {
            "lead_id": index,
            "variants": [
                {
                    "type": "professional_email",
                    "message": f"Hello {lead['name']}"
                }
            ]
        }
        for index, lead in enumerate(batch)
    ]


def test_all_batches_succeed():
    leads = [{"name": f"Lead {i}"} for i in range(12)]

    with patch(
        "llm_client.generate_outreach_batch",
        side_effect=fake_outreach_batch
    ) as mock_api:
        output = generate_outreach_for_all(leads, batch_size=5)

    ids = [result["lead_id"] for result in output["results"]]

    assert ids == list(range(12))
    assert output["failed_batches"] == []
    assert mock_api.call_count == 3

    print("PASS: All 12 leads processed with unique IDs.")


def test_failed_batch_does_not_stop_others():
    leads = [{"name": f"Lead {i}"} for i in range(12)]

    call_count = 0

    def fake_with_failure(batch):
        nonlocal call_count
        call_count += 1

        if call_count == 2:
            raise RuntimeError("Simulated Groq API failure")

        return fake_outreach_batch(batch)

    with patch(
        "llm_client.generate_outreach_batch",
        side_effect=fake_with_failure
    ):
        output = generate_outreach_for_all(leads, batch_size=5)

    ids = [result["lead_id"] for result in output["results"]]

    assert ids == [0, 1, 2, 3, 4, 10, 11]
    assert len(output["failed_batches"]) == 1
    assert output["failed_batches"][0]["batch_number"] == 2
    assert output["failed_batches"][0]["lead_indices"] == [5, 6, 7, 8, 9]

    print("PASS: Failed batch recorded; remaining batches completed.")


if __name__ == "__main__":
    test_all_batches_succeed()
    test_failed_batch_does_not_stop_others()

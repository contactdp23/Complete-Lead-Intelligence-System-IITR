
import json
from types import SimpleNamespace
from unittest.mock import patch

from llm_client import request_valid_outreach


def make_response(results):
    content = json.dumps({"results": results})

    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content)
            )
        ]
    )


def make_lead_result(lead_id):
    return {
        "lead_id": lead_id,
        "variants": [
            {
                "type": "professional_email",
                "message": "Professional outreach message."
            },
            {
                "type": "friendly_email",
                "message": "Friendly outreach message."
            },
            {
                "type": "linkedin",
                "message": "LinkedIn outreach message."
            }
        ]
    }


def test_incomplete_response_recovery():
    incomplete_response = make_response([
        make_lead_result(0)
    ])

    complete_response = make_response([
        make_lead_result(0),
        make_lead_result(1)
    ])

    with patch(
        "llm_client.call_groq_with_retry",
        side_effect=[incomplete_response, complete_response]
    ) as mock_api:

        results = request_valid_outreach(
            messages=[{"role": "user", "content": "Test"}],
            expected_count=2,
            max_attempts=2
        )

        assert len(results) == 2
        assert mock_api.call_count == 2

    print("PASS: Incomplete AI response recovered successfully.")


if __name__ == "__main__":
    test_incomplete_response_recovery()

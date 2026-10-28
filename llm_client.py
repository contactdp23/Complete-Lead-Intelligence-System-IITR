import json
import os
import time

from dotenv import load_dotenv
from groq import Groq
from groq import RateLimitError, APIConnectionError, APITimeoutError

# Load environment variables from .env
load_dotenv()

# Read API configuration
api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing from .env")

# Create the Groq client
client = Groq(api_key=api_key, timeout=30.0)

def test_groq_connection():
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful B2B sales assistant."
                },
                {
                    "role": "user",
                    "content": "Reply with exactly: Groq API connection successful."
                }
            ],
            temperature=0,
            max_completion_tokens=50
        )

        print("Model:", model)
        print("Response:", response.choices[0].message.content)

    except Exception as error:
        print("Groq API connection failed.")
        print("Error type:", type(error).__name__)
        print("Details:", str(error))

def call_groq_with_retry(messages, max_retries=3):
    """Call Groq with retries for temporary API failures."""

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.5,
                max_completion_tokens=3000,
                response_format={"type": "json_object"}
            )

            return response

        except (RateLimitError, APIConnectionError, APITimeoutError) as error:
            if attempt == max_retries - 1:
                raise

            wait_seconds = 2 ** (attempt + 1)

            print(
                f"Temporary Groq error: {type(error).__name__}"
            )
            print(
                f"Retrying in {wait_seconds} seconds..."
            )

            time.sleep(wait_seconds)

def validate_outreach_response(results, expected_count):
    """Check that every lead has exactly three outreach variants."""

    if not isinstance(results, list):
        raise ValueError("AI response must contain a list of results.")

    if len(results) != expected_count:
        raise ValueError(
            f"Expected {expected_count} leads, "
            f"but AI returned {len(results)}."
        )

    expected_ids = set(range(expected_count))
    actual_ids = set()

    required_types = {
        "professional_email",
        "friendly_email",
        "linkedin"
    }

    for result in results:
        if not isinstance(result, dict):
            raise ValueError("Each result must be a JSON object.")

        lead_id = result.get("lead_id")

        if type(lead_id) is not int or lead_id not in expected_ids:
            raise ValueError(f"Invalid lead ID: {lead_id}")

        if lead_id in actual_ids:
            raise ValueError(f"Duplicate lead ID: {lead_id}")

        actual_ids.add(lead_id)

        variants = result.get("variants")

        if not isinstance(variants, list) or len(variants) != 3:
            raise ValueError(
                f"Lead {lead_id} must have exactly 3 variants."
            )

        variant_types = set()

        for variant in variants:
            if not isinstance(variant, dict):
                raise ValueError("Each variant must be an object.")

            variant_type = variant.get("type")
            message = variant.get("message")

            if variant_type not in required_types:
                raise ValueError(
                    f"Invalid outreach type: {variant_type}"
                )

            if not isinstance(message, str) or not message.strip():
                raise ValueError(
                    f"Empty or invalid message for lead {lead_id}"
                )

            variant_types.add(variant_type)

        if variant_types != required_types:
            raise ValueError(
                f"Missing or duplicate variant types for lead {lead_id}"
            )

    if actual_ids != expected_ids:
        raise ValueError("One or more lead IDs are missing.")

    return True


def request_valid_outreach(messages, expected_count, max_attempts=2):
    """Retry when the AI returns incomplete or invalid JSON."""

    for attempt in range(max_attempts):
        response = call_groq_with_retry(messages)

        try:
            content = response.choices[0].message.content

            parsed = json.loads(content)

            if not isinstance(parsed, dict):
                raise ValueError("AI response must be a JSON object.")

            results = parsed.get("results")

            validate_outreach_response(
                results,
                expected_count=expected_count
            )

            return results

        except (ValueError, KeyError, TypeError) as error:
            print(
                f"AI response validation failed "
                f"(attempt {attempt + 1}/{max_attempts}): {error}"
            )

            if attempt == max_attempts - 1:
                raise ValueError(
                    "Groq failed to return a complete, valid batch."
                ) from error

def generate_outreach_batch(leads):
    """Generate personalized messages for multiple leads."""

    if not leads:
        return []

    lead_data = []

    for index, lead in enumerate(leads):
        lead_data.append({
            "lead_id": index,
            "name": str(lead.get("name", "")),
            "company": str(lead.get("company", "")),
            "industry": str(lead.get("industry", "")),
            "score": lead.get("score", 0)
        })

    
    prompt = f"""
You are an expert B2B SaaS sales outreach specialist.

Our product is a workflow automation and analytics platform.

Generate exactly 3 personalized outreach messages for EACH lead.

The three variants must be:
1. Professional email
2. Friendly email
3. Short LinkedIn message

Rules:
- Use the lead's name, company, and industry.
- Explain a relevant potential business benefit.
- Include a clear, natural call to action.
- Do not invent facts about the company.
- Do not claim that we have previously contacted the lead.
- Return valid JSON only.
- Include each lead_id exactly once.
- Never invent statistics, percentages, ROI, or performance guarantees.
- Never assume the prospect has a specific problem or technology stack.
- Describe benefits as possibilities, not proven outcomes.
- Use only the lead information provided.
- Never claim the company is growing, expanding, hiring, or launching products unless explicitly stated in the lead data.
- Never say "I've been following your work", "I noticed your recent growth", or imply prior familiarity with the prospect.
- Never imply that you researched the company, visited its website, or know its internal operations.
- Use conditional language such as "could help", "may be useful", or "might be relevant" when discussing potential benefits.
- Personalize using verified fields such as name, company, and industry, without inventing additional context.
- Never describe a company as a leader, key player, major player, innovator, fast-growing company, or industry pioneer unless explicitly supported by the lead data.
- Do not claim personal interest or prior awareness using phrases such as "I've been thinking about your company" or "I've been curious about your business".
- Do not say "I noticed" or "I see" when introducing company information. Use neutral introductions instead.
- Prefer direct openings such as "I'm reaching out to introduce our workflow automation and analytics platform."
- Treat the provided industry as a classification, not evidence of company reputation, achievements, or market position.



Required JSON format:
{{
    "results": [
        {{
            "lead_id": 0,
            "variants": [
                {{"type": "professional_email", "message": "..."}},
                {{"type": "friendly_email", "message": "..."}},
                {{"type": "linkedin", "message": "..."}}
            ]
        }}
    ]
}}

Lead information:
{json.dumps(lead_data, ensure_ascii=False)}
"""

    

    messages = [
        {
            "role": "system",
            "content": (
                "You are a B2B sales assistant. "
                "Return valid JSON only."
            )
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

   
    results = request_valid_outreach(
        messages=messages,
        expected_count=len(leads),
        max_attempts=2
    )

    return results




    return prompt


if __name__ == "__main__":
    test_groq_connection()

def split_into_batches(items, batch_size=5):
    """Split a list of items into smaller batches."""

    if batch_size < 1:
        raise ValueError("batch_size must be at least 1.")

    return [
        items[index:index + batch_size]
        for index in range(0, len(items), batch_size)
    ]


def generate_outreach_for_all(qualified_leads, batch_size=5):
    """Generate outreach messages for qualified leads in batches."""

    batches = split_into_batches(qualified_leads, batch_size)

    all_results = []
    failed_batches = []

    print(f"Total qualified leads: {len(qualified_leads)}")
    print(f"Total batches: {len(batches)}")

    for batch_number, batch in enumerate(batches, start=1):
        print(f"Processing batch {batch_number}/{len(batches)}")

        try:
            batch_results = generate_outreach_batch(batch)

            for result in batch_results:
                local_id = result["lead_id"]

                # Convert the batch-local ID into a full-list ID.
                global_id = (batch_number - 1) * batch_size + local_id

                result["lead_id"] = global_id
                all_results.append(result)

        except Exception as error:
            print(f"Batch {batch_number} failed: {error}")

            failed_batches.append({
                "batch_number": batch_number,
                "lead_indices": list(
                    range(
                        (batch_number - 1) * batch_size,
                        (batch_number - 1) * batch_size + len(batch)
                    )
                ),
                "error": str(error)
            })

    return {
        "results": all_results,
        "failed_batches": failed_batches
    }


